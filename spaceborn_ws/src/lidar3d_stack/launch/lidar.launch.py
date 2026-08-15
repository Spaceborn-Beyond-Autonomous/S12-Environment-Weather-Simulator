import os
from os import pathsep
from pathlib import Path
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    lidar3d_stack = get_package_share_directory("lidar3d_stack")

    # ── Launch Arguments ─────────────────────────────────────────────

    model_arg = DeclareLaunchArgument(
        name="model",
        default_value=os.path.join(lidar3d_stack, "description", "bot.urdf.xacro"),
        description="Absolute path to robot urdf file"
    )

    world_name_arg = DeclareLaunchArgument(
        name="world_name",
        default_value="lidar_world",
        description="World file name inside worlds/ folder"
    )

    lidar_profile_arg = DeclareLaunchArgument(
        name="lidar_profile",
        default_value="os1_64",
        description="LiDAR profile: os1_64 or vlp16"
    )
    robot_type_arg = DeclareLaunchArgument(
        name="robot_type",
        default_value="rover",
        description="Robot type: rover or drone"
    )
    # ── World Path ───────────────────────────────────────────────────

    world_path = PathJoinSubstitution([
        lidar3d_stack,
        "worlds",
        PythonExpression(expression=["'", LaunchConfiguration("world_name"), "'", " + '.sdf'"])
    ])

    # ── Gazebo Resource Path ─────────────────────────────────────────

    model_path = str(Path(lidar3d_stack).parent.resolve())
    model_path += pathsep + os.path.join(get_package_share_directory("lidar3d_stack"), "models")

    gazebo_resource_path = SetEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH",
        model_path
    )

    # ── Robot Description ─────────────────────────────────────────────

    robot_description = ParameterValue(
        Command([
            "xacro ",
            LaunchConfiguration("model"),
            " is_sim:=True",
            " lidar_profile:=", LaunchConfiguration("lidar_profile"),
            " robot_type:=", LaunchConfiguration("robot_type"),
        ]),
        value_type=str
    )

    # ── Nodes ─────────────────────────────────────────────────────────

    # 1. Robot State Publisher
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{
            "robot_description": robot_description,
            "use_sim_time": True
        }]
    )
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen'
    )

    # 2. Gazebo Harmonic
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory("ros_gz_sim"), "launch"),
            "/gz_sim.launch.py"
        ]),
        launch_arguments={
            "gz_args": [world_path, " -v 4 -r"]
        }.items()
    )

    # 3. Spawn Robot
    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-topic", "robot_description",
            "-name",  "bot",
            "-x", "0.0",
            "-y", "0.0",
            "-z", "5.0",
            "-R", "0.0",
            "-P", "0.0",
            "-Y", "0.0",
            "-static", 
        ],
    )

    # 4. Bridge — Harmonic uses gz.msgs
    gz_ros2_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="gz_ros2_bridge",
        output="screen",
        parameters=[{
            "config_file": os.path.join(lidar3d_stack, "config", "bridge.yaml"),
            "use_sim_time": True
        }]
    )

    # 5. RViz2
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", os.path.join(lidar3d_stack, "rviz", "lidar3d.rviz")],
    )

    return LaunchDescription([
        model_arg,
        world_name_arg,
        lidar_profile_arg,
        robot_type_arg,
        gazebo_resource_path,
        robot_state_publisher_node,
        joint_state_publisher_node,
        gazebo,
        gz_spawn_entity,
        gz_ros2_bridge,
        rviz_node,
    ])