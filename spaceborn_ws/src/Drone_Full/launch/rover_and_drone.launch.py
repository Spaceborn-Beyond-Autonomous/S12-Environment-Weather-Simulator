from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    pkg_path = get_package_share_directory('Drone_Full')

    world_file  = os.path.join(pkg_path, 'worlds', 'urban_street.world')
    drone_urdf  = os.path.join(pkg_path, 'urdf', 'Drone_Full.urdf')
    rover_urdf  = os.path.join(pkg_path, 'urdf', 'rover.urdf')

    with open(drone_urdf, 'r') as f:
        drone_description = f.read()

    with open(rover_urdf, 'r') as f:
        rover_description = f.read()

    # ------------------------------------------------------------------ #
    # Gazebo
    # ------------------------------------------------------------------ #

    gazebo = ExecuteProcess(
        cmd=['gazebo', '--verbose', world_file, '-s', 'libgazebo_ros_factory.so'],
        output='screen'
    )

    # ------------------------------------------------------------------ #
    # Drone nodes  (namespace = /drone)
    # ------------------------------------------------------------------ #

    drone_rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace='drone',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': drone_description,
            'use_sim_time': True,
            # FIX: tell RSP to publish TF under /drone namespace
            'frame_prefix': '',
        }]
    )

    drone_jsp = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        namespace='drone',
        name='joint_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': drone_description,
            'use_sim_time': True,
        }]
    )

    drone_spawn = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'drone',
            '-topic', '/drone/robot_description',
            '-x', '0', '-y', '0', '-z', '0.2'
        ],
        output='screen'
    )

    # ------------------------------------------------------------------ #
    # Rover nodes  (namespace = /rover)
    # ------------------------------------------------------------------ #

    rover_rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace='rover',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': rover_description,
            'use_sim_time': True,
            'frame_prefix': '',
        }]
    )

    rover_jsp = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        namespace='rover',
        name='joint_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': rover_description,
            'use_sim_time': True,
        }]
    )

    rover_spawn = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'rover',
            '-topic', '/rover/robot_description',
            '-x', '2', '-y', '0', '-z', '0.2'
        ],
        output='screen'
    )

    # FIX: relay node so rear wheels also receive cmd_vel
    rover_cmd_vel_relay = Node(
        package='topic_tools',
        executable='relay',
        name='rover_cmd_vel_relay',
        arguments=['/rover/cmd_vel', '/rover/cmd_vel_rear'],
        output='screen'
    )

    return LaunchDescription([
        gazebo,

        # RSP + JSP start immediately
        drone_rsp,
        drone_jsp,
        rover_rsp,
        rover_jsp,

        # Spawn after 5 s so Gazebo is ready
        TimerAction(
            period=5.0,
            actions=[
                drone_spawn,
                rover_spawn,
                rover_cmd_vel_relay,   # FIX: relay starts after spawn
            ]
        )
    ])
