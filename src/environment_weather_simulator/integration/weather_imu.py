#!/usr/bin/env python3

import copy
import random

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Imu


class WeatherIMU(Node):

    def __init__(self):

        super().__init__("weather_imu")

        self.subscription = self.create_subscription(
            Imu,
            "/imu/data",
            self.imu_callback,
            10)

        self.publisher = self.create_publisher(
            Imu,
            "/imu/weather",
            10)

        ##################################################
        # Enable / Disable Weather
        ##################################################

        self.enable_rain = True
        self.enable_fog = False
        self.enable_snow = False

        ##################################################
        # Noise Parameters
        ##################################################

        # Standard deviation of Gaussian noise

        self.rain_accel_noise = 0.15
        self.rain_gyro_noise = 0.05

        self.fog_accel_noise = 0.03
        self.fog_gyro_noise = 0.01

        self.snow_accel_noise = 0.30
        self.snow_gyro_noise = 0.10

        self.get_logger().info("Weather IMU Node Started")

    ##################################################

    def add_noise(self, imu_msg, accel_std, gyro_std):

        imu = copy.deepcopy(imu_msg)

        # Linear acceleration

        imu.linear_acceleration.x += random.gauss(0, accel_std)
        imu.linear_acceleration.y += random.gauss(0, accel_std)
        imu.linear_acceleration.z += random.gauss(0, accel_std)

        # Angular velocity

        imu.angular_velocity.x += random.gauss(0, gyro_std)
        imu.angular_velocity.y += random.gauss(0, gyro_std)
        imu.angular_velocity.z += random.gauss(0, gyro_std)

        return imu

    ##################################################

    def imu_callback(self, msg):

        output = copy.deepcopy(msg)

        if self.enable_rain:

            output = self.add_noise(
                output,
                self.rain_accel_noise,
                self.rain_gyro_noise)

        if self.enable_fog:

            output = self.add_noise(
                output,
                self.fog_accel_noise,
                self.fog_gyro_noise)

        if self.enable_snow:

            output = self.add_noise(
                output,
                self.snow_accel_noise,
                self.snow_gyro_noise)

        self.publisher.publish(output)


def main():

    rclpy.init()

    node = WeatherIMU()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()