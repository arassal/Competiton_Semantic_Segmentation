from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'venv_python',
            default_value='/home/alexander/github/av-perception/.venv/bin/python',
        ),
        DeclareLaunchArgument(
            'image_dir',
            default_value='/home/alexander/Desktop/img',
        ),
        DeclareLaunchArgument(
            'replay_topic',
            default_value='/seg_ros/demo/input_image',
        ),
        DeclareLaunchArgument(
            'fps',
            default_value='1.0',
        ),
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
        ),
        DeclareLaunchArgument(
            'rviz_config',
            default_value=(
                '/home/alexander/Desktop/Competiton_Semantic_Segmentation/'
                'ros2_ws/src/seg_ros_bridge/rviz/segformer.rviz'
            ),
        ),
        ExecuteProcess(
            cmd=[
                'ros2', 'run', 'seg_ros_bridge', 'image_replay_node',
                '--ros-args',
                '-p', ['image_dir:=', LaunchConfiguration('image_dir')],
                '-p', ['image_topic:=', LaunchConfiguration('replay_topic')],
                '-p', ['fps:=', LaunchConfiguration('fps')],
            ],
            output='screen',
        ),
        ExecuteProcess(
            cmd=[
                LaunchConfiguration('venv_python'),
                (
                    '/home/alexander/Desktop/Competiton_Semantic_Segmentation/'
                    'ros2_ws/src/seg_ros_bridge/seg_ros_bridge/segformer_node.py'
                ),
                '--ros-args',
                '-p', ['image_topic:=', LaunchConfiguration('replay_topic')],
                '-p', 'publish_input_image:=true',
                '-p', 'enable_hsv_refinement:=true',
                '-p', 'nav2_publish_grid:=true',
            ],
            output='screen',
        ),
        ExecuteProcess(
            cmd=['rviz2', '-d', LaunchConfiguration('rviz_config')],
            condition=IfCondition(LaunchConfiguration('use_rviz')),
            output='screen',
        ),
    ])
