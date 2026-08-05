#!/usr/bin/env python3
"""
===========================================================
Environment Weather Simulator
World Generator (Gazebo Harmonic)

Author : Chetanya Barodiya & Team
Description:
    Generates a Gazebo Harmonic world by combining
    base_world.sdf with a selected weather effect.

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
import sys
import shutil


class WorldGenerator:
    """
    Generates Gazebo Harmonic worlds by injecting weather
    effect models into the base world.
    """

    SUPPORTED_EFFECTS = {
        "clear",
        "rain",
        "snow",
        "fog",
        "dust",
        "storm"
    }

    def __init__(self):

        # Current file directory
        self.package_dir = Path(__file__).resolve().parent

        # gazebo/
        self.gazebo_dir = self.package_dir

        # gazebo/worlds/
        self.worlds_dir = self.gazebo_dir / "worlds"

        # gazebo/effects/
        self.effects_dir = self.gazebo_dir / "effects"

        # Base world
        self.base_world = self.worlds_dir / "base_world.sdf"

        # Generated world
        self.generated_world = self.worlds_dir / "generated_world.sdf"

    # ----------------------------------------------------
    # Validation
    # ----------------------------------------------------

    def validate_effect(self, effect: str):

        effect = effect.lower()

        if effect not in self.SUPPORTED_EFFECTS:
            raise ValueError(
                f"Unsupported weather effect '{effect}'.\n"
                f"Supported effects: "
                f"{', '.join(sorted(self.SUPPORTED_EFFECTS))}"
            )

        return effect

    # ----------------------------------------------------
    # Read File
    # ----------------------------------------------------

    @staticmethod
    def read_file(file_path: Path) -> str:

        if not file_path.exists():
            raise FileNotFoundError(
                f"Missing file:\n{file_path}"
            )

        return file_path.read_text(
            encoding="utf-8"
        )

    # ----------------------------------------------------
    # Write File
    # ----------------------------------------------------

    @staticmethod
    def write_file(file_path: Path, content: str):

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        file_path.write_text(
            content,
            encoding="utf-8"
        )

    # ----------------------------------------------------
    # Read Effect
    # ----------------------------------------------------

    def load_effect(self, effect: str) -> str:

        effect = self.validate_effect(effect)

        # Clear weather uses only base world
        if effect == "clear":
            return ""

        effect_file = self.effects_dir / f"{effect}.sdf"

        return self.read_file(effect_file)

    # ----------------------------------------------------
    # Backup Generated World
    # ----------------------------------------------------

    def backup_generated_world(self):

        if not self.generated_world.exists():
            return

        backup = self.generated_world.with_suffix(".bak")

        shutil.copy2(
            self.generated_world,
            backup
        )

    # ----------------------------------------------------
    # Utility
    # ----------------------------------------------------

    @staticmethod
    def insert_before_world_end(
        world_text: str,
        effect_text: str
    ) -> str:

        tag = "</world>"

        if tag not in world_text:
            raise RuntimeError(
                "Invalid base_world.sdf "
                "('</world>' tag not found)"
            )

        return world_text.replace(
            tag,
            "\n"
            + effect_text
            + "\n\n"
            + tag
        )


    # ----------------------------------------------------
    # Particle Emitter Plugin
    # ----------------------------------------------------

    @staticmethod
    def particle_plugin() -> str:

        return """
    <plugin
      filename="gz-sim-particle-emitter-system"
      name="gz::sim::systems::ParticleEmitter"/>
"""

    # ----------------------------------------------------
    # Insert Particle Plugin
    # ----------------------------------------------------

    def insert_particle_plugin(
        self,
        world_text: str
    ) -> str:

        plugin_name = "gz::sim::systems::ParticleEmitter"

        # Already present
        if plugin_name in world_text:
            return world_text

        insert_after = (
            '<plugin\n'
            '      filename="gz-sim-navsat-system"\n'
            '      name="gz::sim::systems::NavSat"/>'
        )

        if insert_after in world_text:

            return world_text.replace(
                insert_after,
                insert_after +
                "\n" +
                self.particle_plugin()
            )

        # Fallback
        return world_text.replace(
            "</world>",
            self.particle_plugin() +
            "\n</world>"
        )

    # ----------------------------------------------------
    # Generate World
    # ----------------------------------------------------

    def generate_world(
        self,
        effect: str
    ) -> Path:

        effect = self.validate_effect(effect)

        print("=" * 60)
        print(" Environment Weather Simulator")
        print("=" * 60)
        print(f"Weather : {effect}")

        base_world_text = self.read_file(
            self.base_world
        )

        # ----------------------------------------
        # Clear Weather
        # ----------------------------------------

        if effect == "clear":

            self.write_file(
                self.generated_world,
                base_world_text
            )

            print("Clear weather selected.")
            print("No weather model inserted.")
            print(
                f"Generated:\n{self.generated_world}"
            )

            return self.generated_world

        # ----------------------------------------
        # Other Weather Effects
        # ----------------------------------------

        effect_text = self.load_effect(
            effect
        )

        world_text = self.insert_particle_plugin(
            base_world_text
        )

        world_text = self.insert_before_world_end(
            world_text,
            effect_text
        )

        self.backup_generated_world()

        self.write_file(
            self.generated_world,
            world_text
        )

        print(
            f"Inserted weather effect: {effect}"
        )

        print(
            f"Generated:\n{self.generated_world}"
        )

        return self.generated_world

    # ----------------------------------------------------
    # Preview
    # ----------------------------------------------------

    def preview(
        self,
        effect: str
    ):

        world = self.generate_world(effect)

        print("\nGeneration completed successfully.")

        print(f"\nOutput:\n{world}")



# ----------------------------------------------------
# Command Line
# ----------------------------------------------------

def build_argument_parser():

    parser = argparse.ArgumentParser(
        description="Gazebo Harmonic World Generator"
    )

    parser.add_argument(
        "--effect",
        "-e",
        type=str,
        default="clear",
        choices=sorted(WorldGenerator.SUPPORTED_EFFECTS),
        help="Weather effect to generate"
    )

    return parser


# ----------------------------------------------------
# Main
# ----------------------------------------------------

def main():

    parser = build_argument_parser()

    args = parser.parse_args()

    try:

        generator = WorldGenerator()

        world_path = generator.generate_world(
            args.effect
        )

        print("\n----------------------------------------")
        print(" World generation successful")
        print("----------------------------------------")
        print(f"Effect          : {args.effect}")
        print(f"Generated World : {world_path}")
        print("----------------------------------------")

        return 0

    except KeyboardInterrupt:

        print("\nGeneration cancelled.")

        return 130

    except FileNotFoundError as e:

        print("\nERROR")
        print("----------------------------------------")
        print(e)
        print("----------------------------------------")

        return 1

    except ValueError as e:

        print("\nERROR")
        print("----------------------------------------")
        print(e)
        print("----------------------------------------")

        return 1

    except Exception as e:

        print("\nUnexpected Error")
        print("----------------------------------------")
        print(type(e).__name__)
        print(e)
        print("----------------------------------------")

        return 1


# ----------------------------------------------------
# Entry Point
# ----------------------------------------------------

if __name__ == "__main__":
    sys.exit(main())