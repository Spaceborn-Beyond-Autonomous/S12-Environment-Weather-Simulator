#!/usr/bin/env python3
"""
rain_physics_node.py — Hydro-dynamic rain impact, water mass accumulation, 
and slanted rain drag simulator for the ANSA drone.
"""

import math
import random
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Wrench, Vector3
from sensor_msgs.msg import Imu


class RainPhysicsNode(Node):
    def __init__(self):
        super().__init__('rain_physics_node')

        # -------------------------------------------------------------------
        # ROS 2 Parameters
        # -------------------------------------------------------------------
        self.declare_parameter('rain_intensity_mm_hr', 35.0)    # Heavy rain (mm/hr)
        self.declare_parameter('droplet_terminal_velocity', 9.0) # Downward speed (m/s)
        self.declare_parameter('drone_top_area_m2', 0.08)        # Top surface area (m²)
        self.declare_parameter('wind_velocity_x', 2.0)          # Horizontal rain slant X (m/s)
        self.declare_parameter('wind_velocity_y', 1.0)          # Horizontal rain slant Y (m/s)
        self.declare_parameter('water_drain_rate_kg_s', 0.005)   # Water drainage/shedding rate
        self.declare_parameter('max_water_film_kg', 0.04)        # Max trapped surface water (40g)

        # State Variables
        self.accumulated_water_mass_kg = 0.0
        self.current_pitch = 0.0
        self.current_roll = 0.0

        # -------------------------------------------------------------------
        # ROS 2 Interfaces
        # -------------------------------------------------------------------
        # Subscribe to IMU to track tilt angles
        self.create_subscription(Imu, '/imu/data', self._imu_cb, 10)

        # Publisher for external wrench (Force + Torque)
        self.wrench_pub = self.create_publisher(
            Wrench, '/ansa_drone/gazebo/external_wrench', 10)

        # Physics loop running at 50 Hz
        self.dt = 0.02
        self.create_timer(self.dt, self._apply_rain_dynamics)

        self.get_logger().info('Rain Physics Node online — active hydro-dynamics enabled.')

    def _imu_cb(self, msg: Imu):
        """Extract pitch and roll from quaternion orientation."""
        q = msg.orientation
        
        # Roll (x-axis rotation)
        sinr_cosp = 2.0 * (q.w * q.x + q.y * q.z)
        cosr_cosp = 1.0 - 2.0 * (q.x * q.x + q.y * q.y)
        self.current_roll = math.atan2(sinr_cosp, cosr_cosp)

        # Pitch (y-axis rotation)
        sinp = 2.0 * (q.w * q.y - q.z * q.x)
        if abs(sinp) >= 1:
            self.current_pitch = math.copysign(math.pi / 2, sinp)
        else:
            self.current_pitch = math.asin(sinp)

    def _apply_rain_dynamics(self):
        # Fetch current parameter values
        intensity = self.get_parameter('rain_intensity_mm_hr').value
        v_drop_z = self.get_parameter('droplet_terminal_velocity').value
        area = self.get_parameter('drone_top_area_m2').value
        v_wind_x = self.get_parameter('wind_velocity_x').value
        v_wind_y = self.get_parameter('wind_velocity_y').value
        drain_rate = self.get_parameter('water_drain_rate_kg_s').value
        max_water = self.get_parameter('max_water_film_kg').value

        # 1. Effective Surface Area Calculation based on Drone Tilt
        total_tilt = math.sqrt(self.current_pitch**2 + self.current_roll**2)
        effective_area = area * max(0.2, math.cos(total_tilt))

        # 2. Water Mass Flow Rate & Accumulation
        # 1 mm/hr rain intensity = 1 kg / (m² * 3600 s)
        mass_flow_rate = (intensity / 3600.0) * effective_area  # kg/s
        
        # Update water film payload buildup on drone body
        self.accumulated_water_mass_kg += (mass_flow_rate - drain_rate) * self.dt
        self.accumulated_water_mass_kg = max(0.0, min(max_water, self.accumulated_water_mass_kg))

        # 3. Direct Momentum Impact Force Calculation (F = m_dot * v)
        # Downward impact force
        f_impact_z = mass_flow_rate * v_drop_z
        
        # Static mass weight force (added water weight)
        f_weight_z = self.accumulated_water_mass_kg * 9.81
        
        # Total Z Force
        total_fz = -(f_impact_z + f_weight_z)

        # Horizontal Slanted Rain Drag (Momentum transfer from lateral rain speed)
        total_fx = mass_flow_rate * v_wind_x
        total_fy = mass_flow_rate * v_wind_y

        # 4. Stochastic Turbulence & Droplet Jitter (Forces & Torques)
        jitter_factor = 0.08 * abs(total_fz)
        jitter_fx = total_fx + random.gauss(0.0, jitter_factor)
        jitter_fy = total_fy + random.gauss(0.0, jitter_factor)
        jitter_fz = total_fz + random.gauss(0.0, jitter_factor * 0.5)

        # Off-center raindrop impacts create slight pitch/roll torques
        torque_x = random.gauss(0.0, 0.005 * abs(total_fz))
        torque_y = random.gauss(0.0, 0.005 * abs(total_fz))

        # 5. Build and Publish Wrench Message
        wrench_msg = Wrench()
        wrench_msg.force.x = round(jitter_fx, 4)
        wrench_msg.force.y = round(jitter_fy, 4)
        wrench_msg.force.z = round(jitter_fz, 4)
        
        wrench_msg.torque.x = round(torque_x, 5)
        wrench_msg.torque.y = round(torque_y, 5)
        wrench_msg.torque.z = 0.0

        self.wrench_pub.publish(wrench_msg)


def main(args=None):
    rclpy.init(args=args)
    node = RainPhysicsNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()