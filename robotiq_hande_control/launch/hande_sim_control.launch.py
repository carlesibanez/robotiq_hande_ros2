import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    desc_pkg_path = get_package_share_directory('robotiq_hande_description')
    control_pkg_path = get_package_share_directory('robotiq_hande_control')
    
    # Tell Gazebo where to find custom meshes
    model_paths = [os.path.dirname(desc_pkg_path)]
    if 'GZ_SIM_RESOURCE_PATH' in os.environ:
        os.environ['GZ_SIM_RESOURCE_PATH'] += f":{':'.join(model_paths)}"
    else:
        os.environ['GZ_SIM_RESOURCE_PATH'] = ":".join(model_paths)

    declare_camera = DeclareLaunchArgument(
        'use_camera',
        default_value='true',
        description='Whether to load wrist camera and bridges',
    )
    use_camera = LaunchConfiguration('use_camera')

    world_file = os.path.join(control_pkg_path, 'worlds', 'empty_sensors.sdf')
    urdf_file = PathJoinSubstitution([
        FindPackageShare('robotiq_hande_description'),
        'urdf',
        'gripper.urdf.xacro',
    ])

    robot_desc = ParameterValue(
        Command([
            PathJoinSubstitution([FindExecutable(name='xacro')]),
            ' ',
            urdf_file,
            ' use_sim:=true',
            ' use_camera:=', use_camera,
        ]),
        value_type=str,
    )

    gz_sim_launch = os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_sim_launch),
        launch_arguments={
            "gz_args": f"-r {world_file} --physics-engine gz-physics-bullet-featherstone-plugin"
        }.items(),
    )

    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_desc, 'use_sim_time': True}]
    )

    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-string', robot_desc, '-name', 'robotiq_hande', '-allow_renaming', 'true'],
        output='screen'
    )

    load_jsb = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
    )

    load_gripper_ctrl = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller", "--controller-manager", "/controller_manager"],
    )

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen'
    )

    camera_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/wrist_camera/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
            '/wrist_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
        ],
        output='screen',
        condition=IfCondition(use_camera),
    )

    image_bridge = Node(
        package='ros_gz_image',
        executable='image_bridge',
        arguments=['/wrist_camera/image', '/wrist_camera/depth_image'],
        output='screen',
        condition=IfCondition(use_camera),
    )

    return LaunchDescription([
        declare_camera,
        gazebo,
        clock_bridge,
        camera_bridge,
        image_bridge,
        node_robot_state_publisher,
        spawn_entity,
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_entity,
                on_exit=[load_jsb, load_gripper_ctrl],
            )
        ),
    ])