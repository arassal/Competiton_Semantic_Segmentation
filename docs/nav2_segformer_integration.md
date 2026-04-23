# Nav2 SegFormer Integration

This branch publishes a **local keepout mask** for Nav2, not a global map.

## Published Nav2 Topics

| Topic | Type | Notes |
|---|---|---|
| `/seg_ros/segformer/nav2/filter_mask` | `nav_msgs/msg/OccupancyGrid` | keepout mask for Nav2 filter |
| `/seg_ros/segformer/nav2/drivable_grid` | `nav_msgs/msg/OccupancyGrid` | debug drivable grid |
| `/seg_ros/segformer/nav2/costmap_filter_info` | `nav2_msgs/msg/CostmapFilterInfo` | filter metadata |

## Grid Convention

- frame: `base_link`
- width: configurable, default `6.0 m`
- length: configurable, default `8.0 m`
- resolution: configurable, default `0.05 m`
- origin:
  - `x = 0.0`
  - `y = -width / 2`

This means the grid starts at the vehicle and extends forward.

## Projection Method

The current implementation uses a lower-image trapezoid and projects it into a local bird's-eye grid.

This is a pragmatic local planner representation, not a calibrated metric perception stack.

## Recommended Use

Use this branch with a **local Nav2 costmap filter**, not as a substitute for a proper global map.

Example config:

- [nav2_keepout_example.yaml](../config/nav2_keepout_example.yaml)

## Limits

- no depth fusion
- no LiDAR fusion
- no object-aware keepout beyond what the semantic road mask rejects
- projection is heuristic until calibrated against the actual camera geometry
