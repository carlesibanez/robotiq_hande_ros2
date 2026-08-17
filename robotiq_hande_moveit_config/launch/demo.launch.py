import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler, TimerAction
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    moveit_config = (
        MoveItConfigsBuilder("robotiq_hande", package_name="robotiq_hande_moveit_config")
        .robot_description(file_path="config/robotiq_hande.urdf.xacro")
        .to_moveit_configs()
    )

    pkg_share = get_package_share_directory("robotiq_hande_moveit_config")

    ld = LaunchDescription()

    ld.add_action(DeclareLaunchArgument("use_rviz", default_value="true"))
    ld.add_action(DeclareLaunchArgument("db", default_value="false"))
    ld.add_action(DeclareLaunchArgument("debug", default_value="false"))

    # 1. Robot State Publisher (publishes /robot_description and TF)
    rsp_launch = os.path.join(pkg_share, "launch", "rsp.launch.py")
    if os.path.exists(rsp_launch):
        ld.add_action(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(rsp_launch)
            )
        )

    # 2. Fake / Mock Hardware Controller Manager (ros2_control_node)
    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            moveit_config.robot_description,
            os.path.join(pkg_share, "config", "ros2_controllers.yaml"),
        ],
        output="screen",
    )
    ld.add_action(ros2_control_node)

    # 3. Spawn Controllers (delayed to allow ros2_control_node to initialize)
    load_jsb = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )
    load_gripper_ctrl = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller"],
    )

    delayed_spawners = TimerAction(
        period=2.0,
        actions=[
            load_jsb,
            RegisterEventHandler(
                event_handler=OnProcessExit(
                    target_action=load_jsb,
                    on_exit=[load_gripper_ctrl],
                )
            ),
        ],
    )
    ld.add_action(delayed_spawners)

    # 4. Move Group (MoveIt planning brain)
    move_group_launch = os.path.join(pkg_share, "launch", "move_group.launch.py")
    if os.path.exists(move_group_launch):
        ld.add_action(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(move_group_launch)
            )
        )

    # 5. RViz with MoveIt plugin
    moveit_rviz_launch = os.path.join(pkg_share, "launch", "moveit_rviz.launch.py")
    if os.path.exists(moveit_rviz_launch):
        ld.add_action(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(moveit_rviz_launch),
                condition=IfCondition(LaunchConfiguration("use_rviz")),
            )
        )

    return ld
