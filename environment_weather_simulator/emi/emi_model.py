import math
import random

class EMIModel:
    """
    Simulates Electromagnetic Interference (EMI) based on the inverse-square law.
    Calculates field intensity and injects corresponding noise into sensor readings.
    """
    def __init__(self, tower_x: float = 5.0, tower_y: float = 5.0, tower_z: float = 4.0, base_intensity: float = 100.0):
        self.tower_pos = (tower_x, tower_y, tower_z)
        self.base_intensity = base_intensity

    def calculate_intensity(self, drone_x: float, drone_y: float, drone_z: float) -> float:
        """
        Calculates the EMI field strength at the drone's current location.
        """
        dx = drone_x - self.tower_pos[0]
        dy = drone_y - self.tower_pos[1]
        dz = drone_z - self.tower_pos[2]
        
        # Calculate Euclidean distance
        distance = math.sqrt(dx**2 + dy**2 + dz**2)
        
        # Prevent division by zero if drone crashes directly into the tower core
        distance = max(distance, 0.5) 
        
        # Inverse square law: I = I_0 / d^2
        return self.base_intensity / (distance ** 2)

    def inject_magnetometer_noise(self, original_mag_value: float, emi_intensity: float) -> float:
        """
        Injects Gaussian noise into a magnetometer reading based on EMI intensity.
        """
        # Noise standard deviation scales with EMI intensity
        noise_std_dev = emi_intensity * 0.15 
        noise = random.gauss(0.0, noise_std_dev)
        return original_mag_value + noise
        
    def inject_gps_covariance_noise(self, base_covariance: float, emi_intensity: float) -> float:
        """
        Degrades GPS signal reliability (increases covariance) under high EMI.
        """
        # Exponential degradation of signal lock near high EMI
        return base_covariance + (emi_intensity * 0.5)