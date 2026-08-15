class ThermalModel:
    """
    Thermal model for the drone/equipment.

    Calculates surface temperature using:
        - Ambient temperature
        - Solar irradiance
        - Wind speed

    Also calculates thermal noise/degradation for sensors.

    Data flow:

        api.py
            ↓
        thermal_model.py
            ↓
        engine.py
            ↓
        ROS2 publisher
    """

    def __init__(
        self,
        specific_heat_factor: float = 0.015,
        wind_cooling_factor: float = 0.5,
    ):
        """
        Initialize the thermal model.

        Args:
            specific_heat_factor:
                Conversion factor from solar irradiance
                (W/m²) to surface temperature increase.

            wind_cooling_factor:
                Cooling factor caused by wind speed.
        """

        self.specific_heat_factor = float(
            specific_heat_factor
        )

        self.wind_cooling_factor = float(
            wind_cooling_factor
        )

    def calculate_surface_temperature(
        self,
        ambient_temp_c: float,
        solar_irradiance: float,
        wind_speed_m_s: float,
    ) -> float:
        """
        Calculate effective surface temperature.

        The simplified thermal equation is:

            T_surface =
                T_ambient
                + solar_heating
                - wind_cooling

        Args:
            ambient_temp_c:
                Ambient air temperature in Celsius.

            solar_irradiance:
                Solar irradiance in W/m².

            wind_speed_m_s:
                Wind speed in m/s.

        Returns:
            Surface temperature in Celsius.
        """

        # Prevent physically invalid negative inputs.
        solar_irradiance = max(
            0.0,
            solar_irradiance,
        )

        wind_speed_m_s = max(
            0.0,
            wind_speed_m_s,
        )

        # Heating caused by solar radiation.
        solar_heating = (
            solar_irradiance
            * self.specific_heat_factor
        )

        # Cooling caused by wind.
        convective_cooling = (
            wind_speed_m_s
            * self.wind_cooling_factor
        )

        # Calculate surface temperature.
        surface_temp = (
            ambient_temp_c
            + solar_heating
            - convective_cooling
        )

        # In this simplified model, wind cannot reduce
        # surface temperature below ambient temperature.
        return max(
            surface_temp,
            ambient_temp_c,
        )

    def calculate_camera_thermal_noise(
        self,
        surface_temp_c: float,
        threshold_temp: float = 40.0,
    ) -> float:
        """
        Calculate thermal noise/degradation for sensors.

        Thermal noise starts when the surface temperature
        exceeds the operational threshold.

        Args:
            surface_temp_c:
                Current surface temperature in Celsius.

            threshold_temp:
                Temperature at which thermal degradation begins.

        Returns:
            Noise multiplier:

                0.0 = no degradation
                1.0 = maximum degradation
        """

        # No thermal degradation below the threshold.
        if surface_temp_c <= threshold_temp:
            return 0.0

        # Temperature above the operational threshold.
        excess_heat = (
            surface_temp_c
            - threshold_temp
        )

        # Convert excess temperature into
        # a normalized noise multiplier.
        noise_multiplier = (
            excess_heat * 0.05
        )

        # Limit degradation to 100%.
        return min(
            max(noise_multiplier, 0.0),
            1.0,
        )

