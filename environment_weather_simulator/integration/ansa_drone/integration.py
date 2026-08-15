#!/usr/bin/env python3

"""
===========================================================
ANSA Drone Integration
S12 Environment & Weather Simulator
===========================================================

Purpose:
    Provides ANSA Digital Twin robot information to the
    Environment Weather Simulator.

Important:
    WorldGenerator does NOT know that this is an ANSA drone.

    This integration module is responsible for providing:

        1. Robot URDF
        2. Robot mesh directory
        3. Robot world file (if available)
        4. Robot name
        5. Spawn position
        6. Spawn orientation

The WorldGenerator only consumes this information.

Architecture:

    ANSA Digital Twin
            |
            v
    ANSADroneIntegration
            |
            v
    Robot Integration Data
            |
            v
    WorldGenerator
            |
            +---- Robot World / Base World
            |
            +---- Weather Effect
            |
            v
    generated_world.sdf
===========================================================
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class RobotIntegrationData:
    """
    Generic robot integration data.

    This structure is intentionally robot-independent.

    WorldGenerator can use this object without knowing
    which robot is being integrated.
    """

    name: str

    urdf_path: Path

    meshes_path: Path

    world_path: Path | None

    spawn_x: float = 0.0
    spawn_y: float = 0.0
    spawn_z: float = 0.5

    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0


class ANSADroneIntegration:
    """
    Integration adapter for the ANSA Digital Twin drone.

    This class contains ANSA-specific paths and information.

    WorldGenerator should never contain these paths directly.
    """

    ROBOT_NAME = "ansa_drone"

    PACKAGE_NAME = "ansa_digital_twin"

    def __init__(
        self,
        package_path: str | Path,
    ):
        """
        Parameters
        ----------
        package_path:
            Absolute path to the ANSA Digital Twin package.

        Example:

            ~/Spaceborn-Digital-Twin-main/src/ansa_digital_twin
        """

        self.package_path = Path(
            package_path
        ).expanduser().resolve()

        if not self.package_path.exists():
            raise FileNotFoundError(
                "ANSA Digital Twin package was not found:\n"
                f"{self.package_path}"
            )

        # -------------------------------------------------
        # Robot files
        # -------------------------------------------------

        self.urdf_path = (
            self.package_path
            / "urdf"
            / "Drone_Full.urdf"
        )

        self.meshes_path = (
            self.package_path
            / "meshes"
        )

        self.world_path = (
            self.package_path
            / "worlds"
            / "ansa_world.sdf"
        )

        # -------------------------------------------------
        # Validate robot files
        # -------------------------------------------------

        self.validate()

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

    def validate(self):
        """
        Validate the ANSA Digital Twin files required
        for integration.
        """

        if not self.urdf_path.exists():
            raise FileNotFoundError(
                "ANSA Drone URDF not found:\n"
                f"{self.urdf_path}"
            )

        if not self.meshes_path.exists():
            raise FileNotFoundError(
                "ANSA Drone meshes directory not found:\n"
                f"{self.meshes_path}"
            )

        # World is optional according to the integration
        # architecture.

        if not self.world_path.exists():

            print(
                "WARNING: ANSA Drone world file not found.\n"
                "Environment base world will be used."
            )

            self.world_path = None

    # -----------------------------------------------------
    # Robot data
    # -----------------------------------------------------

    def get_robot_data(self) -> RobotIntegrationData:
        """
        Return generic robot integration data.

        The returned object does not expose ANSA-specific
        implementation details to WorldGenerator.
        """

        return RobotIntegrationData(

            name=self.ROBOT_NAME,

            urdf_path=self.urdf_path,

            meshes_path=self.meshes_path,

            world_path=self.world_path,

            spawn_x=0.0,
            spawn_y=0.0,
            spawn_z=0.5,

            roll=0.0,
            pitch=0.0,
            yaw=0.0,
        )

    # -----------------------------------------------------
    # URDF
    # -----------------------------------------------------

    def read_urdf(self) -> str:
        """
        Read the ANSA Drone URDF.

        Mesh package URIs are converted to absolute
        file:// paths so Gazebo can resolve them.
        """

        urdf = self.urdf_path.read_text(
            encoding="utf-8"
        )

        package_uri = (
            f"package://{self.PACKAGE_NAME}/meshes/"
        )

        file_uri = (
            "file://"
            + str(self.meshes_path)
            + "/"
        )

        urdf = urdf.replace(
            package_uri,
            file_uri
        )

        return urdf

    # -----------------------------------------------------
    # Spawn configuration
    # -----------------------------------------------------

    def get_spawn_arguments(self) -> dict:
        """
        Return the robot spawn configuration.

        This is kept separate so future robots can provide
        different spawn positions without modifying the
        WorldGenerator.
        """

        return {
            "name": self.ROBOT_NAME,

            "x": 0.0,
            "y": 0.0,
            "z": 0.5,

            "roll": 0.0,
            "pitch": 0.0,
            "yaw": 0.0,
        }


# ---------------------------------------------------------
# Factory Function
# ---------------------------------------------------------

def create_integration(
    package_path: str | Path,
) -> ANSADroneIntegration:
    """
    Create the ANSA Drone integration.

    WorldGenerator / launch files can use this function
    without directly constructing the adapter class.
    """

    return ANSADroneIntegration(
        package_path
    )


# ---------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------

def main():

    """
    Simple integration test.

    This does NOT start Gazebo.

    It only verifies that the ANSA Digital Twin files
    can be located and loaded.
    """

    import argparse

    parser = argparse.ArgumentParser(
        description="Test ANSA Drone integration"
    )

    parser.add_argument(
        "--package-path",
        required=True,
        help=(
            "Path to ansa_digital_twin package"
        ),
    )

    args = parser.parse_args()

    try:

        integration = create_integration(
            args.package_path
        )

        robot = integration.get_robot_data()

        print("=" * 60)
        print("ANSA Drone Integration")
        print("=" * 60)

        print(
            f"Robot       : {robot.name}"
        )

        print(
            f"URDF        : {robot.urdf_path}"
        )

        print(
            f"Meshes      : {robot.meshes_path}"
        )

        print(
            f"World       : {robot.world_path}"
        )

        print(
            "Spawn       : "
            f"({robot.spawn_x}, "
            f"{robot.spawn_y}, "
            f"{robot.spawn_z})"
        )

        print("=" * 60)
        print("Integration validation successful.")
        print("=" * 60)

    except Exception as exc:

        print(
            "Integration validation failed:"
        )

        print(exc)

        raise


if __name__ == "__main__":
    main()