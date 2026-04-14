# Competiton Semantic Segmentation

ROS 2 perception proof for road/lane semantic segmentation and traffic cone detection.

The current pipeline combines:

- **YOLOPv2** for drivable-area and lane-line segmentation.
- **Roboflow Logistics YOLOv8** for traffic cones and other competition objects.
- **ROS 2 Jazzy** publishers for images, masks, overlays, and JSON detections.

> Repository name intentionally follows the requested spelling: `Competiton_Semantic_Segmentation`.

## Pipeline

One pipeline: road image in, semantic road/lane masks and cone detections out.

![ROS 2 road segmentation and cone detection pipeline](docs/ros2_semantic_segmentation_pipeline.png)

## Proof Gallery

**Combined road + cone proof**

Same format as the original segmentation proof:

```text
input road image | semantic road/lane + cone overlay | drivable mask | lane mask
```

![Combined road segmentation and cone detection proof](proof/combined/semantic_segmentation_plus_cones_contact_sheet.jpg)

**Single combined overlay**

![Road segmentation and traffic cone overlay](proof/combined/semantic_segmentation_plus_cones_road.jpg)

**Original segmentation baseline**

![Original road-line segmentation proof](proof/contact_sheet.jpg)

**Traffic cone evaluation proof**

![Actual road cone detections](proof/traffic_cones/actual_road_cone_contact_sheet.jpg)

## What Works

Semantic segmentation:

- publishes drivable-area mask
- publishes lane-line mask
- publishes overlay image
- publishes label metadata

Competition object detection:

- detects traffic cones
- can also detect people, traffic lights, road signs, cars, trucks, and vans from the included model
- publishes annotated image and JSON detections

Traffic cone reliability checks:

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

| Topic | Type |
|---|---|
| `/seg_ros/input_image` | `sensor_msgs/msg/Image` |
| `/seg_ros/overlay_image` | `sensor_msgs/msg/Image` |
| `/seg_ros/drivable_mask` | `sensor_msgs/msg/Image` |
| `/seg_ros/lane_mask` | `sensor_msgs/msg/Image` |
| `/seg_ros/lane_confidence` | `sensor_msgs/msg/Image` |
| `/seg_ros/label_info` | `vision_msgs/msg/LabelInfo` |
| `/seg_ros/detections` | `std_msgs/msg/String` |

Competition object topics:

| Topic | Type |
|---|---|
| `/seg_ros/competition_objects/input_image` | `sensor_msgs/msg/Image` |
| `/seg_ros/competition_objects/annotated_image` | `sensor_msgs/msg/Image` |
| `/seg_ros/competition_objects/detections` | `std_msgs/msg/String` |

## Models

Included:

```text
models/roboflow_logistics_yolov8.pt
```

This is the small traffic-cone-capable YOLOv8 checkpoint.

External, not committed:

```text
/home/alexander/Desktop/seg/data/weights/yolopv2.pt
```

The YOLOPv2 checkpoint is about 150 MB, so it stays external. See [models/README.md](models/README.md).

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

## Project Layout

```text
docs/
  ros2_semantic_segmentation_pipeline.png
  traffic_cones/README.md
models/
  roboflow_logistics_yolov8.pt
proof/
  combined/
  source_images/
  traffic_cones/
ros2_ws/src/seg_ros_bridge/
scripts/
```

## Next Steps

1. Replace image-folder demos with a live RealSense image subscriber.
2. Feed drivable-area masks into Nav2 semantic costmap work.
3. Treat cones and people as obstacle/safety cues.
4. Keep geometric obstacle layers active for safety.
