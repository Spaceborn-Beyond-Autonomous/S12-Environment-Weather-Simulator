#!/usr/bin/env python3
"""
===========================================================
S12 Environment & Weather Simulator
Generic Gazebo Harmonic World Generator

Author : Chetanya Barodiya & Team

Purpose:
    Generate a final Gazebo world by combining:

        World Input
             +
        Weather Effect
             |
             v
        generated_world.sdf

Architecture:

    Robot Integration
          |
          | world source (optional)
          v
    WorldGenerator
          |
          +---- selected weather effect
          |
          v
    Final Generated World
          |
          v
        Gazebo

Important:
    This module does NOT know which robot is being used.

    It can receive:
        1. A robot-specific world file
        2. No robot world -> use S12 base_world.sdf

    Robot-specific integration is handled outside this file.

Supported Effects:
    - clear
    - rain
    - snow
    - fog
    - dust
    - storm
===========================================================
"""

from pathlib import Path
import argparse
import shutil
import sys
from typing import Optional, Union


class WorldGenerator:
    """
    Generic Gazebo Harmonic world generator.

    The generator is intentionally robot-agnostic.

    It only knows how to:

        1. Select a world source.
        2. Load a weather effect.
        3. Inject the effect into the world.
        4. Generate the final SDF.

    Robot identity, URDF, robot launch files and robot
    spawning logic are NOT handled here.
    """

    SUPPORTED_EFFECTS = {
        "clear",
        "rain",
        "snow",
        "fog",
        "dust",
        "storm",
    }

    def __init__(
        self,
        world_source: Optional[Union[str, Path]] = None,
        output_world: Optional[Union[str, Path]] = None,
    ):
        # -------------------------------------------------
        # Current package directory
        # -------------------------------------------------

        self.package_dir = Path(__file__).resolve().parent

        # -------------------------------------------------
        # Gazebo directory
        # -------------------------------------------------

        self.gazebo_dir = self.package_dir

        # -------------------------------------------------
        # S12 world/effect directories
        # -------------------------------------------------

        self.worlds_dir = self.gazebo_dir / "worlds"

        self.effects_dir = self.gazebo_dir / "effects"

        # -------------------------------------------------
        # Default S12 base world
        # -------------------------------------------------

        self.base_world = (
            self.worlds_dir / "base_world.sdf"
        )

        # -------------------------------------------------
        # World supplied by integration layer
        # -------------------------------------------------

        self.world_source = (
            Path(world_source)
            if world_source is not None
            else None
        )

        # -------------------------------------------------
        # Final generated world
        # -------------------------------------------------

        if output_world is not None:

            self.generated_world = Path(
                output_world
            )

        else:

            self.generated_world = (
                self.worlds_dir /
                "generated_world.sdf"
            )

    # =====================================================
    # Validation
    # =====================================================

    def validate_effect(
        self,
        effect: str,
    ) -> str:
        """
        Validate requested weather effect.
        """

        if not isinstance(effect, str):
            raise TypeError(
                "Weather effect must be a string."
            )

        effect = effect.strip().lower()

        if effect not in self.SUPPORTED_EFFECTS:

            raise ValueError(
                f"Unsupported weather effect "
                f"'{effect}'.\n"
                f"Supported effects: "
                f"{', '.join(sorted(self.SUPPORTED_EFFECTS))}"
            )

        return effect

    # =====================================================
    # File Utilities
    # =====================================================

    @staticmethod
    def read_file(
        file_path: Path,
    ) -> str:
        """
        Read a text file.
        """

        file_path = Path(file_path)

        if not file_path.exists():

            raise FileNotFoundError(
                f"Missing file:\n{file_path}"
            )

        if not file_path.is_file():

            raise FileNotFoundError(
                f"Path is not a file:\n{file_path}"
            )

        return file_path.read_text(
            encoding="utf-8"
        )

    @staticmethod
    def write_file(
        file_path: Path,
        content: str,
    ):
        """
        Write generated world.
        """

        file_path = Path(file_path)

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path.write_text(
            content,
            encoding="utf-8",
        )

    # =====================================================
    # World Source Selection
    # =====================================================

    def resolve_world_source(self) -> Path:
        """
        Select the world that will be used as the source.

        Priority:

            1. Integration supplied world
            2. S12 base_world.sdf

        Therefore:

            Robot has own world
                    |
                    v
            use robot world

            Robot has no own world
                    |
                    v
            use S12 base_world.sdf
        """

        # -------------------------------------------------
        # Case 1:
        # Integration supplied a world
        # -------------------------------------------------

        if self.world_source is not None:

            world_path = self.world_source.expanduser()

            if not world_path.exists():

                raise FileNotFoundError(
                    "Integration supplied a world file, "
                    "but it does not exist:\n"
                    f"{world_path}"
                )

            if not world_path.is_file():

                raise FileNotFoundError(
                    "Integration world source is not "
                    f"a file:\n{world_path}"
                )

            print(
                "World source : "
                f"integration -> {world_path}"
            )

            return world_path

        # -------------------------------------------------
        # Case 2:
        # No robot-specific world
        # -------------------------------------------------

        if self.base_world.exists():

            print(
                "World source : "
                f"S12 base world -> {self.base_world}"
            )

            return self.base_world

        # -------------------------------------------------
        # Nothing available
        # -------------------------------------------------

        raise FileNotFoundError(
            "No world source available.\n"
            "Provide an integration world or create:\n"
            f"{self.base_world}"
        )

    # =====================================================
    # Load World
    # =====================================================

    def load_world(
        self,
    ) -> str:
        """
        Load the selected world source.
        """

        world_path = self.resolve_world_source()

        world_text = self.read_file(
            world_path
        )

        if "<world" not in world_text:

            raise RuntimeError(
                "Invalid Gazebo world file.\n"
                f"' <world ' tag not found in:\n"
                f"{world_path}"
            )

        if "</world>" not in world_text:

            raise RuntimeError(
                "Invalid Gazebo world file.\n"
                f"'</world>' tag not found in:\n"
                f"{world_path}"
            )

        return world_text

    # =====================================================
    # Load Weather Effect
    # =====================================================

    def load_effect(
        self,
        effect: str,
    ) -> str:
        """
        Load the selected weather effect.

        Example:

            rain
              |
              v
            effects/rain.sdf
        """

        effect = self.validate_effect(
            effect
        )

        # -------------------------------------------------
        # Clear weather
        # -------------------------------------------------

        if effect == "clear":

            return ""

        # -------------------------------------------------
        # Weather effect file
        # -------------------------------------------------

        effect_file = (
            self.effects_dir /
            f"{effect}.sdf"
        )

        return self.read_file(
            effect_file
        )

    # =====================================================
    # Backup
    # =====================================================

    def backup_generated_world(self):
        """
        Backup previous generated world.
        """

        if not self.generated_world.exists():

            return

        backup = (
            self.generated_world
            .with_suffix(".bak")
        )

        shutil.copy2(
            self.generated_world,
            backup
        )

        print(
            f"Previous generated world backed up to:\n"
            f"{backup}"
        )

    # =====================================================
    # Remove Previous Weather Effect
    # =====================================================

    @staticmethod
    def remove_previous_effect(
        world_text: str,
    ) -> str:
        """
        Prevent repeated weather insertion.

        This is intentionally generic.

        Weather blocks generated by this system are
        surrounded by:

            <!-- S12_WEATHER_EFFECT_START -->

            ...

            <!-- S12_WEATHER_EFFECT_END -->
        """

        start_marker = (
            "<!-- S12_WEATHER_EFFECT_START -->"
        )

        end_marker = (
            "<!-- S12_WEATHER_EFFECT_END -->"
        )

        while (
            start_marker in world_text
            and end_marker in world_text
        ):

            start_index = world_text.index(
                start_marker
            )

            end_index = world_text.index(
                end_marker,
                start_index,
            )

            end_index += len(
                end_marker
            )

            world_text = (
                world_text[:start_index]
                + world_text[end_index:]
            )

        return world_text

    # =====================================================
    # Insert Weather Effect
    # =====================================================

    @staticmethod
    def insert_weather_effect(
        world_text: str,
        effect_text: str,
    ) -> str:
        """
        Insert weather effect before </world>.
        """

        world_end = "</world>"

        if world_end not in world_text:

            raise RuntimeError(
                "Invalid Gazebo world:\n"
                "'</world>' tag not found."
            )

        if not effect_text.strip():

            return world_text

        weather_block = f"""
    <!-- S12_WEATHER_EFFECT_START -->

{effect_text.rstrip()}

    <!-- S12_WEATHER_EFFECT_END -->

"""

        return world_text.replace(
            world_end,
            weather_block +
            world_end,
            1,
        )

    # =====================================================
    # Particle Emitter Plugin
    # =====================================================

    @staticmethod
    def particle_plugin() -> str:
        """
        Gazebo ParticleEmitter system.

        Required by effects such as:
            rain
            snow
            dust
        """

        return """
    <plugin
        filename="gz-sim-particle-emitter-system"
        name="gz::sim::systems::ParticleEmitter"/>
"""

    # =====================================================
    # Insert Particle Plugin
    # =====================================================

    def insert_particle_plugin(
        self,
        world_text: str,
    ) -> str:
        """
        Add Gazebo ParticleEmitter plugin when needed.

        If already present, nothing is changed.
        """

        plugin_name = (
            "gz::sim::systems::ParticleEmitter"
        )

        if plugin_name in world_text:

            return world_text

        world_end = "</world>"

        if world_end not in world_text:

            raise RuntimeError(
                "Invalid Gazebo world:\n"
                "'</world>' tag not found."
            )

        return world_text.replace(
            world_end,
            self.particle_plugin()
            + "\n"
            + world_end,
            1,
        )

    # =====================================================
    # Generate World
    # =====================================================

    def generate_world(
        self,
        effect: str = "clear",
    ) -> Path:
        """
        Generate final Gazebo world.

        Pipeline:

            Integration World
                    |
                    | OR
                    v
              S12 Base World
                    |
                    v
             Remove old effect
                    |
                    v
              Add new effect
                    |
                    v
          generated_world.sdf
        """

        effect = self.validate_effect(
            effect
        )

        print("=" * 60)
        print(
            " S12 Environment Weather Simulator"
        )
        print("=" * 60)

        print(
            f"Weather effect : {effect}"
        )

        # -------------------------------------------------
        # Load selected world source
        # -------------------------------------------------

        world_text = self.load_world()

        # -------------------------------------------------
        # Remove previously generated S12 effect
        # -------------------------------------------------

        world_text = (
            self.remove_previous_effect(
                world_text
            )
        )

        # -------------------------------------------------
        # Clear weather
        # -------------------------------------------------

        if effect == "clear":

            self.backup_generated_world()

            self.write_file(
                self.generated_world,
                world_text,
            )

            print(
                "Weather       : CLEAR"
            )

            print(
                "No weather effect inserted."
            )

            print(
                f"Generated world:\n"
                f"{self.generated_world}"
            )

            return self.generated_world

        # -------------------------------------------------
        # Load weather effect
        # -------------------------------------------------

        effect_text = self.load_effect(
            effect
        )

        # -------------------------------------------------
        # Particle effects
        # -------------------------------------------------

        if effect in {
            "rain",
            "snow",
            "dust",
            "storm",
        }:

            world_text = (
                self.insert_particle_plugin(
                    world_text
                )
            )

        # -------------------------------------------------
        # Insert weather
        # -------------------------------------------------

        world_text = (
            self.insert_weather_effect(
                world_text,
                effect_text,
            )
        )

        # -------------------------------------------------
        # Backup previous generated world
        # -------------------------------------------------

        self.backup_generated_world()

        # -------------------------------------------------
        # Write final world
        # -------------------------------------------------

        self.write_file(
            self.generated_world,
            world_text,
        )

        # -------------------------------------------------
        # Output information
        # -------------------------------------------------

        print(
            f"Weather       : {effect}"
        )

        print(
            "Weather effect inserted successfully."
        )

        print(
            f"Generated world:\n"
            f"{self.generated_world}"
        )

        return self.generated_world

    # =====================================================
    # Preview
    # =====================================================

    def preview(
        self,
        effect: str,
    ):
        """
        Generate and print final world path.
        """

        world = self.generate_world(
            effect
        )

        print(
            "\nGeneration completed successfully."
        )

        print(
            f"Output:\n{world}"
        )


# =========================================================
# Command Line Interface
# =========================================================

def build_argument_parser():

    parser = argparse.ArgumentParser(
        description=(
            "Generic Gazebo Harmonic "
            "Environment World Generator"
        )
    )

    parser.add_argument(
        "--effect",
        "-e",
        type=str,
        default="clear",
        choices=sorted(
            WorldGenerator.SUPPORTED_EFFECTS
        ),
        help="Weather effect to generate.",
    )

    parser.add_argument(
        "--world",
        "-w",
        type=str,
        default=None,
        help=(
            "Optional integration world file. "
            "If omitted, S12 base_world.sdf is used."
        ),
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help=(
            "Optional path for generated world."
        ),
    )

    return parser


# =========================================================
# Main
# =========================================================

def main():

    parser = build_argument_parser()

    args = parser.parse_args()

    try:

        generator = WorldGenerator(
            world_source=args.world,
            output_world=args.output,
        )

        world_path = generator.generate_world(
            effect=args.effect
        )

        print(
            "\n"
            + "-" * 60
        )

        print(
            " World generation successful"
        )

        print(
            "-" * 60
        )

        print(
            f"Effect          : {args.effect}"
        )

        if args.world:

            print(
                f"Input World     : {args.world}"
            )

        else:

            print(
                "Input World     : S12 base_world.sdf"
            )

        print(
            f"Generated World : {world_path}"
        )

        print(
            "-" * 60
        )

        return 0

    except KeyboardInterrupt:

        print(
            "\nGeneration cancelled."
        )

        return 130

    except (
        FileNotFoundError,
        ValueError,
        TypeError,
        RuntimeError,
    ) as exc:

        print(
            "\nERROR"
        )

        print(
            "-" * 60
        )

        print(
            exc
        )

        print(
            "-" * 60
        )

        return 1

    except Exception as exc:

        print(
            "\nUnexpected Error"
        )

        print(
            "-" * 60
        )

        print(
            type(exc).__name__
        )

        print(
            exc
        )

        print(
            "-" * 60
        )

        return 1


# =========================================================
# Entry Point
# =========================================================

if __name__ == "__main__":
    sys.exit(main())