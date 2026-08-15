#!/usr/bin/env python3
"""
Simple, safe vertical-only flight sequence:
    1. Ramp up and CLIMB for ~3 seconds
    2. Brief HOVER at altitude
    3. Gentle, controlled DESCEND
    4. Cut thrust once descent time has elapsed (assumed landed)

No left/right/forward/back/yaw commands are ever issued - this script
only ever commands equal thrust on all 4 motors (vertical motion), and
uses the same PD attitude stabilization as drone_hover_controller.py to
correct any unwanted tilt along the way.

IMPORTANT - this is OPEN LOOP for altitude (no height sensor in your
URDF), so it's a timed thrust profile, not a guaranteed landing. Tune
CLIMB_ACCEL / DESCEND_ACCEL / durations below after watching one run.

Run (make sure drone_hover_controller.py / keyboard teleop are NOT also
running at the same time - only one node should be commanding the motors):
    python3 drone_takeoff_land.py
"""

import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Wrench
from sensor_msgs.msg import Imu


# ---- Flight profile (tune these) ----
TOTAL_MASS = 1.02            # kg, approx from URDF - adjust if you know exact mass
GRAVITY = 9.81

RAMP_UP_DURATION = 1.0       # s, soft-start into climb thrust
CLIMB_DURATION = 3.0         # s, as requested - climbs for 3 seconds
CLIMB_ACCEL = 0.8            # m/s^2 net upward accel during climb (keep gentle)

HOVER_DURATION = 1.0         # s, brief steady hover at altitude before descending

DESCEND_DURATION = 3.0       # s, controlled descent
DESCEND_ACCEL = 0.5          # m/s^2 net downward accel during descent (gentle)

FINAL_HOLD = 1.0             # s, sit at zero thrust at the end (assume landed/settling)

# ---- Attitude stabilization gains (same approach as drone_hover_controller.py) ----
KP = 1.5
KD = 0.6
MAX_CORRECTION = 1.0         # N, per-motor clamp on attitude correction


class TakeoffLandSequence(Node):
    def __init__(self):
        super().__init__('drone_takeoff_land')

        self.hover_thrust_per_motor = (TOTAL_MASS * GRAVITY) / 4.0
        self.climb_thrust_per_motor = (TOTAL_MASS * (GRAVITY + CLIMB_ACCEL)) / 4.0
        self.descend_thrust_per_motor = (TOTAL_MASS * (GRAVITY - DESCEND_ACCEL)) / 4.0

        self.roll = 0.0
        self.pitch = 0.0
        self.roll_rate = 0.0
        self.pitch_rate = 0.0

        self.pub_lf = self.create_publisher(Wrench, '/drone/motor1/force', 10)
        self.pub_rf = self.create_publisher(Wrench, '/drone/motor2/force', 10)
        self.pub_lb = self.create_publisher(Wrench, '/drone/motor3/force', 10)
        self.pub_rb = self.create_publisher(Wrench, '/drone/motor4/force', 10)

        self.create_subscription(Imu, '/imu/data', self.imu_cb, 10)

        self.start_time = self.get_clock().now()
        self.timer = self.create_timer(1.0 / 50.0, self.control_loop)

        # Precompute phase boundaries (seconds, cumulative)
        self.t_ramp_end = RAMP_UP_DURATION
        self.t_climb_end = self.t_ramp_end + CLIMB_DURATION
        self.t_hover_end = self.t_climb_end + HOVER_DURATION
        self.t_descend_end = self.t_hover_end + DESCEND_DURATION
        self.t_final_end = self.t_descend_end + FINAL_HOLD

        self.get_logger().info(
            f'Hover thrust/motor: {self.hover_thrust_per_motor:.3f} N | '
            f'Climb thrust/motor: {self.climb_thrust_per_motor:.3f} N | '
            f'Descend thrust/motor: {self.descend_thrust_per_motor:.3f} N'
        )
        self.get_logger().info(
            f'Sequence: ramp-up 0-{self.t_ramp_end:.1f}s, '
            f'climb to {self.t_climb_end:.1f}s, '
            f'hover to {self.t_hover_end:.1f}s, '
            f'descend to {self.t_descend_end:.1f}s, '
            f'then thrust off.'
        )

        self.done_logged = False

    def imu_cb(self, msg: Imu):
        q = msg.orientation
        sinr_cosp = 2 * (q.w * q.x + q.y * q.z)
        cosr_cosp = 1 - 2 * (q.x * q.x + q.y * q.y)
        self.roll = math.atan2(sinr_cosp, cosr_cosp)

        sinp = 2 * (q.w * q.y - q.z * q.x)
        sinp = max(-1.0, min(1.0, sinp))
        self.pitch = math.asin(sinp)

        self.roll_rate = msg.angular_velocity.x
        self.pitch_rate = msg.angular_velocity.y

    def clamp(self, val, lo, hi):
        return max(lo, min(hi, val))

    def target_base_thrust(self, elapsed):
        """Returns the desired equal-thrust-per-motor for the current phase,
        with smooth ramps between phases instead of hard steps."""
        if elapsed < self.t_ramp_end:
            # 0 -> climb thrust
            frac = elapsed / RAMP_UP_DURATION
            return self.climb_thrust_per_motor * frac

        elif elapsed < self.t_climb_end:
            return self.climb_thrust_per_motor

        elif elapsed < self.t_hover_end:
            # smoothly ease from climb thrust to hover thrust
            frac = (elapsed - self.t_climb_end) / HOVER_DURATION
            return self.climb_thrust_per_motor + \
                (self.hover_thrust_per_motor - self.climb_thrust_per_motor) * frac

        elif elapsed < self.t_descend_end:
            # smoothly ease from hover thrust down to descend thrust
            frac = (elapsed - self.t_hover_end) / DESCEND_DURATION
            return self.hover_thrust_per_motor + \
                (self.descend_thrust_per_motor - self.hover_thrust_per_motor) * frac

        elif elapsed < self.t_final_end:
            # ease descend thrust down to zero (assume near/at ground by now)
            frac = (elapsed - self.t_descend_end) / FINAL_HOLD
            return self.descend_thrust_per_motor * (1.0 - frac)

        else:
            return 0.0

    def control_loop(self):
        elapsed = (self.get_clock().now() - self.start_time).nanoseconds / 1e9

        base = self.target_base_thrust(elapsed)

        # Attitude PD stabilization, ALWAYS targeting level (0 roll, 0 pitch).
        # No lateral/yaw commands are ever issued in this script.
        roll_error = 0.0 - self.roll
        pitch_error = 0.0 - self.pitch
        roll_corr = self.clamp(KP * roll_error - KD * self.roll_rate,
                                -MAX_CORRECTION, MAX_CORRECTION)
        pitch_corr = self.clamp(KP * pitch_error - KD * self.pitch_rate,
                                 -MAX_CORRECTION, MAX_CORRECTION)

        lf = base + pitch_corr + roll_corr
        rf = base + pitch_corr - roll_corr
        lb = base - pitch_corr + roll_corr
        rb = base - pitch_corr - roll_corr

        self._publish(self.pub_lf, lf)
        self._publish(self.pub_rf, rf)
        self._publish(self.pub_lb, lb)
        self._publish(self.pub_rb, rb)

        if elapsed >= self.t_final_end and not self.done_logged:
            self.get_logger().info('Sequence complete - thrust off, holding at 0 N.')
            self.done_logged = True

    def _publish(self, pub, z_force):
        msg = Wrench()
        msg.force.z = max(0.0, z_force)
        pub.publish(msg)


def main():
    rclpy.init()
    node = TakeoffLandSequence()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

