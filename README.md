# Competiton Semantic Segmentation

ROS 2 Jazzy perception package for semantic road segmentation, lane-line masks, and traffic-cone/object detection.

The repository currently wraps pretrained perception models into a ROS 2-compatible workflow and includes proof images, evaluation scripts, launch files, and documentation needed to reproduce the static-image validation. The long-term goal is a competition-ready perception module that can run from a live robot camera and feed navigation/safety logic.

> Repository name intentionally follows the requested spelling: `Competiton_Semantic_Segmentation`.

## System Summary

| Capability | Current status |
|---|---|
| Drivable-road segmentation | Working from pretrained YOLOPv2 checkpoint |
| Lane-line segmentation | Working from pretrained YOLOPv2 checkpoint |
| Traffic-cone detection | Working from included Roboflow Logistics YOLOv8 checkpoint |
| People / road-sign / vehicle detections | Supported by the included object model |
| ROS 2 Jazzy package | Builds locally with `colcon` |
| Live RealSense camera input | Planned next implementation step |
| Nav2 semantic costmap integration | Planned; not claimed as complete |

## Technical Stack

| Area | Implementation |
|---|---|
| ROS package | `seg_ros_bridge`, Python `ament_python` |
| ROS distribution | ROS 2 Jazzy |
| Image bridge | `cv_bridge`, OpenCV BGR frames |
| Road/lane backend | YOLOPv2 TorchScript checkpoint loaded with PyTorch |
| Object backend | Ultralytics YOLOv8 checkpoint trained on Roboflow Logistics data |
| Road/lane outputs | `sensor_msgs/msg/Image` masks and overlay, `vision_msgs/msg/LabelInfo`, JSON detections |
| Object outputs | annotated `sensor_msgs/msg/Image`, JSON detections |
| Current runtime mode | deterministic static-image publishers for repeatable proof runs |
| Next runtime mode | live camera subscriber for RealSense `/camera/camera/color/image_raw` |

## Pipeline

One perception path: road image in, semantic road/lane masks and cone detections out.

![ROS 2 road segmentation and cone detection pipeline](docs/ros2_semantic_segmentation_pipeline.png)

## Proof Gallery

**Combined road + cone proof**

The combined contact sheet uses one road image with both road surface and traffic cones:

```text
input road image | semantic road/lane + cone overlay | drivable mask | lane mask
```

![Combined road segmentation and cone detection proof](proof/combined/semantic_segmentation_plus_cones_contact_sheet.jpg)

**Single combined overlay**

![Road segmentation and traffic cone overlay](proof/combined/semantic_segmentation_plus_cones_road.jpg)

**Original road/lane segmentation baseline**

![Original road-line segmentation proof](proof/contact_sheet.jpg)

**Traffic cone evaluation proof**

![Actual road cone detections](proof/traffic_cones/actual_road_cone_contact_sheet.jpg)

## Models And Datasets

This project uses pretrained upstream models. The ROS 2 integration, proof scripts, evaluation commands, and documentation are project-owned. The current repository does not claim that the road segmentation model or object detector were trained from scratch here.

| Model | Task | Dataset / training source | Stored in repo? |
|---|---|---|---|
| YOLOPv2 | object detection, drivable-area segmentation, lane-line segmentation | Upstream YOLOPv2 training, documented around BDD100K driving perception tasks | No, external checkpoint |
| Roboflow Logistics YOLOv8 | traffic cones, people, traffic lights, road signs, vehicles, logistics objects | Roboflow Logistics dataset: 99,238 images, 20 classes, reported 76% mAP | Yes, small checkpoint |

Detailed dataset, model provenance, training status, and future fine-tuning plan:

- [Dataset and Training Notes](docs/datasets_and_training.md)
- [Technical Architecture](docs/technical_architecture.md)
- [Model Weights](models/README.md)
- [Traffic Cone Detection Notes](docs/traffic_cones/README.md)

## Runtime Architecture

Current implementation contains two ROS nodes.

| Node | Backend | Input source | Main outputs |
|---|---|---|---|
| `seg_demo_node` | YOLOPv2 | image directory | drivable mask, lane mask, lane confidence, overlay, label map, detection JSON |
| `competition_objects_node` | Roboflow Logistics YOLOv8 | image directory | annotated image, object detection JSON |

Road/lane inference path:

```text
OpenCV image
  -> resize to 1280x720
  -> YOLOPv2 letterbox to 640
  -> RGB tensor normalization
  -> TorchScript forward pass
  -> drivable-area mask
  -> lane-line mask
  -> ROS image publications
```

Object detection path:

```text
OpenCV image
  -> Ultralytics YOLOv8 inference at imgsz=640
  -> confidence filtering
  -> class allow-list
  -> annotated image
  -> JSON detection publication
```

Detection bounding boxes use image-pixel `xyxy` format:

```text
[x_min, y_min, x_max, y_max]
```

For navigation, these 2D detections still need camera calibration and depth/lidar association before they can become physical obstacles.

## What Works Now

Road/lane semantic segmentation:

- publishes input image, overlay image, drivable-area mask, lane-line mask, lane confidence, detections, and label metadata
- uses the local YOLOPv2 checkpoint at `/home/alexander/Desktop/seg/data/weights/yolopv2.pt`
- proof images show non-empty drivable and lane masks on road scenes

Competition object detection:

- detects traffic cones using `models/roboflow_logistics_yolov8.pt`
- can also detect people, traffic lights, road signs, cars, trucks, and vans from the same checkpoint
- publishes annotated images and JSON detections
- includes traffic-cone evaluation results and proof images

Traffic cone reliability checks currently recorded:

```text
annotation evaluation:
  images: 48
  ground-truth cones: 167
  predicted cones: 168
  precision: 0.8274
  recall: 0.8323
  F1: 0.8299

road smoke test:
  non-cone road frames: 72
  cone false positives: 0
  road-cone scenes: 12
  detected cones: 59
```

## ROS 2 Topics

Road/lane segmentation topics:

| Topic | Type | Encoding / payload | Purpose |
|---|---|---|---|
| `/seg_ros/input_image` | `sensor_msgs/msg/Image` | `bgr8` | Source frame used for inference |
| `/seg_ros/overlay_image` | `sensor_msgs/msg/Image` | `bgr8` | Debug image with segmentation overlay |
| `/seg_ros/drivable_mask` | `sensor_msgs/msg/Image` | `mono8`, 0 or 255 | Drivable-area mask |
| `/seg_ros/lane_mask` | `sensor_msgs/msg/Image` | `mono8`, 0 or 255 | Lane-line mask |
| `/seg_ros/lane_confidence` | `sensor_msgs/msg/Image` | `mono8`, 0 or 255 | Current lane confidence proxy |
| `/seg_ros/label_info` | `vision_msgs/msg/LabelInfo` | transient-local class map | Semantic class labels |
| `/seg_ros/detections` | `std_msgs/msg/String` | JSON | YOLOPv2 detection boxes |

Competition object topics:

| Topic | Type | Encoding / payload | Purpose |
|---|---|---|---|
| `/seg_ros/competition_objects/input_image` | `sensor_msgs/msg/Image` | `bgr8` | Source frame used for object inference |
| `/seg_ros/competition_objects/annotated_image` | `sensor_msgs/msg/Image` | `bgr8` | Debug image with object boxes |
| `/seg_ros/competition_objects/detections` | `std_msgs/msg/String` | JSON | Filtered competition object detections |

Semantic label map:

| Class ID | Class name |
|---:|---|
| 0 | `background` |
| 1 | `drivable_area` |
| 2 | `lane_marking` |

Competition object allow-list:

```text
person
traffic cone
traffic light
road sign
car
truck
van
```

Example object detection JSON:

```json
{
  "image": "frame_name.jpg",
  "count": 1,
  "detections": [
    {
      "type": "traffic_cone",
      "class_name": "traffic cone",
      "confidence": 0.87,
      "xyxy": [248.0, 315.0, 302.0, 417.0]
    }
  ]
}
```

## Repository Layout

```text
docs/
  datasets_and_training.md
  ros2_semantic_segmentation_pipeline.png
  semantic_roadlines_pipeline.md
  technical_architecture.md
  traffic_cones/README.md
models/
  README.md
  roboflow_logistics_yolov8.pt
proof/
  combined/
  source_images/
  traffic_cones/
ros2_ws/src/seg_ros_bridge/
scripts/
```

## Build

```bash
cd /home/alexander/Desktop/Competiton_Semantic_Segmentation/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select seg_ros_bridge
```

Verified locally:

```text
ROS 2 Jazzy
rclpy
sensor_msgs
std_msgs
cv_bridge
vision_msgs
PyTorch / Ultralytics runtime
```

## Launch Parameters

Road/lane segmentation node:

| Parameter | Default | Meaning |
|---|---|---|
| `project_root` | `/home/alexander/Desktop/seg` | YOLOPv2 source/utilities path |
| `image_dir` | `${project_root}/data/demo` | static demo image folder |
| `weights_path` | `${project_root}/data/weights/yolopv2.pt` | YOLOPv2 checkpoint |
| `device` | `cpu` | PyTorch device |
| `img_size` | `640` | model letterbox size |
| `conf_thres` | `0.30` | detection confidence threshold |
| `iou_thres` | `0.45` | NMS IoU threshold |
| `publish_rate_hz` | `1.0` | output rate for static images |

Competition object node:

| Parameter | Default | Meaning |
|---|---|---|
| `image_dir` | `proof/traffic_cones/raw_road_inputs` | static object-demo image folder |
| `model_path` | `models/roboflow_logistics_yolov8.pt` | object detector checkpoint |
| `enabled_classes` | competition allow-list | classes allowed into output |
| `confidence` | `0.35` | object confidence threshold |
| `device` | `cpu` | Ultralytics device |
| `publish_rate_hz` | `1.0` | output rate for static images |

## Run

Run semantic road/lane segmentation demo:

```bash
source /opt/ros/jazzy/setup.bash
cd /home/alexander/Desktop/seg
/home/alexander/github/av-perception/.venv/bin/python \
  /home/alexander/Desktop/Competiton_Semantic_Segmentation/ros2_ws/src/seg_ros_bridge/seg_ros_bridge/seg_demo_node.py \
  --ros-args \
  -p project_root:=/home/alexander/Desktop/seg \
  -p image_dir:=/home/alexander/Desktop/seg/data/demo \
  -p weights_path:=/home/alexander/Desktop/seg/data/weights/yolopv2.pt \
  -p device:=cpu
```

Run competition object detector:

```bash
source /opt/ros/jazzy/setup.bash
cd /home/alexander/Desktop/Competiton_Semantic_Segmentation/ros2_ws
ros2 launch seg_ros_bridge competition_objects.launch.py
```

Verify:

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic list | grep '^/seg_ros/'
ros2 topic echo /seg_ros/competition_objects/detections --once
```

## Reproduce Proofs

Road/lane segmentation proof:

```bash
/home/alexander/github/av-perception/.venv/bin/python \
  scripts/export_roadline_proof.py \
  --project-root /home/alexander/Desktop/seg \
  --weights /home/alexander/Desktop/seg/data/weights/yolopv2.pt \
  --output-dir proof \
  --device cpu
```

Traffic-cone evaluation:

```bash
/home/alexander/github/av-perception/.venv/bin/python \
  scripts/evaluate_traffic_cones.py \
  --model models/roboflow_logistics_yolov8.pt \
  --dataset /home/alexander/Desktop/HERE_Object_Anomaly/cone_test/cone_dataset \
  --output-dir proof/traffic_cones \
  --device cpu \
  --conf 0.25 \
  --iou 0.50
```

Combined semantic road + cone proof:

```bash
/home/alexander/github/av-perception/.venv/bin/python \
  scripts/generate_combined_semantic_cone_proof.py
```

## Validation Method

Road/lane validation currently verifies:

- model loads and runs on static road frames
- drivable-area mask is non-empty
- lane-line mask is non-empty
- overlay image aligns visually with road/lane regions
- ROS 2 image topics publish with expected encodings
- label metadata publishes with transient-local QoS

Traffic-cone validation currently uses:

- local XML annotations
- `traffic cone` class filtering
- IoU matching at `0.50`
- precision, recall, and F1 reporting
- road-scene false-positive smoke testing

This is an integration validation, not a final safety certification.

## Proof Files

Combined proof:

```text
proof/combined/semantic_segmentation_plus_cones_contact_sheet.jpg
proof/combined/semantic_segmentation_plus_cones_road.jpg
proof/source_images/road_cars_cones_input.jpg
```

Traffic cone proof:

```text
proof/traffic_cones/actual_road_cone_contact_sheet.jpg
proof/traffic_cones/traffic_cone_eval_contact_sheet.jpg
proof/traffic_cones/traffic_cone_eval.json
proof/traffic_cones/actual_road_cone_test.json
```

Source image credit:

```text
Photo by Limi change on Unsplash
https://unsplash.com/photos/a-city-street-filled-with-traffic-and-construction-cones-5AFdk2U3htY
```

## Known Limits

- The road/lane model is still an upstream pretrained checkpoint, not a locally fine-tuned competition model.
- The object detector has good traffic-cone proof results, but it still needs validation on the actual robot camera.
- Static proof images are not a replacement for live RealSense testing, motion blur testing, nighttime testing, or Nav2 integration testing.
- Lane-line masks should be treated as navigation cues, not physical obstacles.
- Cones and people should be treated as safety cues, then fused with geometric obstacle sensing before driving decisions.

## Next Steps

1. Add a live RealSense subscriber so the same models run on `/camera/camera/color/image_raw`.
2. Record a local validation set from the robot camera with road, lane-line, cone, person, and anomaly examples.
3. Label a small project-owned dataset for lane/drivable masks and traffic cones.
4. Fine-tune or replace the pretrained models only after local validation shows the failure cases clearly.
5. Feed drivable-area masks into a Nav2 semantic costmap experiment while keeping geometric obstacle layers active.
