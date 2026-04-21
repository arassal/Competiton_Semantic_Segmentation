# SegFormer Experiment

SegFormer is added as an optional comparison backend, not a replacement for the current YOLOPv2 + Roboflow pipeline.

## Why Test It

SegFormer can produce general semantic scene masks from road images. A Cityscapes-pretrained model can identify classes such as:

```text
road
sidewalk
person
car
truck
bus
traffic light
traffic sign
```

That may help with future semantic costmap work because it can provide a road-vs-sidewalk scene mask.

## Why It Is Not A Drop-In Replacement

The current project needs:

```text
drivable road
lane markings
traffic cones
people/objects
```

A standard Cityscapes SegFormer does not directly provide:

```text
lane_marking
traffic_cone
```

So the correct comparison is:

| Capability | Current YOLOPv2 + Roboflow | SegFormer Cityscapes |
|---|---|---|
| drivable/road mask | yes | road class only |
| lane-line mask | yes | no direct class |
| traffic cones | yes | no direct class |
| people/cars/signs | yes through object detector | semantic classes only |
| Nav2 semantic road/sidewalk cue | possible | potentially useful |

## Node

Node:

```text
segformer_node
```

Launch:

```bash
source /opt/ros/jazzy/setup.bash
source /home/alexander/Desktop/Competiton_Semantic_Segmentation/ros2_ws/install/setup.bash

ros2 launch seg_ros_bridge segformer.launch.py \
  image_topic:=/zed/zed_node/rgb/color/rect/image \
  model_id:=nvidia/segformer-b0-finetuned-cityscapes-512-1024 \
  device:=cpu
```

## Optional Dependency

The current runtime venv did not have `transformers` installed when this branch was created.

Install only if you want to run the SegFormer experiment:

```bash
/home/alexander/github/av-perception/.venv/bin/python -m pip install -r requirements-segformer.txt
```

The node intentionally fails with a clear error if `transformers` is missing.

## Topics

| Topic | Type | Meaning |
|---|---|---|
| `/seg_ros/segformer/input_image` | `sensor_msgs/msg/Image` | republished source frame |
| `/seg_ros/segformer/overlay_image` | `sensor_msgs/msg/Image` | semantic overlay |
| `/seg_ros/segformer/class_mask` | `sensor_msgs/msg/Image` | raw class-id mask |
| `/seg_ros/segformer/road_mask` | `sensor_msgs/msg/Image` | binary Cityscapes `road` class |
| `/seg_ros/segformer/sidewalk_mask` | `sensor_msgs/msg/Image` | binary Cityscapes `sidewalk` class |
| `/seg_ros/segformer/label_info` | `vision_msgs/msg/LabelInfo` | model class map |
| `/seg_ros/segformer/metadata` | `std_msgs/msg/String` | class pixel counts and timing |
| `/seg_ros/segformer/timing` | `std_msgs/msg/String` | per-frame runtime |

## How To Decide If It Is Better

Use the same ZED X frames for both pipelines.

Compare:

1. visual road mask quality
2. false road/sidewalk regions
3. lane-line usefulness
4. CPU/GPU runtime
5. whether output helps Nav2 more than YOLOPv2 drivable masks

Do not compare traffic-cone detection, because SegFormer Cityscapes does not have a traffic-cone class.

## Expected Outcome

SegFormer may be useful for:

- road vs sidewalk segmentation
- general semantic scene understanding
- future semantic costmap experiments

SegFormer is unlikely to replace the current pipeline unless:

- we fine-tune it on ZED X road/lane/cone labels, or
- road-vs-sidewalk segmentation becomes more important than lane-line segmentation.

## Local Smoke Test

The node was tested by publishing the saved combined road/cone proof image as a ROS image and reading `/seg_ros/segformer/metadata`.

Input:

```text
proof/source_images/road_cars_cones_input.jpg
```

Result on CPU:

```text
model: nvidia/segformer-b0-finetuned-cityscapes-512-1024
road pixels: 669,873
sidewalk pixels: 33,905
top classes: road, fence, car, building, vegetation, person
timing: about 963 ms/frame
```

This confirms the ROS node works and produces Cityscapes semantic masks. It does not prove that SegFormer is better than YOLOPv2 for lane-line segmentation, because the Cityscapes model does not provide a lane-line class.
