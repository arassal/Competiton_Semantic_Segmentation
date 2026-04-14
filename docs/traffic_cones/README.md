# Traffic Cone Detection

This branch adds traffic-cone-capable object detection to the ROS 2 perception proof.

## Model

Included checkpoint:

```text
models/roboflow_logistics_yolov8.pt
```

Source:

```text
https://blog.roboflow.com/logistics-object-detection-model/
```

The model is useful here because it has a native `traffic cone` class. COCO YOLO models do not.

Relevant classes for the competition stack:

```text
person
traffic cone
traffic light
road sign
car
truck
van
```

## ROS 2 Node

Node:

```text
competition_objects_node
```

Published topics:

```text
/seg_ros/competition_objects/input_image
/seg_ros/competition_objects/annotated_image
/seg_ros/competition_objects/detections
```

The detection topic is JSON in `std_msgs/msg/String` for now. That keeps the proof simple and easy to inspect.

## Proof Images

Actual road cone detections:

```text
proof/traffic_cones/actual_road_cone_contact_sheet.jpg
```

Combined semantic segmentation and traffic cone detections on the same road image:

```text
proof/combined/semantic_segmentation_plus_cones_road.jpg
proof/combined/semantic_segmentation_plus_cones_contact_sheet.jpg
```

The combined contact sheet follows the same format as the original semantic segmentation proof:

```text
original road frame | road/lane + cone overlay | drivable mask | lane mask
```

Annotation-based evaluation contact sheet:

```text
proof/traffic_cones/traffic_cone_eval_contact_sheet.jpg
```

Raw road-cone demo inputs:

```text
proof/traffic_cones/raw_road_inputs/
```

## Results

Annotation-based evaluation:

```text
images evaluated: 48
ground-truth cones: 167
predicted cones: 168
true positives: 139
false positives: 29
false negatives: 28
precision: 0.8274
recall: 0.8323
F1: 0.8299
```

Actual road-scene smoke test:

```text
non-cone road frames tested: 72
cone false positives on those frames: 0
selected road-cone scenes: 12
traffic cones detected: 59
```

## Re-run Evaluation

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

The dataset path is local because the full cone dataset is not committed. Only proof images and JSON summaries are included in this branch.

## Reliability Notes

This is reliable enough for the next ROS 2 integration step, but it still needs testing on the actual robot camera. The main risks are small distant cones, motion blur, low light, unusual cone colors, and partial occlusion.
