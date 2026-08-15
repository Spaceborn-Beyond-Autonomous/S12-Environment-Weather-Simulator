import math
import random


class EMIModel:
    """
    Electromagnetic Interference (EMI) model.

    This class performs only EMI calculations.
    It does not contain ROS2 publisher/subscriber logic.

    Data flow:
        api.py
            ↓
        emi_model.py
            ↓
        engine.py
            ↓
        ROS2 publisher
    """

    def __init__(
        self,
        tower_x: float = 5.0,
        tower_y: float = 5.0,
        tower_z: float = 4.0,
        base_intensity: float = 100.0,
    ):
        """
        Initialize the EMI source.

        Args:
            tower_x: EMI source X position in meters.
            tower_y: EMI source Y position in meters.
            tower_z: EMI source Z position in meters.
            base_intensity: Reference EMI intensity.
        """

        self.tower_position = (
            float(tower_x),
            float(tower_y),
            float(tower_z),
        )

        self.base_intensity = float(base_intensity)

    def calculate_intensity(
        self,
        drone_x: float,
        drone_y: float,
        drone_z: float,
    ) -> float:
        """
        Calculate EMI intensity at the drone position.

        Uses an inverse-square relationship:

            I = I0 / d²

        Args:
            drone_x: Drone X position in meters.
            drone_y: Drone Y position in meters.
            drone_z: Drone Z position in meters.

        Returns:
            EMI field intensity.
        """

        dx = drone_x - self.tower_position[0]
        dy = drone_y - self.tower_position[1]
        dz = drone_z - self.tower_position[2]

        distance = math.sqrt(
            dx**2 +
            dy**2 +
            dz**2
        )

        # Prevent division by zero / extremely large intensity.
        distance = max(distance, 0.5)

        intensity = self.base_intensity / (distance**2)

        return intensity

    def inject_magnetometer_noise(
        self,
        original_mag_value: float,
        emi_intensity: float,
    ) -> float:
        """
        Add EMI-dependent Gaussian noise to a magnetometer value.

        Args:
            original_mag_value: Original sensor reading.
            emi_intensity: EMI intensity at the drone.

        Returns:
            Magnetometer reading affected by EMI.
        """

        noise_std_dev = max(0.0, emi_intensity) * 0.15

        noise = random.gauss(
            0.0,
            noise_std_dev,
        )

        return original_mag_value + noise

    def inject_gps_covariance_noise(
        self,
        base_covariance: float,
        emi_intensity: float,
    ) -> float:
        """
        Increase GPS covariance according to EMI intensity.

        Higher EMI produces higher covariance and therefore
        represents reduced GPS reliability.

        Args:
            base_covariance: Original GPS covariance.
            emi_intensity: EMI intensity at the drone.

        Returns:
            EMI-affected GPS covariance.
        """

        return (
            base_covariance +
            max(0.0, emi_intensity) * 0.5
        )

