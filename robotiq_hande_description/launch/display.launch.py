import os
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_name = 'robotiq_hande_description'
    pkg_share = get_package_share_directory(pkg_name)
    urdf_path = os.path.join(pkg_share, 'urdf', 'gripper.urdf.xacro')

    # Parse the XACRO file into a standard URDF string
    robot_description = ParameterValue(Command(['xacro ', urdf_path]), value_type=str)

    # Node: Robot State Publisher
    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}]
    )

    # Node: Joint State Publisher GUI (for testing the sliders)
    jsp_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui'
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
        rsp_node,
        jsp_gui_node,
        rviz_node
    ])