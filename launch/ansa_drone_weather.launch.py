#!/usr/bin/env python3

"""
===========================================================
ANSA Drone + Weather Integration Launch
===========================================================

Purpose:
    Launch the ANSA Digital Twin drone together with
    an environment/weather effect in the SAME Gazebo world.

Architecture:

    ANSA Drone Integration
            |
            v
    world_generator.py
            |
            +---- Drone world (if provided)
            |
            +---- Weather effect
            |
            v
    generated_world.sdf
            |
            v
         Gazebo
            |
            +---- ANSA Drone
            +---- Weather Effect
            +---- ROS-Gazebo Bridge
            +---- Robot State Publisher

The WorldGenerator itself does not know which robot
is being integrated.

Supported effects:
    clear
    rain
    snow
    fog
    dust
    storm
===========================================================
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import ExecuteProcess
from launch.actions import TimerAction

from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():

    # ====================================================
    # Package paths
    # ====================================================

    env_pkg = get_package_share_directory(
        'environment_weather_simulator'
    )

    # ====================================================
    # Launch arguments
    # ====================================================

    effect = LaunchConfiguration('effect')

    declare_effect = DeclareLaunchArgument(
        'effect',
        default_value='clear',
        description=(
            'Weather effect to apply: '
            'clear, rain, snow, fog, dust, storm'
        )
    )

    # ====================================================
    # Paths
    # ====================================================

    world_generator = os.path.join(
        env_pkg,
        'gazebo',
        'world_generator.py'
    )

    generated_world = os.path.join(
        env_pkg,
        'gazebo',
        'worlds',
        'generated_world.sdf'
    )

    # ====================================================
    # 1. Generate final world
    # ====================================================

    generate_world = ExecuteProcess(
        cmd=[
            'python3',
            world_generator,
            '--effect',
            effect
        ],
        output='screen'
    )

    # ====================================================
    # 2. Start Gazebo with generated world
    # ====================================================

    gazebo = TimerAction(
        period=2.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    'gz',
                    'sim',
                    '-r',
                    generated_world
                ],
                output='screen'
            )
        ]
    )

    # ====================================================
    # 3. Spawn ANSA Drone
    # ====================================================
    #
    # IMPORTANT:
    #
    # The drone description is supplied by the integration
    # launch layer.
    #
    # world_generator.py does NOT know about ANSA Drone.
    #
    # This keeps the generator generic.
    #
    # ====================================================

    drone_pkg = get_package_share_directory(
        'ansa_digital_twin'
    )

    urdf_path = os.path.join(
        drone_pkg,
        'urdf',
        'Drone_Full.urdf'
    )

    meshes_dir = os.path.join(
        drone_pkg,
        'meshes'
    )

    # ----------------------------------------------------
    # Read URDF
    # ----------------------------------------------------

    with open(urdf_path, 'r') as file:
        robot_desc = file.read()

    # ----------------------------------------------------
    # Convert package:// mesh paths to file:// paths
    # ----------------------------------------------------

    robot_desc = robot_desc.replace(
        'package://ansa_digital_twin/meshes/',
        'file://' + meshes_dir + '/'
    )

    # ====================================================
    # Spawn drone after Gazebo starts
    # ====================================================

    spawn_drone = TimerAction(
        period=6.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    'ros2',
                    'run',
                    'ros_gz_sim',
                    'create',

                    '-name',
                    'ansa_drone',

                    '-string',
                    robot_desc,

                    '-x',
                    '0',

                    '-y',
                    '0',

                    '-z',
                    '0.5',

                    '-world',
                    'default'
                ],
                output='screen'
            )
        ]
    )

    # ====================================================
    # 4. ROS2 <-> Gazebo Bridge
    # ====================================================

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',

        arguments=[

            '/imu/data'
            '@sensor_msgs/msg/Imu'
            '@gz.msgs.IMU',

            '/gps/fix'
            '@sensor_msgs/msg/NavSatFix'
            '@gz.msgs.NavSat',

            '/baro/data'
            '@sensor_msgs/msg/FluidPressure'
            '@gz.msgs.FluidPressure',

            '/model/ansa_drone/odometry'
            '@nav_msgs/msg/Odometry'
            '@gz.msgs.Odometry',

            '/model/ansa_drone/battery/'
            'ansa_drone_battery/state'
            '@sensor_msgs/msg/BatteryState'
            '@gz.msgs.BatteryState',

            '/ansa_drone/cmd_vel'
            '@geometry_msgs/msg/Twist'
            '@gz.msgs.Twist',

            '/ansa_drone/enable'
            '@std_msgs/msg/Bool'
            '@gz.msgs.Boolean',
        ],

        remappings=[
            (
                '/model/ansa_drone/battery/'
                'ansa_drone_battery/state',

                '/battery_state'
            ),
        ],

        output='screen'
    )

    # ====================================================
    # 5. Robot State Publisher
    # ====================================================

    robot_state_publisher = Node(
        package='robot_state_publisher',

        executable='robot_state_publisher',

        parameters=[
            {
                'robot_description': robot_desc
            }
        ],

        output='screen'
    )

    # ====================================================
    # Launch Description
    # ====================================================

    return LaunchDescription([

        # Arguments
        declare_effect,

        # Generate final SDF
        generate_world,

        # Start Gazebo
        gazebo,

        # Spawn drone
        spawn_drone,

        # ROS <-> Gazebo bridge
        bridge,

        # Robot TF/state publisher
        robot_state_publisher,

    ])