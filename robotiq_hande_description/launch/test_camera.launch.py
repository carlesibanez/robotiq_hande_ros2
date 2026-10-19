#!/usr/bin/env python3
"""
Standalone Camera Test Launch File
Launches the RealSense D405 driver, publishes the standalone camera URDF/TF,
and opens RViz2 with pre-configured PointCloud2 and Image streams.
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_name = 'robotiq_hande_description'
    pkg_share = get_package_share_directory(pkg_name)

    # 1. Declare Arguments
    rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='true',
        description='Whether to launch RViz2 viewer'
    )
    serial_no_arg = DeclareLaunchArgument(
        'serial_no',
        default_value='',
        description='RealSense device serial number (optional if only 1 device connected)'
    )
    pointcloud_arg = DeclareLaunchArgument(
        'pointcloud',
        default_value='true',
        description='Enable 3D point cloud generation'
    )

    rviz = LaunchConfiguration('rviz')
    serial_no = LaunchConfiguration('serial_no')
    pointcloud = LaunchConfiguration('pointcloud')

    # 2. Standalone Robot State Publisher (Mount + RealSense D405 Mesh)
    urdf_path = os.path.join(pkg_share, 'urdf', 'd405_standalone.urdf.xacro')
    robot_description = ParameterValue(
        Command(['xacro ', urdf_path]),
        value_type=str
    )

    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='camera_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen'
    )

    # 3. Include RealSense Driver
    wrist_camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'wrist_camera.launch.py')
        ),
        launch_arguments={
            'serial_no': serial_no,
            'pointcloud_enable': pointcloud,
        }.items(),
    )

    # 4. RViz2 Viewer
    rviz_config_file = os.path.join(pkg_share, 'rviz', 'camera_viewer.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2_camera_viewer',
        output='screen',
        arguments=['-d', rviz_config_file],
        condition=IfCondition(rviz)
    )

    rqt_arg = DeclareLaunchArgument(
        'rqt',
        default_value='false',
        description='Whether to launch rqt_image_view'
    )
    rqt = LaunchConfiguration('rqt')

    rqt_node = Node(
        package='rqt_image_view',
        executable='rqt_image_view',
        name='rqt_image_view',
        output='screen',
        condition=IfCondition(rqt)
    )

    return LaunchDescription([
        rviz_arg,
        rqt_arg,
        serial_no_arg,
        pointcloud_arg,
        rsp_node,
        wrist_camera_launch,
        rviz_node,
        rqt_node,
    ])
