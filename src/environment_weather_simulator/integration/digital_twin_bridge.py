#!/usr/bin/env python3

"""
digital_twin_bridge.py

Bridge between Environment Engine and external Digital Twin systems.

Owner : Engineer A
"""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class DigitalTwinBridge(Node):

    def __init__(self):

        super().__init__("digital_twin_bridge")

        self.publisher = self.create_publisher(
            String,
            "/environment/weather_state",
            10
        )

        self.get_logger().info(
            "Digital Twin Bridge started."
        )

    def convert_weather_state(self, weather_state):

        data = {

            "timestamp": weather_state.timestamp,

            "rain_mm_hr":
                weather_state.precipitation.rain_mm_hr,

            "snow_mm_hr":
                weather_state.precipitation.snow_mm_hr,

            "fog_density":
                weather_state.precipitation.fog_density,

            "dust_density":
                weather_state.precipitation.dust_density,

            "visibility_m":
                weather_state.precipitation.visibility_m,

            "wind_velocity":
                weather_state.wind.velocity_vector,

            "gust":
                weather_state.wind.gust_magnitude,

            "shear":
                weather_state.wind.shear_gradient,

            "turbulence":
                weather_state.wind.turbulence_intensity,

            "solar_azimuth":
                weather_state.solar.solar_azimuth_deg,

            "solar_elevation":
                weather_state.solar.solar_elevation_deg,

            "ambient_temperature":
                weather_state.solar.ambient_temp_c,

            "surface_temperature_delta":
                weather_state.solar.surface_temp_delta_c,

            "emi_db":
                weather_state.emi.interference_db,

            "affected_bands":
                weather_state.emi.affected_bands
        }

        return json.dumps(data)

    def publish_weather(self, weather_state):

        msg = String()

        msg.data = self.convert_weather_state(
            weather_state
        )

        self.publisher.publish(msg)

    def shutdown(self):

        self.get_logger().info(
            "Digital Twin Bridge stopped."
        )