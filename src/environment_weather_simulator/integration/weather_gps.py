#!/usr/bin/env python3

import copy
import random

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import NavSatFix


class WeatherGPS(Node):

    def __init__(self):

        super().__init__("weather_gps")

        self.subscription = self.create_subscription(
            NavSatFix,
            "/gps/fix",
            self.gps_callback,
            10)

        self.publisher = self.create_publisher(
            NavSatFix,
            "/gps/weather",
            10)

        ##################################################
        # Enable / Disable Weather
        ##################################################

        self.enable_rain = True
        self.enable_fog = False
        self.enable_snow = False

        ##################################################
        # GPS Noise Parameters
        ##################################################

        # Standard deviation

        self.rain_latlon_noise = 0.000003
        self.rain_alt_noise = 0.30

        self.fog_latlon_noise = 0.000001
        self.fog_alt_noise = 0.10

        self.snow_latlon_noise = 0.000008
        self.snow_alt_noise = 0.80

        self.get_logger().info("Weather GPS Node Started")

    ##################################################

    def add_noise(self, gps_msg, latlon_std, alt_std):

        gps = copy.deepcopy(gps_msg)

        gps.latitude += random.gauss(0, latlon_std)
        gps.longitude += random.gauss(0, latlon_std)
        gps.altitude += random.gauss(0, alt_std)

        return gps

    ##################################################

    def gps_callback(self, msg):

        output = copy.deepcopy(msg)

        if self.enable_rain:

            output = self.add_noise(
                output,
                self.rain_latlon_noise,
                self.rain_alt_noise)

        if self.enable_fog:

            output = self.add_noise(
                output,
                self.fog_latlon_noise,
                self.fog_alt_noise)

        if self.enable_snow:

            output = self.add_noise(
                output,
                self.snow_latlon_noise,
                self.snow_alt_noise)

        self.publisher.publish(output)


def main():

    rclpy.init()

    node = WeatherGPS()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()