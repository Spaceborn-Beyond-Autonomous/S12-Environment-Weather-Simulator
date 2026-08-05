from setuptools import setup, find_packages
from glob import glob
import os


package_name = "environment_weather_simulator"


setup(
    name=package_name,

    version="1.0.0",

    packages=find_packages(
        exclude=[
            "test",
            "tests"
        ]
    ),


    data_files=[

        # ROS2 package index registration
        (
            "share/ament_index/resource_index/packages",
            [
                "resource/" + package_name
            ],
        ),


        # package.xml
        (
            "share/" + package_name,
            [
                "package.xml"
            ],
        ),


        # Launch files
        (
            os.path.join(
                "share",
                package_name,
                "launch"
            ),
            glob(
                "launch/*.launch.py"
            ),
        ),


        # Configuration YAML
        (
            os.path.join(
                "share",
                package_name,
                "config"
            ),
            glob(
                "config/*.yaml"
            ),
        ),


        # Documentation
        (
            os.path.join(
                "share",
                package_name,
                "docs"
            ),
            glob(
                "docs/*"
            ),
        ),


        # Gazebo worlds
        (
            os.path.join(
                "share",
                package_name,
                "worlds"
            ),
            glob(
                "environment_weather_simulator/gazebo/worlds/*.sdf"
            ),
        ),


        # Gazebo weather effects
        (
            os.path.join(
                "share",
                package_name,
                "worlds",
                "effects"
            ),
            glob(
                "environment_weather_simulator/gazebo/effects/*.sdf"
            ),
        ),

    ],


    install_requires=[
        "setuptools",
        "PyYAML",
    ],


    zip_safe=True,


    maintainer="Chetanya Barodiya",

    description=(
        "Environment and Weather Simulator "
        "for Autonomous Systems"
    ),


    license="Apache-2.0",


    tests_require=[
        "pytest"
    ],


    entry_points={

        "console_scripts": [

            "world_generator = "
            "environment_weather_simulator.gazebo.world_generator:main",
            "wind_test = environment_weather_simulator.wind.__main__:main",
            "solar_test = environment_weather_simulator.solar_thermal.__main__:main",
            "emi_test = environment_weather_simulator.emi.__main__:main",

        ],

    },
)