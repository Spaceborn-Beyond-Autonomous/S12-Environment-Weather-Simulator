#!/usr/bin/env python3
"""
wind_simulation_node.py
Bridges environment_weather_simulator/wind into ROS 2 & Gazebo physics.
"""

import math
import rclpy
from rclpy.node import Node

from nav_msgs.msg import Odometry
from geometry_msgs.msg import Vector3, Wrench

# Relative import targeting your package structure
from environment_weather_simulator.wind.wind_field import WindFieldGrid


class WindSimulationNode(Node):
    def __init__(self):
        super().__init__('wind_simulation_node')

        # Parameters
        self.declare_parameter('enable_shear', True)
        self.declare_parameter('enable_turbulence', True)
        self.declare_parameter('base_wind_x', 5.0)
        self.declare_parameter('base_wind_y', 2.0)
        self.declare_parameter('base_wind_z', 0.0)
        self.declare_parameter('drone_drag_coeff', 0.47)
        self.declare_parameter('drone_cross_section_m2', 0.15)

        enable_shear = self.get_parameter('enable_shear').value
        enable_turbulence = self.get_parameter('enable_turbulence').value
        base_x = self.get_parameter('base_wind_x').value
        base_y = self.get_parameter('base_wind_y').value
        base_z = self.get_parameter('base_wind_z').value

        self.Cd = self.get_parameter('drone_drag_coeff').value
        self.A = self.get_parameter('drone_cross_section_m2').value
        self.rho = 1.225  # Air density kg/m^3

        # Instantiate Wind Grid Engine from your package
        self.wind_grid = WindFieldGrid(
            bounds=(-500.0, 500.0, -500.0, 500.0, 0.0, 200.0),
            resolution=10.0,
            base_wind=(base_x, base_y, base_z),
            enable_shear=enable_shear,
            enable_turbulence=enable_turbulence
        )

        self.drone_pos = (0.0, 0.0, 0.0)
        self.drone_vel = (0.0, 0.0, 0.0)

        # ROS 2 Pubs/Subs
        self.create_subscription(
            Odometry, '/model/ansa_drone/odometry', self._odom_cb, 10)

        self.wind_pub = self.create_publisher(Vector3, '/env/wind_velocity', 10)
        self.force_pub = self.create_publisher(Wrench, '/model/ansa_drone/wind_wrench', 10)

        # 50 Hz physics loop
        self.create_timer(0.02, self._physics_loop)
        self.get_logger().info("Wind Simulation Engine node started successfully.")

    def _odom_cb(self, msg: Odometry):
        p = msg.pose.pose.position
        v = msg.twist.twist.linear
        self.drone_pos = (p.x, p.y, p.z)
        self.drone_vel = (v.x, v.y, v.z)

    def _physics_loop(self):
        t = self.get_clock().now().nanoseconds / 1e9

        # Sample wind
        sample = self.wind_grid.sample_at(self.drone_pos, timestamp=t)
        w_vx, w_vy, w_vz = sample.velocity_vector

        # Publish wind vector
        wind_msg = Vector3()
        wind_msg.x = float(w_vx)
        wind_msg.y = float(w_vy)
        wind_msg.z = float(w_vz)
        self.wind_pub.publish(wind_msg)

        # Calculate relative drag force
        rel_vx = w_vx - self.drone_vel[0]
        rel_vy = w_vy - self.drone_vel[1]
        rel_vz = w_vz - self.drone_vel[2]

        v_rel_mag = math.sqrt(rel_vx**2 + rel_vy**2 + rel_vz**2)

        if v_rel_mag > 1e-3:
            f_mag = 0.5 * self.rho * (v_rel_mag ** 2) * self.Cd * self.A
            
            wrench = Wrench()
            wrench.force.x = f_mag * (rel_vx / v_rel_mag)
            wrench.force.y = f_mag * (rel_vy / v_rel_mag)
            wrench.force.z = f_mag * (rel_vz / v_rel_mag)
            
            self.force_pub.publish(wrench)


def main(args=None):
    rclpy.init(args=args)
    node = WindSimulationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()