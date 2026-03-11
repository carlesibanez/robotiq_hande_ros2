import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    # 1. Launch the Simulation (Gazebo + Controllers)
    control_pkg_launch = os.path.join(
        get_package_share_directory('robotiq_hande_control'),
        'launch',
        'hande_sim_control.launch.py'
    )
    sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(control_pkg_launch)
    )

    # 2. Build MoveIt Parameters
    moveit_config = (
        MoveItConfigsBuilder("robotiq_hande", package_name="robotiq_hande_moveit_config")
        .robot_description(file_path="config/robotiq_hande.urdf.xacro")
        .to_moveit_configs()
    )

    # 3. Start the MoveIt Brain (move_group)
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            {"use_sim_time": True},
        ],
    )

    # 4. Start RViz with the MoveIt Plugin
    rviz_config_file = os.path.join(
        get_package_share_directory("robotiq_hande_moveit_config"),
        "config",
        "moveit.rviz",
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config_file],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            {"use_sim_time": True},
        ],
    )

    return LaunchDescription([
        sim_launch,
        move_group_node,
        rviz_node
    ])