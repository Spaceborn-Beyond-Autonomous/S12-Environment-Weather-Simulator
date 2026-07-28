"""
timeline.py

Stores simulation history.

Owner: Engineer A
"""

import json


class Timeline:
    """Stores WeatherState history."""

    def __init__(self):
        self._history = []

    def add(self, weather_state):
        """
        Add a WeatherState to the timeline.
        """
        self._history.append(weather_state)

    def get_history(self):
        """
        Return the complete simulation history.
        """
        return self._history

    def clear(self):
        """
        Clear all stored history.
        """
        self._history.clear()

    def export(self, file_path: str):
        """
        Export timeline to a JSON file.
        """

        export_data = []

        for state in self._history:
            export_data.append(state.__dict__)

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(export_data, file, indent=4)