"""
api.py

Frozen Interface Contract
Environment & Weather Simulator

Owner: Engineer A
"""

from typing import Dict, List, Tuple


class PrecipitationState:
    """Rain, snow, fog and dust information."""

    def __init__(self):
        self.rain_mm_hr: float = 0.0
        self.snow_mm_hr: float = 0.0
        self.fog_density: float = 0.0
        self.dust_density: float = 0.0
        self.visibility_m: float = 0.0
        self.attenuation_coeff: Dict[str, float] = {}


class WindFieldSample:
    """Wind information at a single location."""

    def __init__(self):
        self.velocity_vector: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.gust_magnitude: float = 0.0
        self.shear_gradient: float = 0.0
        self.turbulence_intensity: float = 0.0


class SolarThermalState:
    """Solar and thermal information."""

    def __init__(self):
        self.solar_azimuth_deg: float = 0.0
        self.solar_elevation_deg: float = 0.0
        self.glare_intensity: float = 0.0
        self.ambient_temp_c: float = 0.0
        self.surface_temp_delta_c: float = 0.0


class EMIState:
    """Electromagnetic interference information."""

    def __init__(self):
        self.interference_db: float = 0.0
        self.affected_bands: List[str] = []


class WeatherState:
    """Single frame of environmental conditions."""

    def __init__(self):
        self.timestamp: float = 0.0
        self.precipitation = PrecipitationState()
        self.wind = WindFieldSample()
        self.solar = SolarThermalState()
        self.emi = EMIState()


class EnvironmentEngine:
    """Main Environment Engine Interface."""

    def step(self, dt: float) -> WeatherState:
        raise NotImplementedError

    def sample_at(self, position_xyz, timestamp) -> WeatherState:
        raise NotImplementedError

    def get_wind_grid(self, bounds, resolution):
        raise NotImplementedError

    def load_scenario(self, scenario_config: dict) -> None:
        raise NotImplementedError

    def export_timeline(self, path: str) -> None:
        raise NotImplementedError