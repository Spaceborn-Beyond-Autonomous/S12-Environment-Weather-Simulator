"""
S12 -> S04 Navigation Bridge
Feeds live 3D wind vectors, gust magnitude, and turbulence into S04 (GPS-Denied Navigation).
"""

from typing import Tuple, Dict, Any
from environment_weather_simulator.engine import EnvironmentEngine

class NavigationBridge:
    """
    Interfaces EnvironmentEngine with S04 GPS-Denied Navigation system.
    """
    def __init__(self, engine: EnvironmentEngine, drag_coefficient: float = 0.5, cross_section_area: float = 0.1):
        self.engine = engine
        self.cd = drag_coefficient  # Aerodynamic drag coefficient
        self.area = cross_section_area # Frontal area in m^2

    def get_navigation_wind_feed(self, agent_position_xyz: Tuple[float, float, float], timestamp: float) -> Dict[str, Any]:
        """
        Queries wind at agent position and returns wind disturbance payload for S04.
        """
        weather_state = self.engine.sample_at(agent_position_xyz, timestamp=timestamp)
        wind_sample = weather_state.wind

        vx, vy, vz = wind_sample.velocity_vector
        
        # Estimate quadratic drag force perturbation: F_drag = 0.5 * rho * Cd * A * V^2
        air_density = 1.225  # kg/m^3 (ISA sea-level)
        fx = 0.5 * air_density * self.cd * self.area * (vx ** 2) * (1.0 if vx >= 0 else -1.0)
        fy = 0.5 * air_density * self.cd * self.area * (vy ** 2) * (1.0 if vy >= 0 else -1.0)
        fz = 0.5 * air_density * self.cd * self.area * (vz ** 2) * (1.0 if vz >= 0 else -1.0)

        return {
            "timestamp": timestamp,
            "wind_velocity_enu_ms": wind_sample.velocity_vector,
            "gust_magnitude_ms": wind_sample.gust_magnitude,
            "turbulence_intensity": wind_sample.turbulence_intensity,
            "estimated_drag_force_N": (fx, fy, fz)
        }