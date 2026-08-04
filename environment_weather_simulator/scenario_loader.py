"""
scenario_loader.py

Loads and validates environment scenario configuration files.

Owner: Engineer A
"""

import json
import yaml


class ScenarioLoader:
    """Loads and validates simulation scenarios."""

    def __init__(self):
        self._configuration = {}

    def load_yaml(self, file_path: str) -> dict:
        """
        Load a YAML scenario file.
        """

        with open(file_path, "r", encoding="utf-8") as file:
            self._configuration = yaml.safe_load(file)

        self.validate()

        return self._configuration

    def load_json(self, file_path: str) -> dict:
        """
        Load a JSON scenario file.
        """

        with open(file_path, "r", encoding="utf-8") as file:
            self._configuration = json.load(file)

        self.validate()

        return self._configuration

    def validate(self) -> bool:
        """
        Validate loaded scenario configuration.
        """

        if self._configuration is None:
            raise ValueError("Scenario configuration is empty.")

        if not isinstance(self._configuration, dict):
            raise TypeError("Scenario configuration must be a dictionary.")

        return True

    def get_configuration(self) -> dict:
        """
        Return loaded configuration.
        """

        return self._configuration