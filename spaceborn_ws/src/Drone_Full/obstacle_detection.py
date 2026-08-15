#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Float32


class PointCloudDistanceChecker(Node):

    def __init__(self):
        super().__init__('pointcloud_distance_checker')

        # Subscriber
        self.subscription = self.create_subscription(
            PointCloud2,
            '/points',
            self.pointcloud_callback,
            10
        )

        # Publisher
        self.publisher = self.create_publisher(
            Float32,
            '/obstacles/detected',
            10
        )

        self.threshold_distance = 2.0  # meters
        self.minimum_valid_distance = 0.25 # meters

        self.get_logger().info(
            f'Checking for obstacles between '
            f'{self.minimum_valid_distance} m and '
            f'{self.threshold_distance} m'
        )

    def pointcloud_callback(self, msg):

        min_distance = float('inf')

        # Read every point in the point cloud
        for point in point_cloud2.read_points(
            msg,
            field_names=("x", "y", "z"),
            skip_nans=True
        ):

            x, y, z = point

            distance = math.sqrt(x**2 + y**2 + z**2)

            # Find the closest point within the detection range
            if self.minimum_valid_distance < distance <= self.threshold_distance:
                if distance < min_distance:
                    min_distance = distance

        # Publish only if an obstacle exists
        if min_distance != float('inf'):

            obstacle_msg = Float32()
            obstacle_msg.data = float(min_distance)

            self.publisher.publish(obstacle_msg)

            self.get_logger().warn(
                f'Obstacle detected! Distance: {min_distance:.2f} m'
            )

        else:
            self.get_logger().info(
                'No obstacle detected within 2.0 m'
            )


def main(args=None):

    rclpy.init(args=args)

    node = PointCloudDistanceChecker()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
