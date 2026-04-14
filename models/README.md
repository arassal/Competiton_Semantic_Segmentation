# Model Weights

The current semantic segmentation model is YOLOPv2.

Expected local checkpoint:

```text
/home/alexander/Desktop/seg/data/weights/yolopv2.pt
```

Source project:

```text
https://github.com/CAIC-AD/YOLOPv2
```

Source release URL:

```text
https://github.com/CAIC-AD/YOLOPv2/releases/download/V0.0.1/yolopv2.pt
```

The checkpoint is approximately 150 MB and is intentionally excluded from this repository. Use Git LFS or an external release artifact if the weight needs to be versioned with the project later.

## Included Competition Object Model

This repository includes one small YOLOv8 object-detection checkpoint:

```text
models/roboflow_logistics_yolov8.pt
```

It is used by `competition_objects_node` for traffic cones and related competition objects.

Source:

```text
https://blog.roboflow.com/logistics-object-detection-model/
```

The model includes these useful classes:

```text
person
traffic cone
traffic light
road sign
car
truck
van
```

It is committed because it is about 6 MB, unlike the 150 MB YOLOPv2 segmentation checkpoint.
