import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_name = 'robotiq_hande_description'
    pkg_share = get_package_share_directory(pkg_name)
    urdf_path = os.path.join(pkg_share, 'urdf', 'gripper.urdf.xacro')

    finger_type_arg = DeclareLaunchArgument(
        'finger_type',
        default_value='aluminum',
        description='Type of fingers to mount: aluminum (default) or v1'
    )
    use_sim_arg = DeclareLaunchArgument(
        'use_sim',
        default_value='false',
        description='Whether to mock/simulate (true) or use real hardware camera (false)'
    )
    serial_no_arg = DeclareLaunchArgument(
        'serial_no',
        default_value='',
        description='RealSense device serial number (optional)'
    )

    finger_type = LaunchConfiguration('finger_type')
    use_sim = LaunchConfiguration('use_sim')
    serial_no = LaunchConfiguration('serial_no')

    # Parse the XACRO file into a standard URDF string
    robot_description = ParameterValue(
        Command(['xacro ', urdf_path, ' finger_type:=', finger_type, ' use_sim:=', use_sim]),
        value_type=str
    )

    # Node: Robot State Publisher
    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': False}]
    )

    # Node: Joint State Publisher GUI (for testing the sliders)
    jsp_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui'
    )

    # RealSense Camera Driver Launch (active when use_sim:=false)
    wrist_camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'wrist_camera.launch.py')
        ),
        launch_arguments={
            'serial_no': serial_no,
        }.items(),
        condition=UnlessCondition(use_sim),
    )

    # Node: RViz2
    rviz_config_file = os.path.join(pkg_share, 'rviz', 'display.rviz')

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file]
    )

    return LaunchDescription([
        finger_type_arg,
        use_sim_arg,
        serial_no_arg,
        rsp_node,
        jsp_gui_node,
        wrist_camera_launch,
        rviz_node,
    ])