import math


class SolarModel:
    """
    Solar irradiance model.

    This class is responsible only for calculating solar irradiance.
    ROS2 communication is handled by the environment engine.

    Data flow:

        api.py
            ↓
        solar_model.py
            ↓
        engine.py
            ↓
        ROS2 publisher
    """

    def __init__(
        self,
        max_irradiance: float = 1000.0,
    ):
        """
        Initialize the solar model.

        Args:
            max_irradiance:
                Maximum clear-sky solar irradiance in W/m².
        """

        self.max_irradiance = float(max_irradiance)

    def calculate_irradiance(
        self,
        time_of_day_hours: float,
        cloud_cover_percent: float = 0.0,
    ) -> float:
        """
        Calculate solar irradiance for a given time of day.

        The simplified model assumes:

            06:00 → sunrise
            12:00 → maximum irradiance
            18:00 → sunset

        Irradiance follows a sine-wave profile during daylight.

        Args:
            time_of_day_hours:
                Time of day in hours.
                Valid range: 0.0 to 24.0.

            cloud_cover_percent:
                Cloud-cover factor.

                Expected range:
                    0.0 = clear sky
                    1.0 = completely overcast

        Returns:
            Solar irradiance in W/m².
        """

        # Keep time inside a valid 24-hour range.
        time_of_day_hours = time_of_day_hours % 24.0

        # Clamp cloud cover between 0 and 1.
        cloud_cover_percent = max(
            0.0,
            min(1.0, cloud_cover_percent),
        )

        # No solar irradiance during night.
        if (
            time_of_day_hours < 6.0
            or time_of_day_hours > 18.0
        ):
            return 0.0

        # Convert daylight period (06:00–18:00)
        # into a sine-wave angle from 0 to π.
        sun_angle = math.pi * (
            time_of_day_hours - 6.0
        ) / 12.0

        sun_angle_factor = math.sin(sun_angle)

        # Prevent tiny negative floating-point values.
        sun_angle_factor = max(
            0.0,
            sun_angle_factor,
        )

        # Cloud attenuation.
        #
        # Clear sky:
        #     cloud_cover = 0.0
        #     attenuation = 1.0
        #
        # Heavy cloud:
        #     cloud_cover = 1.0
        #     attenuation = 0.2
        #
        # Therefore maximum cloud attenuation is 80%.
        cloud_attenuation = 1.0 - (
            cloud_cover_percent * 0.8
        )

        irradiance = (
            self.max_irradiance
            * sun_angle_factor
            * cloud_attenuation
        )

        return max(0.0, irradiance)

