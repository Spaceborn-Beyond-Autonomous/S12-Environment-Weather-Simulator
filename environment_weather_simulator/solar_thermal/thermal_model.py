class ThermalModel:
    """
    Calculates object surface temperatures based on ambient weather, solar heating, and wind cooling.
    """
    def __init__(self, specific_heat_factor: float = 0.015, wind_cooling_factor: float = 0.5):
        # How easily the object absorbs heat from the sun
        self.specific_heat_factor = specific_heat_factor
        # How rapidly convective wind cools the object down
        self.wind_cooling_factor = wind_cooling_factor

    def calculate_surface_temperature(self, ambient_temp_c: float, solar_irradiance: float, wind_speed_m_s: float) -> float:
        """
        Calculates the effective surface temperature of the drone/equipment.
        """
        # Heat gained from direct sunlight (W/m^2 converted to temperature delta)
        solar_heating = solar_irradiance * self.specific_heat_factor
        
        # Heat lost due to convective wind cooling
        convective_cooling = wind_speed_m_s * self.wind_cooling_factor
        
        # Base thermal equation
        surface_temp = ambient_temp_c + solar_heating - convective_cooling
        
        # The wind cannot cool the object below the ambient air temperature
        return max(surface_temp, ambient_temp_c)

    def calculate_camera_thermal_noise(self, surface_temp_c: float, threshold_temp: float = 40.0) -> float:
        """
        Simulates thermal noise on optical/infrared sensors if the equipment gets too hot.
        Returns a noise multiplier (0.0 means no noise).
        """
        if surface_temp_c <= threshold_temp:
            return 0.0
            
        # Noise scales linearly for every degree above the operational threshold
        excess_heat = surface_temp_c - threshold_temp
        return min(excess_heat * 0.05, 1.0) # Cap noise at 1.0 (100% degradation)