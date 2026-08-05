import math

class SolarModel:
    """
    Simulates Solar Irradiance based on time of day and cloud attenuation.
    """
    def __init__(self, max_irradiance: float = 1000.0):
        # Maximum clear-sky solar irradiance (Watts per square meter)
        self.max_irradiance = max_irradiance

    def calculate_irradiance(self, time_of_day_hours: float, cloud_cover_percent: float = 0.0) -> float:
        """
        Calculates current solar irradiance.
        :param time_of_day_hours: Float from 0.0 to 24.0 (e.g., 14.5 = 2:30 PM)
        :param cloud_cover_percent: Float from 0.0 (clear) to 1.0 (overcast)
        """
        # Assume daylight is exactly between 06:00 and 18:00 for a simplified model
        if time_of_day_hours < 6.0 or time_of_day_hours > 18.0:
            return 0.0  # Night time, zero solar irradiance
        
        # Map 06:00 - 18:00 to a sine wave (0 to Pi) where peak is at 12:00
        # math.sin(pi/2) = 1.0 (Max sun at noon)
        sun_angle_factor = math.sin(math.pi * (time_of_day_hours - 6.0) / 12.0)
        
        # Cloud cover reduces irradiance (up to an 80% reduction in heavy overcast)
        cloud_attenuation = 1.0 - (cloud_cover_percent * 0.8)
        
        return self.max_irradiance * sun_angle_factor * cloud_attenuation