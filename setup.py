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


        # Gazebo world files
        (
            os.path.join(
                "share",
                package_name,
                "gazebo",
                "worlds"
            ),
            glob(
                "environment_weather_simulator/gazebo/worlds/*.sdf"
            ),
        ),

        # Gazebo weather effect files
        (
            os.path.join(
                "share",
                package_name,
                "gazebo",
                "effects"
            ),
            glob(
                "environment_weather_simulator/gazebo/effects/*.sdf"
            ),
        ),
        # Gazebo generator Python file
        (
            os.path.join(
                "share",
                package_name,
                "gazebo"
            ),
            [
                "environment_weather_simulator/gazebo/world_generator.py"
            ],
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
            "environment_publisher = environment_weather_simulator.integration.environment_publisher:main",

        ],

    },
)