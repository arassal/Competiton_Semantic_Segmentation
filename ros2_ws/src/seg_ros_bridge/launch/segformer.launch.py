from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'venv_python',
            default_value='/home/alexander/github/av-perception/.venv/bin/python',
            description='Python interpreter with torch, transformers, and ROS bindings.',
        ),
        DeclareLaunchArgument(
            'node_script',
            default_value=(
                '/home/alexander/Desktop/Competiton_Semantic_Segmentation/'
                'ros2_ws/src/seg_ros_bridge/seg_ros_bridge/segformer_node.py'
            ),
            description='Path to the SegFormer comparison node.',
        ),
        DeclareLaunchArgument(
            'image_topic',
            default_value='/zed/zed_node/rgb/color/rect/image',
            description='ZED X image topic to segment.',
        ),
        DeclareLaunchArgument(
            'model_id',
            default_value='nvidia/segformer-b0-finetuned-cityscapes-512-1024',
            description='Hugging Face SegFormer model id.',
        ),
        DeclareLaunchArgument('device', default_value='cpu'),
        DeclareLaunchArgument('process_every_n', default_value='1'),
        DeclareLaunchArgument('publish_input_image', default_value='true'),
        DeclareLaunchArgument('publish_timing', default_value='true'),

        ExecuteProcess(
            cmd=[
                LaunchConfiguration('venv_python'),
                LaunchConfiguration('node_script'),
                '--ros-args',
                '-p', ['image_topic:=', LaunchConfiguration('image_topic')],
                '-p', ['model_id:=', LaunchConfiguration('model_id')],
                '-p', ['device:=', LaunchConfiguration('device')],
                '-p', ['process_every_n:=', LaunchConfiguration('process_every_n')],
                '-p', ['publish_input_image:=', LaunchConfiguration('publish_input_image')],
                '-p', ['publish_timing:=', LaunchConfiguration('publish_timing')],
            ],
            output='screen',
        ),
    ])
