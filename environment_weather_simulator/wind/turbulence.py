import math
import random
from typing import Tuple

class TurbulenceModel:
    """
    Implements a discrete 3D Dryden-spectrum continuous turbulence model.
    Produces energy-conserving zero-mean stochastic velocity perturbations.
    """
    def __init__(self, intensity_scale: float = 0.1, seed: int = 42):
        """
        intensity_scale: Multiplier for turbulence magnitude (0.0 = calm, 1.0 = heavy).
        seed: Random seed for deterministic reproducibility in unit tests.
        """
        self.intensity_scale = intensity_scale
        self.u_turb = 0.0
        self.v_turb = 0.0
        self.w_turb = 0.0
        random.seed(seed)

    def _get_scale_lengths_and_sigmas(self, altitude_z: float, mean_speed: float) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """Computes altitude-dependent Dryden scale lengths and sigmas."""
        z = max(altitude_z, 1.0)
        
        # Scale lengths (meters)
        L_w = z
        denom = math.pow(0.177 + 0.000823 * z, 1.2)
        L_u = z / denom
        L_v = L_u

        # Sigmas (m/s)
        sigma_w = 0.1 * mean_speed * self.intensity_scale
        denom_sigma = math.pow(0.177 + 0.000823 * z, 0.4)
        sigma_u = sigma_w / max(denom_sigma, 1e-3)
        sigma_v = sigma_u

        return (L_u, L_v, L_w), (sigma_u, sigma_v, sigma_w)

    def step(self, dt: float, mean_speed: float, altitude_z: float) -> Tuple[float, float, float]:
        """
        Advances the stochastic turbulence state by time dt.
        returns: (u_turb, v_turb, w_turb) velocity perturbations in m/s.
        """
        if dt <= 0.0 or self.intensity_scale <= 0.0:
            return (0.0, 0.0, 0.0)

        V = max(mean_speed, 1.0)  # Avoid division by zero
        (L_u, L_v, L_w), (sigma_u, sigma_v, sigma_w) = self._get_scale_lengths_and_sigmas(altitude_z, V)

        # Time constants tau = L / V
        tau_u = L_u / V
        tau_v = L_v / V
        tau_w = L_w / V

        # AR(1) Energy-conserving discrete updates
        for state, tau, sigma, axis in [
            (self.u_turb, tau_u, sigma_u, 'u'),
            (self.v_turb, tau_v, sigma_v, 'v'),
            (self.w_turb, tau_w, sigma_w, 'w')
        ]:
            alpha = math.exp(-dt / tau)
            noise_scale = sigma * math.sqrt(max(0.0, 1.0 - math.exp(-2.0 * dt / tau)))
            new_val = state * alpha + noise_scale * random.gauss(0.0, 1.0)

            if axis == 'u':
                self.u_turb = new_val
            elif axis == 'v':
                self.v_turb = new_val
            else:
                self.w_turb = new_val

        return (self.u_turb, self.v_turb, self.w_turb)

    def get_turbulence_intensity(self, mean_speed: float) -> float:
        """Returns dimensionless turbulence intensity ratio (std_dev / mean_speed)."""
        if mean_speed <= 0.0:
            return 0.0
        total_turb_mag = math.sqrt(self.u_turb**2 + self.v_turb**2 + self.w_turb**2)
        return total_turb_mag / mean_speed