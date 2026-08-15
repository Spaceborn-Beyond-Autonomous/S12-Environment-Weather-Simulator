"""
S12 Environment Engine - Core Simulation Loop & State Aggregator

Architecture:

ROS2 Drone State
        ↓
EnvironmentEngine
        ↓
 ┌───────────────┬───────────────┬───────────────┐
 ↓               ↓               ↓
WindFieldGrid   SolarModel    ThermalModel    EMIModel
 └───────────────┴───────────────┴───────────────┘
                        ↓
                  WeatherState
                        ↓
                 ROS2 Publisher

This file is responsible for coordinating environmental
models and aggregating their outputs into WeatherState.

ROS2 publishing is intentionally kept outside this file.
"""

import math
from typing import Tuple, Dict, Any, Optional

from environment_weather_simulator.api import (
    WeatherState,
    PrecipitationState,
    WindFieldSample,
    SolarThermalState,
    EMIState,
)

from environment_weather_simulator.wind.wind_field import WindFieldGrid
from environment_weather_simulator.solar_thermal.solar_model import SolarModel
from environment_weather_simulator.solar_thermal.thermal_model import ThermalModel
from environment_weather_simulator.emi.emi_model import EMIModel


class EnvironmentEngine:
    """
    Central environment simulation engine.

    Responsibilities:
        - Maintain simulation time
        - Sample wind
        - Calculate solar irradiance
        - Calculate thermal state
        - Calculate EMI
        - Aggregate all results into WeatherState

    The engine does not publish ROS2 messages directly.
    """

    def __init__(
        self,
        wind_bounds: Tuple[
            float, float, float,
            float, float, float
        ] = (
            -100.0,
            100.0,
            -100.0,
            100.0,
            0.0,
            50.0,
        ),
        wind_resolution: float = 10.0,
        base_wind: Tuple[float, float, float] = (
            5.0,
            2.0,
            0.0,
        ),
        ambient_temperature_c: float = 20.0,
    ):
        # -------------------------------------------------
        # Simulation time
        # -------------------------------------------------

        self.current_time: float = 0.0

        # -------------------------------------------------
        # Environment parameters
        # -------------------------------------------------

        self.ambient_temperature_c = ambient_temperature_c

        # -------------------------------------------------
        # Wind model
        # -------------------------------------------------

        self.wind_grid = WindFieldGrid(
            bounds=wind_bounds,
            resolution=wind_resolution,
            base_wind=base_wind,
            enable_shear=True,
            enable_turbulence=True,
        )

        # -------------------------------------------------
        # Solar model
        # -------------------------------------------------

        self.solar_model = SolarModel()

        # -------------------------------------------------
        # Thermal model
        # -------------------------------------------------

        self.thermal_model = ThermalModel()

        # -------------------------------------------------
        # EMI model
        # -------------------------------------------------

        self.emi_model = EMIModel()

    # =====================================================
    # Utility Functions
    # =====================================================

    @staticmethod
    def _wind_speed(
        velocity: Tuple[float, float, float]
    ) -> float:
        """
        Calculates wind speed from velocity vector.
        """

        vx, vy, vz = velocity

        return math.sqrt(
            vx * vx +
            vy * vy +
            vz * vz
        )

    @staticmethod
    def _time_of_day_hours(timestamp: float) -> float:
        """
        Converts simulation timestamp into a 24-hour clock.

        Simulation starts at 00:00.
        """

        seconds_per_day = 24.0 * 60.0 * 60.0

        seconds = timestamp % seconds_per_day

        return seconds / 3600.0

    @staticmethod
    def _solar_elevation(
        time_of_day_hours: float
    ) -> float:
        """
        Simplified solar elevation model.

        06:00 -> 0 deg
        12:00 -> 90 deg
        18:00 -> 0 deg
        """

        if (
            time_of_day_hours < 6.0
            or time_of_day_hours > 18.0
        ):
            return 0.0

        return 90.0 * math.sin(
            math.pi *
            (time_of_day_hours - 6.0) /
            12.0
        )

    @staticmethod
    def _solar_azimuth(
        time_of_day_hours: float
    ) -> float:
        """
        Simplified solar azimuth model.

        06:00 -> 90 deg
        12:00 -> 180 deg
        18:00 -> 270 deg
        """

        if time_of_day_hours < 6.0:
            return 90.0

        if time_of_day_hours > 18.0:
            return 270.0

        return 90.0 + (
            (time_of_day_hours - 6.0)
            * 15.0
        )

    # =====================================================
    # Main Simulation Step
    # =====================================================

    def step(
        self,
        dt: float
    ) -> WeatherState:
        """
        Advances simulation by dt seconds.

        Returns:
            WeatherState containing wind, solar,
            thermal and EMI information.
        """

        if dt < 0.0:
            raise ValueError(
                "dt cannot be negative"
            )

        self.current_time += dt

        return self.sample_at(
            position_xyz=(0.0, 0.0, 10.0),
            timestamp=self.current_time,
        )

    # =====================================================
    # Spatial Environment Sampling
    # =====================================================

    def sample_at(
        self,
        position_xyz: Tuple[float, float, float],
        timestamp: Optional[float] = None,
    ) -> WeatherState:
        """
        Samples the complete environment at a
        specific 3D position and simulation time.

        Args:
            position_xyz:
                (x, y, z) position of the drone.

            timestamp:
                Simulation timestamp in seconds.

        Returns:
            WeatherState
        """

        x, y, z = position_xyz

        t = (
            self.current_time
            if timestamp is None
            else timestamp
        )

        # -------------------------------------------------
        # 1. WIND
        # -------------------------------------------------

        wind_sample: WindFieldSample = (
            self.wind_grid.sample_at(
                position_xyz,
                timestamp=t,
            )
        )

        wind_speed = self._wind_speed(
            wind_sample.velocity_vector
        )

        # -------------------------------------------------
        # 2. SOLAR
        # -------------------------------------------------

        time_of_day = self._time_of_day_hours(t)

        solar_irradiance = (
            self.solar_model.calculate_irradiance(
                time_of_day_hours=time_of_day,
                cloud_cover_percent=0.0,
            )
        )

        solar_state = SolarThermalState()

        solar_state.solar_azimuth_deg = (
            self._solar_azimuth(time_of_day)
        )

        solar_state.solar_elevation_deg = (
            self._solar_elevation(time_of_day)
        )

        solar_state.glare_intensity = (
            solar_irradiance / 1000.0
        )

        solar_state.ambient_temp_c = (
            self.ambient_temperature_c
        )

        # -------------------------------------------------
        # 3. THERMAL
        # -------------------------------------------------

        surface_temperature = (
            self.thermal_model.calculate_surface_temperature(
                ambient_temp_c=self.ambient_temperature_c,
                solar_irradiance=solar_irradiance,
                wind_speed_m_s=wind_speed,
            )
        )

        solar_state.surface_temp_delta_c = (
            surface_temperature -
            self.ambient_temperature_c
        )

        # -------------------------------------------------
        # 4. EMI
        # -------------------------------------------------

        emi_intensity = (
            self.emi_model.calculate_intensity(
                drone_x=x,
                drone_y=y,
                drone_z=z,
            )
        )

        emi_state = EMIState()

        # Convert calculated intensity into a
        # logarithmic-style dB representation.
        emi_state.interference_db = (
            10.0 *
            math.log10(
                max(emi_intensity, 1e-12)
            )
        )

        emi_state.affected_bands = (
            self._get_affected_bands(
                emi_intensity
            )
        )

        # -------------------------------------------------
        # 5. PRECIPITATION
        # -------------------------------------------------

        precipitation_state = (
            PrecipitationState()
        )

        # Precipitation models can be connected here
        # when their engine interfaces are finalized.

        # -------------------------------------------------
        # 6. AGGREGATE WEATHER STATE
        # -------------------------------------------------

        state = WeatherState()

        state.timestamp = t

        state.precipitation = (
            precipitation_state
        )

        state.wind = wind_sample

        state.solar = solar_state

        state.emi = emi_state

        return state

    # =====================================================
    # EMI Band Classification
    # =====================================================

    @staticmethod
    def _get_affected_bands(
        emi_intensity: float
    ) -> list:
        """
        Determines which sensor frequency bands may
        be affected by the calculated EMI level.

        This is intentionally a simplified model.
        """

        if emi_intensity < 1.0:
            return []

        if emi_intensity < 10.0:
            return ["low_frequency"]

        if emi_intensity < 50.0:
            return [
                "low_frequency",
                "navigation",
            ]

        if emi_intensity < 100.0:
            return [
                "low_frequency",
                "navigation",
                "radio",
            ]

        return [
            "low_frequency",
            "navigation",
            "radio",
            "high_frequency",
        ]

    # =====================================================
    # Wind Grid Interface
    # =====================================================

    def get_wind_grid(
        self,
        bounds: Optional[
            Tuple[
                float, float, float,
                float, float, float
            ]
        ] = None,
        resolution: Optional[float] = None,
    ) -> WindFieldGrid:
        """
        Returns the active WindFieldGrid.

        If bounds and resolution are supplied,
        a new WindFieldGrid is returned.
        """

        if (
            bounds is not None
            and resolution is not None
        ):
            return WindFieldGrid(
                bounds=bounds,
                resolution=resolution,
                base_wind=self.wind_grid.base_wind,
                enable_shear=True,
                enable_turbulence=True,
            )

        return self.wind_grid

    # =====================================================
    # Scenario Interface
    # =====================================================

    def load_scenario(
        self,
        scenario_config: Dict[str, Any]
    ) -> None:
        """
        Loads environment parameters from a
        scenario configuration dictionary.
        """

        if not isinstance(
            scenario_config,
            dict,
        ):
            raise TypeError(
                "scenario_config must be a dictionary"
            )

        # -------------------------------------------------
        # Wind
        # -------------------------------------------------

        if "base_wind" in scenario_config:

            base_wind = tuple(
                scenario_config["base_wind"]
            )

            if len(base_wind) != 3:
                raise ValueError(
                    "base_wind must contain 3 values"
                )

            self.wind_grid.base_wind = (
                base_wind
            )

            self.wind_grid.grid = (
                self.wind_grid._generate_grid()
            )

        # -------------------------------------------------
        # Ambient temperature
        # -------------------------------------------------

        if "ambient_temperature_c" in scenario_config:

            self.ambient_temperature_c = float(
                scenario_config[
                    "ambient_temperature_c"
                ]
            )

        # -------------------------------------------------
        # Solar maximum irradiance
        # -------------------------------------------------

        if "max_irradiance" in scenario_config:

            self.solar_model.max_irradiance = float(
                scenario_config[
                    "max_irradiance"
                ]
            )

    # =====================================================
    # Timeline Interface
    # =====================================================

    def export_timeline(
        self,
        path: str
    ) -> None:
        """
        Placeholder for timeline export.

        Timeline serialization will be implemented
        when the timeline subsystem is connected.
        """

        raise NotImplementedError(
            "Timeline export is not implemented yet."
        )