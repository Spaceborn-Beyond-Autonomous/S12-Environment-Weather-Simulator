#!/usr/bin/env python3

from pathlib import Path

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from environment_weather_simulator.gazebo.world_generator import WorldGenerator


SUPPORTED_EFFECTS = (
    "clear",
    "rain",
    "fog",
    "snow",
    "dust",
    "storm",
    "wind",
    "thunder",
)


def launch_setup(context, *args, **kwargs):

    effect = LaunchConfiguration("effect").perform(context).lower()

    if effect not in SUPPORTED_EFFECTS:
        raise RuntimeError(
            f"Unsupported weather effect '{effect}'. "
            f"Supported effects: {', '.join(SUPPORTED_EFFECTS)}"
        )

    package_share = Path(
        get_package_share_directory(
            "environment_weather_simulator"
        )
    )

    # ------------------------------------------------------------------
    # Resources
    # ------------------------------------------------------------------

    gazebo_dir = package_share / "gazebo"

    world_file = (
        gazebo_dir
        / "worlds"
        / "base_world.sdf"
    )

    generator_directory = (
        gazebo_dir
        / "effects"
    )

    generated_directory = (
        gazebo_dir
        / "generated_world"
    )

    generated_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    generator = WorldGenerator(
        world_file=str(world_file),
        generator_directory=str(generator_directory),
        output_directory=str(generated_directory),
    )

    generated_world = generator.prepare_world(effect)

    # ------------------------------------------------------------------
    # Launch simulator
    # ------------------------------------------------------------------

    ansa_share = Path(
        get_package_share_directory(
            "ansa_digital_twin"
        )
    )

    simulator = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(
                ansa_share
                / "launch"
                / "sim.launch.py"
            )
        ),
        launch_arguments={
            "world": generated_world,
        }.items(),
    )

    return [
        simulator,
    ]


def generate_launch_description():

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "effect",
                default_value="clear",
                description="Weather effect",
            ),
            OpaqueFunction(
                function=launch_setup,
            ),
        ]
    )