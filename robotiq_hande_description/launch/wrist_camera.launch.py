#!/usr/bin/env python3
"""
RealSense D405 Wrist Camera Launch File
Publishes all streams: Color, Depth, Infra 1 & 2, Aligned Depth, and Colored Point Cloud.
Optionally provides backwards-compatible topic aliases (/wrist_camera/image, etc.).
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # --------------------------------------------------------------------------
    # 1. Declare Launch Arguments
    # --------------------------------------------------------------------------
    camera_name_arg = DeclareLaunchArgument(
        'camera_name',
        default_value='wrist_camera',
        description='Camera unique name and topic prefix'
    )
    camera_namespace_arg = DeclareLaunchArgument(
        'camera_namespace',
        default_value='',
        description='Camera namespace (empty for top-level /<camera_name> topics)'
    )
    serial_no_arg = DeclareLaunchArgument(
        'serial_no',
        default_value='',
        description='RealSense device serial number (optional if only 1 device connected)'
    )
    enable_color_arg = DeclareLaunchArgument(
        'enable_color',
        default_value='true',
        description='Enable RGB color stream'
    )
    enable_depth_arg = DeclareLaunchArgument(
        'enable_depth',
        default_value='true',
        description='Enable depth stream'
    )
    enable_infra1_arg = DeclareLaunchArgument(
        'enable_infra1',
        default_value='true',
        description='Enable left infrared stream'
    )
    enable_infra2_arg = DeclareLaunchArgument(
        'enable_infra2',
        default_value='true',
        description='Enable right infrared stream'
    )
    align_depth_arg = DeclareLaunchArgument(
        'align_depth',
        default_value='true',
        description='Enable aligned depth-to-color stream'
    )
    enable_pointcloud_arg = DeclareLaunchArgument(
        'pointcloud_enable',
        default_value='true',
        description='Enable 3D colored point cloud'
    )
    enable_aliases_arg = DeclareLaunchArgument(
        'enable_aliases',
        default_value='true',
        description='Publish topic aliases (/wrist_camera/image, /wrist_camera/points)'
    )

    camera_name = LaunchConfiguration('camera_name')
    camera_namespace = LaunchConfiguration('camera_namespace')
    serial_no = LaunchConfiguration('serial_no')
    enable_color = LaunchConfiguration('enable_color')
    enable_depth = LaunchConfiguration('enable_depth')
    enable_infra1 = LaunchConfiguration('enable_infra1')
    enable_infra2 = LaunchConfiguration('enable_infra2')
    align_depth = LaunchConfiguration('align_depth')
    pointcloud_enable = LaunchConfiguration('pointcloud_enable')
    enable_aliases = LaunchConfiguration('enable_aliases')

    # --------------------------------------------------------------------------
    # 2. Include Official realsense2_camera Driver Launch
    # --------------------------------------------------------------------------
    realsense_camera_share = FindPackageShare('realsense2_camera')

    realsense_driver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([realsense_camera_share, 'launch', 'rs_launch.py'])
        ),
        launch_arguments={
            'camera_name': camera_name,
            'camera_namespace': camera_namespace,
            'device_type': 'd405',
            'serial_no': serial_no,
            'enable_color': enable_color,
            'enable_depth': enable_depth,
            'enable_infra1': enable_infra1,
            'enable_infra2': enable_infra2,
            'align_depth.enable': align_depth,
            'pointcloud.enable': pointcloud_enable,
            'publish_tf': 'true',
            'initial_reset': 'false',
        }.items(),
    )

    # --------------------------------------------------------------------------
    # 3. Topic Relays for Backwards-Compatibility
    # --------------------------------------------------------------------------
    # Aliases for existing perception nodes and RViz configs:
    # /wrist_camera/color/image_raw -> /wrist_camera/image
    # /wrist_camera/color/camera_info -> /wrist_camera/camera_info
    # /wrist_camera/depth/color/points -> /wrist_camera/points
    # /wrist_camera/depth/image_rect_raw -> /wrist_camera/depth_image
    relay_color = Node(
        package='topic_tools',
        executable='relay',
        name='relay_wrist_camera_image',
        arguments=['/wrist_camera/color/image_raw', '/wrist_camera/image'],
        output='screen',
        condition=IfCondition(enable_aliases),
    )

    relay_info = Node(
        package='topic_tools',
        executable='relay',
        name='relay_wrist_camera_info',
        arguments=['/wrist_camera/color/camera_info', '/wrist_camera/camera_info'],
        output='screen',
        condition=IfCondition(enable_aliases),
    )

    relay_points = Node(
        package='topic_tools',
        executable='relay',
        name='relay_wrist_camera_points',
        arguments=['/wrist_camera/depth/color/points', '/wrist_camera/points'],
        output='screen',
        condition=IfCondition(enable_aliases),
    )

    relay_depth = Node(
        package='topic_tools',
        executable='relay',
        name='relay_wrist_camera_depth',
        arguments=['/wrist_camera/depth/image_rect_raw', '/wrist_camera/depth_image'],
        output='screen',
        condition=IfCondition(enable_aliases),
    )

    return LaunchDescription([
        camera_name_arg,
        camera_namespace_arg,
        serial_no_arg,
        enable_color_arg,
        enable_depth_arg,
        enable_infra1_arg,
        enable_infra2_arg,
        align_depth_arg,
        enable_pointcloud_arg,
        enable_aliases_arg,
        realsense_driver,
        relay_color,
        relay_info,
        relay_points,
        relay_depth,
    ])
