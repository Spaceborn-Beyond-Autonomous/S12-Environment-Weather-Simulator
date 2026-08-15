#!/usr/bin/env python3
"""
Synchronized 4-motor hover controller with attitude leveling AND
keyboard-teleop support via /drone/cmd_vel.

Fixes the toppling issue from running 4 separate `ros2 topic pub` loops by:
  1. Publishing all 4 motor wrenches from ONE node, ONE timer tick (synced).
  2. Reading IMU orientation and applying differential thrust to correct
     roll/pitch tilt, on top of a common hover thrust.
  3. Accepting /drone/cmd_vel (geometry_msgs/Twist) so a teleop node can
     command climb/descend (linear.z) and forward/back/left/right motion
     via commanded tilt (linear.x / linear.y).

Run:
    python3 drone_hover_controller.py
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Wrench, Twist
from sensor_msgs.msg import Imu
import math


class DroneHoverController(Node):
    def __init__(self):
        super().__init__('drone_hover_controller')

        # ---- Tune these ----
        self.total_mass = 1.02          # kg, approx from URDF (adjust if you know exact)
        self.gravity = 9.81
        self.hover_thrust_per_motor = (self.total_mass * self.gravity) / 4.0

        self.kp_roll = 1.5              # N per radian of roll error
        self.kp_pitch = 1.5             # N per radian of pitch error
        self.kd_roll = 0.6              # N per (rad/s) of roll rate - DAMPING, prevents oscillation
        self.kd_pitch = 0.6             # N per (rad/s) of pitch rate - DAMPING, prevents oscillation
        self.max_correction = 1.0       # N, clamp so correction can't exceed/invert thrust
        self.max_tilt = math.radians(15)   # don't let teleop command more than 15 deg tilt
        self.max_throttle_offset = 1.5     # N added/removed across all motors for climb/descend

        # ---- State (measured) ----
        self.roll = 0.0
        self.pitch = 0.0
        self.roll_rate = 0.0
        self.pitch_rate = 0.0

        # ---- State (commanded, from keyboard via cmd_vel) ----
        self.target_roll = 0.0      # rad, desired tilt left(-)/right(+)
        self.target_pitch = 0.0     # rad, desired tilt back(-)/forward(+)
        self.throttle_offset = 0.0  # N, added equally to all 4 motors

        # ---- Publishers: motor layout from URDF ----
        # leftfront  (motor1): x=+0.1205  y=+0.1218
        # rightfront (motor2): x=+0.1213  y=-0.1210
        # leftback   (motor3): x=-0.1224  y=+0.1210
        # rightback  (motor4): x=-0.1216  y=-0.1218
        self.pub_lf = self.create_publisher(Wrench, '/drone/motor1/force', 10)
        self.pub_rf = self.create_publisher(Wrench, '/drone/motor2/force', 10)
        self.pub_lb = self.create_publisher(Wrench, '/drone/motor3/force', 10)
        self.pub_rb = self.create_publisher(Wrench, '/drone/motor4/force', 10)

        # ---- IMU subscriber ----
        self.create_subscription(Imu, '/imu/data', self.imu_cb, 10)

        # ---- Keyboard teleop subscriber ----
        self.create_subscription(Twist, '/drone/cmd_vel', self.cmd_vel_cb, 10)

        # ---- Soft-start: ramp thrust in over ~1s instead of snapping to full ----
        self.start_time = self.get_clock().now()
        self.ramp_duration = 1.0  # seconds

        # ---- Control loop: 50 Hz, all motors published together ----
        self.timer = self.create_timer(1.0 / 50.0, self.control_loop)

        self.get_logger().info(
            f'Hover thrust per motor: {self.hover_thrust_per_motor:.3f} N'
        )

    def imu_cb(self, msg: Imu):
        # Convert quaternion to roll/pitch (yaw not needed for leveling)
        q = msg.orientation
        # roll (x-axis rotation)
        sinr_cosp = 2 * (q.w * q.x + q.y * q.z)
        cosr_cosp = 1 - 2 * (q.x * q.x + q.y * q.y)
        self.roll = math.atan2(sinr_cosp, cosr_cosp)

        # pitch (y-axis rotation)
        sinp = 2 * (q.w * q.y - q.z * q.x)
        sinp = max(-1.0, min(1.0, sinp))
        self.pitch = math.asin(sinp)

        # angular velocity (rad/s) - used as the damping (D) term
        self.roll_rate = msg.angular_velocity.x
        self.pitch_rate = msg.angular_velocity.y

    def cmd_vel_cb(self, msg: Twist):
        # linear.x -> forward/back tilt command (pitch), linear.y -> left/right tilt (roll)
        # linear.z -> climb/descend throttle offset. angular.z (yaw) not modeled - no
        # reaction torque from the force plugin, so it's accepted but has no effect.
        self.target_pitch = self.clamp(msg.linear.x, -1.0, 1.0) * self.max_tilt
        self.target_roll = self.clamp(-msg.linear.y, -1.0, 1.0) * self.max_tilt
        self.throttle_offset = self.clamp(msg.linear.z, -1.0, 1.0) * self.max_throttle_offset
        self.get_logger().info(
            f'cmd_vel received: x={msg.linear.x:.2f} y={msg.linear.y:.2f} z={msg.linear.z:.2f}'
        )

    def clamp(self, val, lo, hi):
        return max(lo, min(hi, val))

    def control_loop(self):
        # Soft-start ramp factor: 0 -> 1 over self.ramp_duration seconds
        elapsed = (self.get_clock().now() - self.start_time).nanoseconds / 1e9
        ramp = min(1.0, elapsed / self.ramp_duration)

        # Error is now measured-vs-COMMANDED angle, not measured-vs-zero,
        # so the keyboard can request a tilt and the controller holds it.
        roll_error = self.target_roll - self.roll
        pitch_error = self.target_pitch - self.pitch

        roll_corr = self.clamp(self.kp_roll * roll_error - self.kd_roll * self.roll_rate,
                                -self.max_correction, self.max_correction)
        pitch_corr = self.clamp(self.kp_pitch * pitch_error - self.kd_pitch * self.pitch_rate,
                                 -self.max_correction, self.max_correction)

        base = (self.hover_thrust_per_motor + self.throttle_offset) * ramp

        # front/back split by pitch_corr, left/right split by roll_corr
        # (corrections also ramped in, so we don't get a sharp attitude
        # correction kick before thrust has even built up)
        lf = base + (pitch_corr + roll_corr) * ramp
        rf = base + (pitch_corr - roll_corr) * ramp
        lb = base + (-pitch_corr + roll_corr) * ramp
        rb = base + (-pitch_corr - roll_corr) * ramp

        self._publish(self.pub_lf, lf)
        self._publish(self.pub_rf, rf)
        self._publish(self.pub_lb, lb)
        self._publish(self.pub_rb, rb)

    def _publish(self, pub, z_force):
        msg = Wrench()
        msg.force.z = max(0.0, z_force)  # rotors can't push down through air this way
        pub.publish(msg)


def main():
    rclpy.init()
    node = DroneHoverController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
