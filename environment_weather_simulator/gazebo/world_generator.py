#!/usr/bin/env python3
"""
world_generator.py

Environment Weather Simulator
-----------------------------

This module dynamically injects weather effects into an existing
Gazebo SDF world (ansa_world.sdf).

Features
--------
✓ Works directly with ansa_world.sdf
✓ Reads weather snippets from:
    rain_generator.txt
    fog_generator.txt
    snow_generator.txt
    wind_generator.txt
    dust_generator.txt
    storm_generator.txt
    thunder_generator.txt
    clear_generator.txt

✓ Removes any previous weather block
✓ Inserts only one weather block
✓ Safe for repeated execution
✓ Compatible with:

ros2 launch environment_weather_simulator weather.launch.py effect:=rain
"""

from __future__ import annotations

import shutil
import argparse
import sys
from pathlib import Path
from typing import Dict, Optional


class WorldGenerator:
    """
    Generates a temporary Gazebo world by injecting
    weather snippets into ansa_world.sdf.
    """

    WEATHER_BEGIN = "<!-- WEATHER_EFFECT_BEGIN -->"
    WEATHER_END = "<!-- WEATHER_EFFECT_END -->"

    def __init__(
        self,
        world_file: str,
        generator_directory: str,
        output_directory: str,
    ) -> None:

        self.world_file = Path(world_file).expanduser().resolve()

        self.generator_directory = (
            Path(generator_directory)
            .expanduser()
            .resolve()
        )

        self.output_directory = (
            Path(output_directory)
            .expanduser()
            .resolve()
        )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.generated_world = (
            self.output_directory /
            self.world_file.name
        )

        self.weather_files: Dict[str, Path] = {
            "clear":
                self.generator_directory /
                "clear_generator.txt",

            "rain":
                self.generator_directory /
                "rain_generator.txt",

            "fog":
                self.generator_directory /
                "fog_generator.txt",

            "snow":
                self.generator_directory /
                "snow_generator.txt",

            "wind":
                self.generator_directory /
                "wind_generator.txt",

            "dust":
                self.generator_directory /
                "dust_generator.txt",

            "storm":
                self.generator_directory /
                "storm_generator.txt",

            "thunder":
                self.generator_directory /
                "thunder_generator.txt",
        }

    # -------------------------------------------------------------
    # Utility Functions
    # -------------------------------------------------------------

    def validate(self) -> None:
        """
        Ensure required files exist.
        """

        if not self.world_file.exists():
            raise FileNotFoundError(
                f"World file not found:\n{self.world_file}"
            )

        if not self.generator_directory.exists():
            raise FileNotFoundError(
                f"Generator directory missing:\n"
                f"{self.generator_directory}"
            )

        # Individual weather files are validated
        # only when the requested effect is loaded.

    def list_effects(self) -> list[str]:
        return sorted(self.weather_files.keys())

    def generator_path(
        self,
        effect: str,
    ) -> Path:

        effect = effect.lower()

        if effect not in self.weather_files:

            raise ValueError(
                f"Unknown weather effect '{effect}'.\n"
                f"Available: {', '.join(self.list_effects())}"
            )

        return self.weather_files[effect]

    def load_world(self) -> str:
        return self.world_file.read_text(
            encoding="utf-8"
        )

    def save_world(
        self,
        content: str,
    ) -> Path:

        self.generated_world.write_text(
            content,
            encoding="utf-8",
        )

        return self.generated_world

    def load_weather(
        self,
        effect: str,
    ) -> str:

        weather_file = self.generator_path(effect)

        if not weather_file.exists():
            raise FileNotFoundError(
                f"Weather generator not found:\n{weather_file}"
            )

        return weather_file.read_text(
            encoding="utf-8"
        )

    def backup_original(self) -> Path:
        """
        Backup ansa_world.sdf once.
        """

        backup = (
            self.output_directory /
            (self.world_file.stem + "_backup.sdf")
        )

        if not backup.exists():
            shutil.copy2(
                self.world_file,
                backup,
            )

        return backup

    # -------------------------------------------------------------
    # Weather Block Handling
    # -------------------------------------------------------------

    def _weather_wrapper(
        self,
        weather_text: str,
    ) -> str:
        """
        Wrap a weather snippet so it can be safely removed
        on the next execution.
        """

        weather_text = weather_text.strip()

        return (
            "\n"
            f"{self.WEATHER_BEGIN}\n"
            f"{weather_text}\n"
            f"{self.WEATHER_END}\n"
        )

    def remove_previous_weather(
        self,
        world_text: str,
    ) -> str:
        """
        Remove an existing injected weather block if present.

        Safe to call multiple times.
        """

        begin = world_text.find(self.WEATHER_BEGIN)

        if begin == -1:
            return world_text

        end = world_text.find(
            self.WEATHER_END,
            begin,
        )

        if end == -1:
            return world_text

        end += len(self.WEATHER_END)

        while (
            end < len(world_text)
            and world_text[end] in ("\n", "\r")
        ):
            end += 1

        return (
            world_text[:begin]
            + world_text[end:]
        )

    def _find_world_end(
        self,
        world_text: str,
    ) -> int:
        """
        Find the closing </world> tag.

        The weather block is inserted immediately before it.
        """

        marker = "</world>"

        position = world_text.rfind(marker)

        if position == -1:
            raise RuntimeError(
                "Closing </world> tag not found "
                "inside ansa_world.sdf"
            )

        return position

    def insert_weather(
        self,
        world_text: str,
        weather_text: str,
    ) -> str:
        """
        Remove any existing weather block and insert
        the requested weather effect.
        """

        cleaned_world = self.remove_previous_weather(
            world_text
        )

        insert_position = self._find_world_end(
            cleaned_world
        )

        wrapped_weather = self._weather_wrapper(
            weather_text
        )

        return (
            cleaned_world[:insert_position]
            + wrapped_weather
            + cleaned_world[insert_position:]
        )

    def build_world_text(
        self,
        effect: str,
    ) -> str:
        """
        Generate the final world text for a weather effect.
        """

        world_text = self.load_world()

        weather_text = self.load_weather(
            effect
        )

        return self.insert_weather(
            world_text,
            weather_text,
        )

    def world_exists(self) -> bool:
        """
        Check whether the generated world already exists.
        """

        return self.generated_world.exists()

    def remove_generated_world(self) -> None:
        """
        Delete the generated world if present.
        """

        if self.generated_world.exists():
            self.generated_world.unlink()

    # -------------------------------------------------------------
    # World Generation
    # -------------------------------------------------------------

    def generate(
        self,
        effect: str,
    ) -> Path:
        """
        Generate a new world containing the requested
        weather effect.

        Parameters
        ----------
        effect : str
            clear, rain, fog, snow, wind,
            dust, storm, thunder

        Returns
        -------
        Path
            Path to the generated world.
        """

        effect = effect.lower().strip()

        self.validate()

        self.backup_original()

        world_text = self.build_world_text(effect)

        return self.save_world(world_text)

    def regenerate(
        self,
        effect: str,
    ) -> Path:
        """
        Regenerate the world from the original source.

        Existing generated worlds are removed first to
        ensure there are never multiple weather blocks.
        """

        if self.generated_world.exists():
            self.generated_world.unlink()

        return self.generate(effect)

    def switch_effect(
        self,
        effect: str,
    ) -> Path:
        """
        Switch weather effects.

        Equivalent to regenerating the world.
        """

        return self.regenerate(effect)

    def get_generated_world(self) -> Path:
        """
        Return the generated world path.
        """

        return self.generated_world

    def effect_exists(
        self,
        effect: str,
    ) -> bool:
        """
        Check whether a weather effect generator exists.
        """

        return (
            effect.lower().strip()
            in self.weather_files
        )

    def available_effects(self) -> tuple[str, ...]:
        """
        Return all supported weather effects.
        """

        return tuple(
            sorted(self.weather_files.keys())
        )

    def restore_original(self) -> Path:
        """
        Restore the original ansa_world.sdf from the
        backup if one exists.
        """

        backup = (
            self.output_directory
            / (self.world_file.stem + "_backup.sdf")
        )

        if not backup.exists():
            raise FileNotFoundError(
                "Backup world not found."
            )

        shutil.copy2(
            backup,
            self.generated_world,
        )

        return self.generated_world

    def clean(self) -> None:
        """
        Remove generated files created by this module.
        """

        if self.generated_world.exists():
            self.generated_world.unlink()

    def __str__(self) -> str:
        return (
            f"WorldGenerator("
            f"world='{self.world_file}', "
            f"generated='{self.generated_world}')"
        )

    def __repr__(self) -> str:
        return self.__str__()

    # -------------------------------------------------------------
    # Launch-Compatible API
    # -------------------------------------------------------------

    def prepare_world(
        self,
        effect: str = "clear",
    ) -> str:
        """
        Generate the requested weather world and return the
        absolute path to the generated SDF.

        This method is intended to be called from
        weather.launch.py.

        Example:
            generator.prepare_world("rain")
        """

        generated = self.generate(effect)

        return str(generated.resolve())

    def prepare_from_launch_argument(
        self,
        effect: Optional[str],
    ) -> str:
        """
        Accept the launch argument 'effect'.

        Example:
            effect:=rain
            effect:=fog
            effect:=snow

        If the argument is empty or None, 'clear' is used.
        """

        if effect is None:
            effect = "clear"

        effect = str(effect).strip().lower()

        if effect == "":
            effect = "clear"

        if not self.effect_exists(effect):
            raise ValueError(
                f"Unsupported weather effect '{effect}'.\n"
                f"Supported effects: "
                f"{', '.join(self.available_effects())}"
            )

        return self.prepare_world(effect)

    def create_world(
        self,
        effect: str,
    ) -> Path:
        """
        Convenience wrapper.
        """

        return self.generate(effect)

    def update_world(
        self,
        effect: str,
    ) -> Path:
        """
        Replace any existing injected weather block with
        the newly requested effect.
        """

        return self.switch_effect(effect)

    def world_path(self) -> str:
        """
        Absolute path to the generated world.
        """

        return str(self.generated_world.resolve())

    def source_world_path(self) -> str:
        """
        Absolute path to the original ansa_world.sdf.
        """

        return str(self.world_file.resolve())

    def summary(self) -> Dict[str, Any]:
        """
        Useful for debugging or logging.
        """

        return {
            "source_world": self.source_world_path(),
            "generated_world": self.world_path(),
            "generator_directory": str(self.generator_directory),
            "available_effects": list(self.available_effects()),
        }   

# -------------------------------------------------------------
# Command Line Interface
# -------------------------------------------------------------

    


def build_argument_parser() -> argparse.ArgumentParser:
    """
    Create the command-line argument parser.
    """

    parser = argparse.ArgumentParser(
        description="Generate a weather-enabled Gazebo world."
    )

    parser.add_argument(
        "--world",
        required=True,
        help="Path to ansa_world.sdf",
    )

    parser.add_argument(
        "--generators",
        required=True,
        help="Directory containing *_generator.txt files",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Directory where the generated world will be written",
    )

    parser.add_argument(
        "--effect",
        default="clear",
        choices=[
            "clear",
            "rain",
            "fog",
            "snow",
            "wind",
            "dust",
            "storm",
            "thunder",
        ],
        help="Weather effect to inject",
    )

    return parser


def main() -> int:
    """
    CLI entry point.

    Example:

    python3 world_generator.py \
        --world ansa_world.sdf \
        --generators weather_generators \
        --output generated \
        --effect rain
    """

    parser = build_argument_parser()
    args = parser.parse_args()

    try:

        generator = WorldGenerator(
            world_file=args.world,
            generator_directory=args.generators,
            output_directory=args.output,
        )

        generated_world = generator.prepare_from_launch_argument(
            args.effect
        )

        print("=" * 60)
        print("Environment Weather Simulator")
        print("=" * 60)
        print(f"Effect           : {args.effect}")
        print(f"Source World     : {generator.source_world_path()}")
        print(f"Generated World  : {generated_world}")
        print("=" * 60)

        return 0

    except Exception as exc:

        print(
            f"[WorldGenerator] ERROR: {exc}",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())