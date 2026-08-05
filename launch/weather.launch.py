#!/usr/bin/env python3

"""
Environment Weather Simulator Launch File
Gazebo Harmonic + ROS2 Jazzy

Generates weather modified world and launches Gazebo.
"""

from pathlib import Path

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import OpaqueFunction
from launch.actions import IncludeLaunchDescription

from launch.substitutions import LaunchConfiguration

from launch.launch_description_sources import PythonLaunchDescriptionSource

from ament_index_python.packages import get_package_share_directory

from environment_weather_simulator.gazebo.world_generator import WorldGenerator


def launch_setup(context, *args, **kwargs):

    # Get weather effect
    effect = LaunchConfiguration("effect").perform(context)

    print("=" * 60)
    print(" Environment Weather Simulator")
    print("=" * 60)
    print(f"Weather : {effect}")


    # Generate world
    generator = WorldGenerator()

    generated_world = generator.generate_world(effect)

    print(f"Generated world:")
    print(generated_world)


    # Gazebo Harmonic launch file
    gz_sim_share = Path(
        get_package_share_directory("ros_gz_sim")
    )

    gz_launch = (
        gz_sim_share /
        "launch" /
        "gz_sim.launch.py"
    )


    return [

        IncludeLaunchDescription(

            PythonLaunchDescriptionSource(
                str(gz_launch)
            ),

            launch_arguments={

                "gz_args":
                f"-r {generated_world}"

            }.items(),

        )

    ]



def generate_launch_description():

    return LaunchDescription([

        DeclareLaunchArgument(

            "effect",

            default_value="clear",

            description=(
                "Weather Effect "
                "(clear, rain, snow, fog, dust, storm)"
            )

        ),


        OpaqueFunction(
            function=launch_setup
        )

    ])