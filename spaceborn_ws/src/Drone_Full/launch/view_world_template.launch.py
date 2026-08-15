from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    pkg_path = get_package_share_directory('Drone_Full')

    urdf_file = os.path.join(pkg_path, 'urdf', 'Drone_Full.urdf')
    world_file = os.path.join(pkg_path, 'worlds', 'world_jean.world')

    with open(urdf_file, 'r') as f:
        robot_description = f.read()

    # Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {'robot_description': robot_description}
        ]
    )

    # Joint State Publisher
    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
        parameters=[
            {'robot_description': robot_description}
        ]
    )

    # Gazebo Classic with custom world
    gazebo = ExecuteProcess(
        cmd=[
            'gazebo',
            '--verbose',
            world_file,
            '-s',
            'libgazebo_ros_factory.so'
        ],
        output='screen'
    )

    # Spawn robot from robot_description topic
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'drone',
            '-topic', 'robot_description',
            '-x', '1',
            '-y', '0',
            '-z', '0.5'
        ],
        output='screen'
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        joint_state_publisher,

        TimerAction(
            period=5.0,
            actions=[spawn_entity]
        )
    ])
