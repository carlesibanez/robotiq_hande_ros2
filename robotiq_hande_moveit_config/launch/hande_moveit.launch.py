import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument(
            "use_sim",
            default_value="false",
            description="Whether to run in Gazebo simulation (true) or on real gripper hardware (false).",
        ),
        DeclareLaunchArgument(
            "use_camera",
            default_value="true",
            description="Whether to load wrist camera and mount.",
        ),
        DeclareLaunchArgument(
            "com_port",
            default_value="/tmp/ttyUR",
            description="Serial port for real Robotiq gripper (e.g. /tmp/ttyUR or /dev/ttyUSB0).",
        ),
        DeclareLaunchArgument(
            "finger_type",
            default_value="aluminum",
            description="Finger type: 'aluminum' or 'v1'.",
        ),
        DeclareLaunchArgument(
            "use_rviz",
            default_value="true",
            description="Whether to launch RViz2.",
        ),
    ]

    use_sim = LaunchConfiguration("use_sim")
    use_camera = LaunchConfiguration("use_camera")
    com_port = LaunchConfiguration("com_port")
    finger_type = LaunchConfiguration("finger_type")
    use_rviz = LaunchConfiguration("use_rviz")

    desc_pkg_share = get_package_share_directory("robotiq_hande_description")
    control_pkg_share = get_package_share_directory("robotiq_hande_control")
    moveit_pkg_share = get_package_share_directory("robotiq_hande_moveit_config")

    urdf_file = os.path.join(desc_pkg_share, "urdf", "gripper.urdf.xacro")
    controllers_file_hardware = os.path.join(control_pkg_share, "config", "controllers_hardware.yaml")

    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name="xacro")]),
        " ",
        urdf_file,
        " use_sim:=", use_sim,
        " use_camera:=", use_camera,
        " finger_type:=", finger_type,
        " com_port:=", com_port,
    ])

    robot_description = {"robot_description": ParameterValue(robot_description_content, value_type=str)}

    # 1. Simulation Pipeline (use_sim == true)
    sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(control_pkg_share, "launch", "hande_sim_control.launch.py")
        ),
        launch_arguments={
            "use_camera": use_camera,
        }.items(),
        condition=IfCondition(use_sim),
    )

    # 2. Hardware Pipeline (use_sim == false)
    # Robot State Publisher
    rsp_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": False}],
        condition=UnlessCondition(use_sim),
    )

    # Hardware ros2_control_node
    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_description, controllers_file_hardware],
        output="screen",
        condition=UnlessCondition(use_sim),
    )

    # Spawner for joint_state_broadcaster
    load_jsb = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        condition=UnlessCondition(use_sim),
    )

    # Spawner for gripper_controller
    load_gripper_ctrl = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller", "--controller-manager", "/controller_manager"],
        condition=UnlessCondition(use_sim),
    )

    # Delayed spawner to ensure controller_manager is initialized
    delayed_spawners = TimerAction(
        period=2.0,
        actions=[
            load_jsb,
            load_gripper_ctrl,
        ],
        condition=UnlessCondition(use_sim),
    )

    # 3. MoveIt 2 Setup
    moveit_config = (
        MoveItConfigsBuilder("robotiq_hande", package_name="robotiq_hande_moveit_config")
        .robot_description(file_path="config/robotiq_hande.urdf.xacro")
        .to_moveit_configs()
    )

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            robot_description,
            {"use_sim_time": use_sim},
        ],
    )

    # 4. RViz2
    rviz_config_file = os.path.join(moveit_pkg_share, "config", "moveit.rviz")
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config_file],
        parameters=[
            robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            {"use_sim_time": use_sim},
        ],
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription(
        declared_arguments
        + [
            sim_launch,
            rsp_node,
            ros2_control_node,
            delayed_spawners,
            move_group_node,
            rviz_node,
        ]
    )
