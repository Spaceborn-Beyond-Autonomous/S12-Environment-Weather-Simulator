#!/usr/bin/env python3

"""
weather.launch.py

Environment Weather Simulator

Supported launch:

ros2 launch environment_weather_simulator weather.launch.py effect:=rain
ros2 launch environment_weather_simulator weather.launch.py effect:=fog
ros2 launch environment_weather_simulator weather.launch.py effect:=snow
ros2 launch environment_weather_simulator weather.launch.py effect:=dust
ros2 launch environment_weather_simulator weather.launch.py effect:=storm
ros2 launch environment_weather_simulator weather.launch.py effect:=clear
"""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)

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
    """
    Executed after launch arguments have been resolved.
    """

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

    world_file = (
        package_share
        / "worlds"
        / "ansa_world.sdf"
    )

    generator_directory = package_share

    generated_directory = (
        package_share
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

    # ---------------------------------------------------------
    # Include ANSA Digital Twin simulator
    # ---------------------------------------------------------

    ansa_share = Path(
        get_package_share_directory(
            "ansa_digital_twin"
        )
    )

    sim_launch = (
        ansa_share
        / "launch"
        / "sim.launch.py"
    )

    

    simulator = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(sim_launch)
        ),
        launch_arguments={
            "world": generated_world
        }.items(),
    )

    return [
        simulator,
    ]


def generate_launch_description():
    """
    Launch description for the Environment Weather Simulator.

    Supported examples:

        ros2 launch environment_weather_simulator weather.launch.py effect:=rain
        ros2 launch environment_weather_simulator weather.launch.py effect:=fog
        ros2 launch environment_weather_simulator weather.launch.py effect:=snow
        ros2 launch environment_weather_simulator weather.launch.py effect:=dust
        ros2 launch environment_weather_simulator weather.launch.py effect:=storm
        ros2 launch environment_weather_simulator weather.launch.py effect:=clear
    """

    effect_argument = DeclareLaunchArgument(
        "effect",
        default_value="clear",
        description=(
            "Weather effect "
            "(clear, rain, fog, snow, dust, storm)"
        ),
    )

    setup_action = OpaqueFunction(
        function=launch_setup,
    )

    return LaunchDescription(
        [
            effect_argument,
            setup_action,
        ]
    )


# ---------------------------------------------------------------------
# Launch File Summary
# ---------------------------------------------------------------------

"""
Execution Flow
==============

1. User launches:

   ros2 launch environment_weather_simulator weather.launch.py effect:=rain

2. The launch argument 'effect' is resolved.

3. launch_setup() executes through OpaqueFunction.

4. WorldGenerator:

   - Loads worlds/ansa_world.sdf
   - Removes any previously injected weather block
   - Reads the requested generator file
       clear_generator.txt
       rain_generator.txt
       fog_generator.txt
       snow_generator.txt
       dust_generator.txt
       storm_generator.txt
   - Writes:

       generated_world/ansa_world.sdf

5. ansa_digital_twin/launch/sim.launch.py is included.

6. sim.launch.py receives:

       world:=generated_world/ansa_world.sdf

This file is intended to be imported by ROS 2 launch and therefore
does not require a standalone main() entry point.
"""        