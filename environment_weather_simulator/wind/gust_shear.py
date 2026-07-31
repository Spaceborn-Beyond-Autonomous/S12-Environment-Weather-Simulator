import math

class GustShearModel:
    """
    Computes altitude-dependent wind shear gradients and discrete temporal wind gusts.
    """
    def __init__(
        self,
        reference_speed: float = 5.0,
        reference_height: float = 10.0,
        alpha: float = 0.143,
        z0: float = 0.1
    ):
        """
        reference_speed: Speed (m/s) at reference_height.
        reference_height: Height (m) where reference_speed is measured (typically 10m).
        alpha: Power-law shear exponent (0.143 for open ground, 0.25 for urban).
        z0: Minimum ground roughness height cutoff (m).
        """
        self.ref_speed = reference_speed
        self.ref_height = reference_height
        self.alpha = alpha
        self.z0 = z0

    def get_shear_velocity(self, altitude_z: float) -> float:
        """
        Computes the wind magnitude at altitude_z using the Power Law shear model.
        """
        z = max(altitude_z, self.z0)
        return self.ref_speed * math.pow(z / self.ref_height, self.alpha)

    def get_shear_gradient(self, altitude_z: float) -> float:
        """
        Computes the spatial derivative dv/dz at altitude_z (1/s).
        """
        z = max(altitude_z, self.z0)
        return (self.alpha * self.ref_speed / self.ref_height) * math.pow(z / self.ref_height, self.alpha - 1.0)

    def get_gust_magnitude(
        self,
        timestamp: float,
        gust_start: float = 5.0,
        gust_duration: float = 3.0,
        peak_magnitude: float = 8.0
    ) -> float:
        """
        Computes a discrete 1-Minus-Cosine gust pulse.
        returns: Extra wind magnitude delta (m/s).
        """
        if gust_start <= timestamp <= (gust_start + gust_duration):
            t_rel = timestamp - gust_start
            return (peak_magnitude / 2.0) * (1.0 - math.cos(2.0 * math.pi * t_rel / gust_duration))
        return 0.0