# Competiton Semantic Segmentation

ROS 2 road-line and drivable-area semantic segmentation pipeline for the AVROS competition stack.

This repository contains the first working implementation using a pretrained YOLOPv2 model. It publishes lane-line masks, drivable-area masks, overlay images, confidence masks, label metadata, and detections as ROS 2 topics.

## Current Status

Working locally as of 2026-04-13:

- Pretrained YOLOPv2 weights run successfully.
- ROS 2 Jazzy bridge publishes segmentation topics.
- Proof images were exported from demo frames.
- Large model weights are intentionally not committed to git.

Proof contact sheet:

![Road-line segmentation proof](proof/contact_sheet.jpg)

## Published ROS 2 Topics

| Topic | Type | Notes |
|---|---|---|
| `/seg_ros/input_image` | `sensor_msgs/msg/Image` | Source image |
| `/seg_ros/overlay_image` | `sensor_msgs/msg/Image` | Debug overlay |
| `/seg_ros/drivable_mask` | `sensor_msgs/msg/Image` | `mono8`, drivable area |
| `/seg_ros/lane_mask` | `sensor_msgs/msg/Image` | `mono8`, lane markings |
| `/seg_ros/lane_confidence` | `sensor_msgs/msg/Image` | `mono8`, current confidence proxy |
| `/seg_ros/label_info` | `vision_msgs/msg/LabelInfo` | Class metadata |
| `/seg_ros/detections` | `std_msgs/msg/String` | JSON detections |

## Repository Layout

```text
.
├── docs/
│   └── semantic_roadlines_pipeline.md
├── models/
│   └── README.md
├── proof/
│   ├── contact_sheet.jpg
│   └── exported proof overlays and masks
├── ros2_ws/
│   └── src/
│       └── seg_ros_bridge/
└── scripts/
    └── export_roadline_proof.py
```

## Model Weights

The expected pretrained checkpoint is:

```text
/home/alexander/Desktop/seg/data/weights/yolopv2.pt
```

It is about 150 MB, so it is not committed. See [models/README.md](models/README.md) for download/source notes.

## Build

```bash
cd ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select seg_ros_bridge
```

## Run

This project currently uses the Python runtime where Torch is installed:

```bash
source /opt/ros/jazzy/setup.bash
cd /home/alexander/Desktop/seg
/home/alexander/github/av-perception/.venv/bin/python \
  /home/alexander/Desktop/Competiton_Semantic_Segmentation/ros2_ws/src/seg_ros_bridge/seg_ros_bridge/seg_demo_node.py \
  --ros-args \
  -p project_root:=/home/alexander/Desktop/seg \
  -p image_dir:=/home/alexander/Desktop/seg/data/demo \
  -p weights_path:=/home/alexander/Desktop/seg/data/weights/yolopv2.pt \
  -p device:=cpu \
  -p publish_rate_hz:=0.5
```

Verify:

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic list | grep '^/seg_ros/'
ros2 topic echo /seg_ros/label_info --once
ros2 topic echo /seg_ros/lane_mask --once
```

## Export Proof Images

```bash
/home/alexander/github/av-perception/.venv/bin/python \
  scripts/export_roadline_proof.py \
  --project-root /home/alexander/Desktop/seg \
  --weights /home/alexander/Desktop/seg/data/weights/yolopv2.pt \
  --source-dir /home/alexander/Desktop/seg/data/demo \
  --output-dir /home/alexander/Desktop/roadline_demo_proof \
  --limit 6 \
  --device cpu
```

Observed proof counts:

```text
all2.jpg: lane_pixels=22216 drivable_pixels=342950
all3.jpg: lane_pixels=30512 drivable_pixels=252702
fs1.jpg: lane_pixels=29901 drivable_pixels=284413
fs2.jpg: lane_pixels=20362 drivable_pixels=168026
fs3.jpg: lane_pixels=2759 drivable_pixels=145975
lane1.jpg: lane_pixels=15326 drivable_pixels=73835
```

## Next Steps

1. Add a live image subscriber for `/camera/camera/color/image_raw`.
2. Keep the current image-folder publisher for reproducible demos.
3. Add TensorRT/ONNX export path for Jetson.
4. Compare YOLOPv2 against TwinLiteNetPlus on the same RealSense frames.
5. Feed drivable-area masks into the Nav2 semantic costmap integration.
