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
- [Model Weights](models/README.md)
- [Traffic Cone Detection Notes](docs/traffic_cones/README.md)

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

| Topic | Type | Purpose |
|---|---|---|
| `/seg_ros/input_image` | `sensor_msgs/msg/Image` | Source frame used for inference |
| `/seg_ros/overlay_image` | `sensor_msgs/msg/Image` | Debug image with segmentation overlay |
| `/seg_ros/drivable_mask` | `sensor_msgs/msg/Image` | Mono drivable-area mask |
| `/seg_ros/lane_mask` | `sensor_msgs/msg/Image` | Mono lane-line mask |
| `/seg_ros/lane_confidence` | `sensor_msgs/msg/Image` | Mono lane confidence image |
| `/seg_ros/label_info` | `vision_msgs/msg/LabelInfo` | Semantic class labels |
| `/seg_ros/detections` | `std_msgs/msg/String` | JSON detections from YOLOPv2 |

Competition object topics:

| Topic | Type | Purpose |
|---|---|---|
| `/seg_ros/competition_objects/input_image` | `sensor_msgs/msg/Image` | Source frame used for object inference |
| `/seg_ros/competition_objects/annotated_image` | `sensor_msgs/msg/Image` | Debug image with object boxes |
| `/seg_ros/competition_objects/detections` | `std_msgs/msg/String` | JSON object detections |

## Repository Layout

```text
docs/
  datasets_and_training.md
  ros2_semantic_segmentation_pipeline.png
  semantic_roadlines_pipeline.md
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
