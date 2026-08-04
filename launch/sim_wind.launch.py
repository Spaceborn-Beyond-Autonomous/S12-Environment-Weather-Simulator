import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('ansa_digital_twin')
    world_path = os.path.join(pkg_share, 'worlds', 'ansa_world_wind.sdf')

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=world_path,
            description='SDF world file path'
        ),

        # 1. Gazebo Sim
        ExecuteProcess(
            cmd=['gz', 'sim', '-r', LaunchConfiguration('world')],
            output='screen'
        ),

        # 2. Wind Engine Physics Node
        Node(
            package='ansa_digital_twin',
            executable='wind_simulation_node.py',
            name='wind_simulation_node',
            output='screen',
            parameters=[{
                'enable_shear': True,
                'enable_turbulence': True,
                'base_wind_x': 5.0,
                'base_wind_y': 2.0
            }]
        ),

        # 3. Digital Twin Dashboard Server
        Node(
            package='ansa_digital_twin',
            executable='dt_server.py',
            name='dt_server_node',
            output='screen'
        )
    ])