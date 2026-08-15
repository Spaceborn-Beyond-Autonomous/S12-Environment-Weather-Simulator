from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_path = get_package_share_directory("Drone_Full")
    urdf_file = os.path.join(pkg_path, "urdf", "drone_experiment.urdf")
    world_file = os.path.join(pkg_path, "worlds", "urban_street.world")

    with open(urdf_file, "r") as f:
        robot_description = f.read()

    # Robot State Publisher
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": robot_description}]
    )

    # Joint State Publisher
    joint_state_publisher = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        output="screen",
        parameters=[{"robot_description": robot_description}]
    )

    # Gazebo Classic
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("gazebo_ros"),
                "launch",
                "gazebo.launch.py"
            )
        ),
        launch_arguments={
            "world": world_file,
            "verbose": "true"
        }.items()
    )

    # Spawn Robot
    spawn_robot = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        output="screen",
        arguments=[
            "-entity", "drone",
            "-topic", "robot_description",
            "-x", "0",
            "-y", "0",
            "-z", "0.2"
        ]
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        joint_state_publisher,
        spawn_robot
    ])
