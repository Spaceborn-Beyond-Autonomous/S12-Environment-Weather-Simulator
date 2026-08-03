#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import cv2
import numpy as np
import random


class RainCamera(Node):

    def __init__(self):

        super().__init__("rain_camera")

        self.bridge = CvBridge()

        self.subscription = self.create_subscription(
            Image,
            "/camera/image_raw",
            self.image_callback,
            10)

        self.publisher = self.create_publisher(
            Image,
            "/camera/weather",
            10)

        ###########################################################
        # Enable / Disable Effects
        ###########################################################

        self.enable_rain = True
        self.enable_fog = False
        self.enable_blur = False
        self.enable_brightness = False
        self.enable_contrast = False

        ###########################################################
        # Weather Parameters
        ###########################################################

        self.rain_intensity = 0.6
        self.fog_intensity = 0.35
        self.blur_strength = 5

        self.get_logger().info("Rain Camera Node Started")

    ###########################################################

    def add_rain(self, image):

        output = image.copy()

        h, w = output.shape[:2]

        number_of_drops = int(600 * self.rain_intensity)

        for _ in range(number_of_drops):

            x = random.randint(0, w - 1)
            y = random.randint(0, h - 1)

            length = random.randint(8, 18)

            cv2.line(
                output,
                (x, y),
                (min(x + 2, w - 1), min(y + length, h - 1)),
                (220, 220, 220),
                1)

        return output

    ###########################################################

    def add_fog(self, image):

        fog = np.full(image.shape, 255, dtype=np.uint8)

        alpha = self.fog_intensity

        return cv2.addWeighted(
            image,
            1 - alpha,
            fog,
            alpha,
            0)

    ###########################################################

    def reduce_brightness(self, image):

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        hsv[:, :, 2] = (hsv[:, :, 2] * 0.75).astype(np.uint8)

        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    ###########################################################

    def blur_image(self, image):

        return cv2.GaussianBlur(
            image,
            (self.blur_strength,
             self.blur_strength),
            0)

    ###########################################################

    def reduce_contrast(self, image):

        alpha = 0.75
        beta = -10

        return cv2.convertScaleAbs(
            image,
            alpha=alpha,
            beta=beta)

    ###########################################################

    def image_callback(self, msg):

        frame = self.bridge.imgmsg_to_cv2(
            msg,
            desired_encoding="bgr8")

        ###########################################################
        # Apply enabled effects
        ###########################################################

        if self.enable_rain:
            frame = self.add_rain(frame)

        if self.enable_fog:
            frame = self.add_fog(frame)

        if self.enable_blur:
            frame = self.blur_image(frame)

        if self.enable_brightness:
            frame = self.reduce_brightness(frame)

        if self.enable_contrast:
            frame = self.reduce_contrast(frame)

        ###########################################################

        output = self.bridge.cv2_to_imgmsg(
            frame,
            encoding="bgr8")

        output.header = msg.header

        self.publisher.publish(output)


def main():

    rclpy.init()

    node = RainCamera()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()