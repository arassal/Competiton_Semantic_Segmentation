import json
import time

import cv2
import numpy as np
import rclpy
import torch
from cv_bridge import CvBridge
from PIL import Image as PilImage
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image
from std_msgs.msg import String
from vision_msgs.msg import LabelInfo, VisionClass


DEFAULT_MODEL_ID = 'nvidia/segformer-b0-finetuned-cityscapes-512-1024'
DEFAULT_IMAGE_TOPIC = '/zed/zed_node/rgb/color/rect/image'


class SegFormerNode(Node):
    """Optional SegFormer semantic segmentation backend for comparison testing."""

    def __init__(self):
        super().__init__('segformer_node')

        self.declare_parameter('image_topic', DEFAULT_IMAGE_TOPIC)
        self.declare_parameter('model_id', DEFAULT_MODEL_ID)
        self.declare_parameter('device', 'cpu')
        self.declare_parameter('process_every_n', 1)
        self.declare_parameter('publish_input_image', True)
        self.declare_parameter('publish_timing', True)

        self.image_topic = self.get_parameter('image_topic').value
        self.model_id = self.get_parameter('model_id').value
        self.device_name = self.get_parameter('device').value
        self.process_every_n = max(1, int(self.get_parameter('process_every_n').value))
        self.publish_input_image = bool(self.get_parameter('publish_input_image').value)
        self.publish_timing = bool(self.get_parameter('publish_timing').value)

        self.bridge = CvBridge()
        self.frame_count = 0
        self.device = self._resolve_device(self.device_name)
        self._load_model()

        self.input_pub = self.create_publisher(
            Image, '/seg_ros/segformer/input_image', 10)
        self.overlay_pub = self.create_publisher(
            Image, '/seg_ros/segformer/overlay_image', 10)
        self.class_mask_pub = self.create_publisher(
            Image, '/seg_ros/segformer/class_mask', 10)
        self.road_mask_pub = self.create_publisher(
            Image, '/seg_ros/segformer/road_mask', 10)
        self.sidewalk_mask_pub = self.create_publisher(
            Image, '/seg_ros/segformer/sidewalk_mask', 10)
        self.metadata_pub = self.create_publisher(
            String, '/seg_ros/segformer/metadata', 10)
        self.timing_pub = self.create_publisher(
            String, '/seg_ros/segformer/timing', 10)

        label_qos = QoSProfile(depth=1)
        label_qos.reliability = ReliabilityPolicy.RELIABLE
        label_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        self.label_pub = self.create_publisher(
            LabelInfo, '/seg_ros/segformer/label_info', label_qos)

        self.sub = self.create_subscription(Image, self.image_topic, self._image_cb, 10)
        self._publish_label_info()
        self.get_logger().info(f'Loaded SegFormer model: {self.model_id}')
        self.get_logger().info(f'Subscribed to image topic: {self.image_topic}')

    def _resolve_device(self, value):
        if value.startswith('cuda') and not torch.cuda.is_available():
            self.get_logger().warning('CUDA requested but unavailable; falling back to CPU')
            return torch.device('cpu')
        return torch.device(value)

    def _load_model(self):
        try:
            from transformers import SegformerForSemanticSegmentation, SegformerImageProcessor
        except ImportError as exc:
            raise RuntimeError(
                'SegFormer support requires the optional transformers dependency. '
                'Install it in the runtime environment with: '
                '/home/alexander/github/av-perception/.venv/bin/python -m pip install transformers'
            ) from exc

        self.processor = SegformerImageProcessor.from_pretrained(self.model_id)
        self.model = SegformerForSemanticSegmentation.from_pretrained(self.model_id)
        self.model.to(self.device)
        self.model.eval()
        self.id2label = {
            int(k): v for k, v in self.model.config.id2label.items()
        }
        self.label2id = {
            label.lower(): idx for idx, label in self.id2label.items()
        }

    def _image_cb(self, msg):
        self.frame_count += 1
        if self.frame_count % self.process_every_n != 0:
            return

        start = time.perf_counter()
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as exc:
            self.get_logger().warning(f'Failed to convert input image: {exc}')
            return

        try:
            class_mask = self._infer(frame)
        except Exception as exc:
            self.get_logger().warning(f'SegFormer inference failed: {exc}')
            return

        road_mask = self._binary_mask(class_mask, 'road')
        sidewalk_mask = self._binary_mask(class_mask, 'sidewalk')
        overlay = self._make_overlay(frame, class_mask)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        self._publish_images(msg, frame, overlay, class_mask, road_mask, sidewalk_mask)
        self._publish_metadata(msg, class_mask, road_mask, sidewalk_mask, elapsed_ms)

    def _infer(self, frame_bgr):
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        pil_image = PilImage.fromarray(frame_rgb)
        inputs = self.processor(images=pil_image, return_tensors='pt')
        inputs = {key: value.to(self.device) for key, value in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            logits = torch.nn.functional.interpolate(
                logits,
                size=frame_bgr.shape[:2],
                mode='bilinear',
                align_corners=False,
            )
            class_mask = logits.argmax(dim=1)[0].cpu().numpy().astype(np.uint8)
        return class_mask

    def _binary_mask(self, class_mask, class_name):
        class_id = self.label2id.get(class_name)
        if class_id is None:
            return np.zeros(class_mask.shape, dtype=np.uint8)
        return (class_mask == class_id).astype(np.uint8) * 255

    def _make_overlay(self, frame, class_mask):
        overlay = frame.copy()
        colors = {
            'road': (70, 70, 70),
            'sidewalk': (120, 120, 120),
            'person': (0, 220, 255),
            'car': (255, 130, 0),
            'truck': (255, 80, 0),
            'bus': (255, 80, 80),
            'traffic light': (60, 220, 60),
            'traffic sign': (30, 180, 30),
        }
        color_mask = np.zeros_like(frame)
        for label, color in colors.items():
            class_id = self.label2id.get(label)
            if class_id is not None:
                color_mask[class_mask == class_id] = color
        active = np.any(color_mask != 0, axis=2)
        overlay[active] = cv2.addWeighted(frame, 0.55, color_mask, 0.45, 0)[active]
        return overlay

    def _publish_images(self, source_msg, frame, overlay, class_mask, road_mask, sidewalk_mask):
        if self.publish_input_image:
            input_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            input_msg.header = source_msg.header
            self.input_pub.publish(input_msg)

        overlay_msg = self.bridge.cv2_to_imgmsg(overlay, encoding='bgr8')
        overlay_msg.header = source_msg.header
        self.overlay_pub.publish(overlay_msg)

        class_msg = self.bridge.cv2_to_imgmsg(class_mask, encoding='mono8')
        class_msg.header = source_msg.header
        self.class_mask_pub.publish(class_msg)

        road_msg = self.bridge.cv2_to_imgmsg(road_mask, encoding='mono8')
        road_msg.header = source_msg.header
        self.road_mask_pub.publish(road_msg)

        sidewalk_msg = self.bridge.cv2_to_imgmsg(sidewalk_mask, encoding='mono8')
        sidewalk_msg.header = source_msg.header
        self.sidewalk_mask_pub.publish(sidewalk_msg)

    def _publish_metadata(self, source_msg, class_mask, road_mask, sidewalk_mask, elapsed_ms):
        counts = {}
        unique, pixels = np.unique(class_mask, return_counts=True)
        for class_id, count in zip(unique.tolist(), pixels.tolist()):
            label = self.id2label.get(int(class_id), str(class_id))
            counts[label] = int(count)

        payload = {
            'header': {
                'stamp': {
                    'sec': source_msg.header.stamp.sec,
                    'nanosec': source_msg.header.stamp.nanosec,
                },
                'frame_id': source_msg.header.frame_id,
            },
            'model_id': self.model_id,
            'road_pixels': int(np.count_nonzero(road_mask)),
            'sidewalk_pixels': int(np.count_nonzero(sidewalk_mask)),
            'class_pixel_counts': counts,
            'timing_ms': elapsed_ms,
        }
        metadata_msg = String()
        metadata_msg.data = json.dumps(payload)
        self.metadata_pub.publish(metadata_msg)

        if self.publish_timing:
            timing_msg = String()
            timing_msg.data = json.dumps({
                'model_id': self.model_id,
                'frame_id': source_msg.header.frame_id,
                'timing_ms': elapsed_ms,
                'process_every_n': self.process_every_n,
            })
            self.timing_pub.publish(timing_msg)

    def _publish_label_info(self):
        msg = LabelInfo()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera_color_optical_frame'
        msg.threshold = 0.0
        msg.class_map = [
            VisionClass(class_id=class_id, class_name=label)
            for class_id, label in sorted(self.id2label.items())
        ]
        self.label_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = SegFormerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
