from setuptools import setup, find_packages
from glob import glob
import os

package_name = "environment_weather_simulator"

setup(
    name=package_name,
    version="1.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        # Register package
        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),

        # Package.xml
        (
            "share/" + package_name,
            ["package.xml"],
        ),

        # Launch files
        (
            os.path.join("share", package_name, "launch"),
            glob("launch/*.py"),
        ),

        # YAML configuration
        (
            os.path.join("share", package_name, "config"),
            glob("config/*.yaml"),
        ),

        # Documentation
        (
            os.path.join("share", package_name, "docs"),
            glob("docs/*"),
        ),

        # Gazebo worlds
        (
            os.path.join("share", package_name, "worlds"),
            glob("environment_weather_simulator/gazebo/worlds/*.sdf"),
        ),

        # Weather effect snippets
        (
            os.path.join("share", package_name, "worlds", "effects"),
            glob("environment_weather_simulator/gazebo/effects/*.sdf"),
        ),
    ],
    install_requires=[
        "setuptools",
        "PyYAML",
    ],
    zip_safe=True,
    maintainer="Chetanya Barodiya",
    maintainer_email="YOUR_EMAIL",
    description="Environment and Weather Simulator for Autonomous Systems",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "world_generator = environment_weather_simulator.gazebo.world_generator:main",
        ],
    },
)