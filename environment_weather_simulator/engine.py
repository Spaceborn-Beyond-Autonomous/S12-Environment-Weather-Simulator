"""
S12 Environment Engine - Core Simulation Loop & State Aggregator
Owned by Eng A (Chetan), integrated with Eng C (Hemant) Wind Modules.
"""

from typing import Tuple, Dict, Any
from environment_weather_simulator.api import (
    WeatherState,
    PrecipitationState,
    WindFieldSample,
    SolarThermalState,
    EMIState
)

from environment_weather_simulator.wind.wind_field import WindFieldGrid

class EnvironmentEngine:
    """
    Central environment state engine driving simulation ticks and spatial sampling.
    """
    def __init__(
        self,
        wind_bounds: Tuple[float, float, float, float, float, float] = (-100.0, 100.0, -100.0, 100.0, 0.0, 50.0),
        wind_resolution: float = 10.0,
        base_wind: Tuple[float, float, float] = (5.0, 2.0, 0.0)
    ):
        self.current_time: float = 0.0
        
        # Instantiate Eng C's Wind Field Grid
        self.wind_grid = WindFieldGrid(
            bounds=wind_bounds,
            resolution=wind_resolution,
            base_wind=base_wind,
            enable_shear=True,
            enable_turbulence=True
        )

    def step(self, dt: float) -> WeatherState:
        """
        Advances the environment simulation by dt seconds and returns the updated WeatherState.
        """
        self.current_time += dt
        
        # Sample wind at default origin (0, 0, 10m) for master tick state
        wind_sample = self.wind_grid.sample_at((0.0, 0.0, 10.0), timestamp=self.current_time)

        state = WeatherState()
        state.timestamp = self.current_time
        state.precipitation = PrecipitationState()
        state.wind = wind_sample
        state.solar = SolarThermalState()
        state.emi = EMIState()

        return state

    def sample_at(self, position_xyz: Tuple[float, float, float], timestamp: float = None) -> WeatherState:
        """
        Returns full environmental weather state sampled at an arbitrary 3D position and time.
        """
        t = timestamp if timestamp is not None else self.current_time
        wind_sample = self.wind_grid.sample_at(position_xyz, timestamp=t)

        state = WeatherState()
        state.timestamp = t
        state.precipitation = PrecipitationState()
        state.wind = wind_sample
        state.solar = SolarThermalState()
        state.emi = EMIState()

        return state

        return state

    def get_wind_grid(self, bounds: Tuple[float, float, float, float, float, float] = None, resolution: float = None) -> WindFieldGrid:
        """
        Returns the active WindFieldGrid instance for spatial wind queries.
        """
        if bounds is not None and resolution is not None:
            return WindFieldGrid(bounds=bounds, resolution=resolution, base_wind=self.wind_grid.base_wind)
        return self.wind_grid

    def load_scenario(self, scenario_config: Dict[str, Any]) -> None:
        """Loads environment parameters from configuration dictionaries."""
        if "base_wind" in scenario_config:
            self.wind_grid.base_wind = tuple(scenario_config["base_wind"])
            self.wind_grid.grid = self.wind_grid._generate_grid()
