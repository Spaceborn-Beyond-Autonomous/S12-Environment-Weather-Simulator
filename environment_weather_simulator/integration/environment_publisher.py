#!/usr/bin/env python3

"""
ROS2 integration node for the S12 Environment & Weather Simulator.

Data flow:

Existing Drone
     |
     | /model/ansa_drone/odometry
     v
EnvironmentPublisher
     |
     v
EnvironmentEngine
     |
     +---- WindFieldGrid
     +---- SolarModel
     +---- ThermalModel
     +---- EMIModel
     |
     v
Environment ROS2 topics

The existing drone repository is not modified.

Subscribed topic:
    /model/ansa_drone/odometry

Published topics:
    /environment/wind
    /environment/solar
    /environment/thermal
    /environment/emi
"""

import math
import time

import rclpy
from rclpy.node import Node

from nav_msgs.msg import Odometry
from geometry_msgs.msg import Vector3
from std_msgs.msg import Float32

from environment_weather_simulator.engine import EnvironmentEngine


class EnvironmentPublisher(Node):
    """
    ROS2 node responsible for connecting the existing drone
    state with the S12 environment engine.

    This node does not perform environmental calculations itself.

    Responsibilities:
        1. Read drone odometry.
        2. Send drone position to EnvironmentEngine.
        3. Receive WeatherState.
        4. Publish environment effects.
    """

    def __init__(self):
        super().__init__("environment_publisher")

        # =================================================
        # Parameters
        # =================================================

        self.declare_parameter(
            "odometry_topic",
            "/model/ansa_drone/odometry",
        )

        self.declare_parameter(
            "publish_rate",
            10.0,
        )

        odometry_topic = self.get_parameter(
            "odometry_topic"
        ).value

        publish_rate = float(
            self.get_parameter("publish_rate").value
        )

        if publish_rate <= 0.0:
            publish_rate = 10.0

        # =================================================
        # Environment Engine
        # =================================================

        self.engine = EnvironmentEngine()

        # =================================================
        # Drone State
        # =================================================

        self.drone_x = 0.0
        self.drone_y = 0.0
        self.drone_z = 0.0

        self.last_odometry_time = None
        self.drone_state_received = False

        # =================================================
        # ROS2 Subscriber
        # =================================================

        self.odometry_subscriber = self.create_subscription(
            Odometry,
            odometry_topic,
            self.odometry_callback,
            10,
        )

        # =================================================
        # ROS2 Publishers
        # =================================================

        # Wind velocity vector
        self.wind_publisher = self.create_publisher(
            Vector3,
            "/environment/wind",
            10,
        )

        # Solar irradiance / glare
        self.solar_publisher = self.create_publisher(
            Float32,
            "/environment/solar",
            10,
        )

        # Thermal surface temperature delta
        self.thermal_publisher = self.create_publisher(
            Float32,
            "/environment/thermal",
            10,
        )

        # EMI interference
        self.emi_publisher = self.create_publisher(
            Float32,
            "/environment/emi",
            10,
        )

        # =================================================
        # Timer
        # =================================================

        timer_period = 1.0 / publish_rate

        self.timer = self.create_timer(
            timer_period,
            self.environment_update,
        )

        # =================================================
        # Startup Information
        # =================================================

        self.get_logger().info(
            "=================================================="
        )

        self.get_logger().info(
            " S12 Environment Publisher"
        )

        self.get_logger().info(
            "=================================================="
        )

        self.get_logger().info(
            f"Odometry topic : {odometry_topic}"
        )

        self.get_logger().info(
            f"Publish rate   : {publish_rate:.1f} Hz"
        )

        self.get_logger().info(
            "Environment engine initialized."
        )

        self.get_logger().info(
            "Waiting for drone odometry..."
        )

    # =====================================================
    # Drone Odometry Callback
    # =====================================================

    def odometry_callback(self, msg: Odometry):
        """
        Receives the current drone position.

        Existing drone topic:
            /model/ansa_drone/odometry

        Only position is required by the current
        environmental models.
        """

        self.drone_x = float(
            msg.pose.pose.position.x
        )

        self.drone_y = float(
            msg.pose.pose.position.y
        )

        self.drone_z = float(
            msg.pose.pose.position.z
        )

        self.drone_state_received = True

        # Store ROS timestamp if available.
        stamp = msg.header.stamp

        if stamp.sec != 0 or stamp.nanosec != 0:
            self.last_odometry_time = (
                float(stamp.sec)
                + float(stamp.nanosec) * 1e-9
            )
        else:
            self.last_odometry_time = time.time()

    # =====================================================
    # Environment Update
    # =====================================================

    def environment_update(self):
        """
        Runs the environment simulation and publishes
        the calculated environmental effects.
        """

        if not self.drone_state_received:
            self.get_logger().debug(
                "Waiting for drone odometry..."
            )
            return

        # -------------------------------------------------
        # Simulation timestamp
        # -------------------------------------------------

        timestamp = time.time()

        # -------------------------------------------------
        # Sample Environment
        # -------------------------------------------------

        try:
            weather_state = self.engine.sample_at(
                position_xyz=(
                    self.drone_x,
                    self.drone_y,
                    self.drone_z,
                ),
                timestamp=timestamp,
            )

        except Exception as exc:
            self.get_logger().error(
                f"Environment calculation failed: {exc}"
            )
            return

        # -------------------------------------------------
        # Publish Wind
        # -------------------------------------------------

        wind_msg = Vector3()

        wind_msg.x = float(
            weather_state.wind.velocity_vector[0]
        )

        wind_msg.y = float(
            weather_state.wind.velocity_vector[1]
        )

        wind_msg.z = float(
            weather_state.wind.velocity_vector[2]
        )

        self.wind_publisher.publish(wind_msg)

        # -------------------------------------------------
        # Publish Solar
        # -------------------------------------------------

        solar_msg = Float32()

        solar_msg.data = float(
            weather_state.solar.glare_intensity
        )

        self.solar_publisher.publish(solar_msg)

        # -------------------------------------------------
        # Publish Thermal
        # -------------------------------------------------

        thermal_msg = Float32()

        thermal_msg.data = float(
            weather_state.solar.surface_temp_delta_c
        )

        self.thermal_publisher.publish(thermal_msg)

        # -------------------------------------------------
        # Publish EMI
        # -------------------------------------------------

        emi_msg = Float32()

        emi_msg.data = float(
            weather_state.emi.interference_db
        )

        self.emi_publisher.publish(emi_msg)

        # -------------------------------------------------
        # Debug information
        # -------------------------------------------------

        wind = weather_state.wind.velocity_vector

        wind_speed = math.sqrt(
            wind[0] ** 2
            + wind[1] ** 2
            + wind[2] ** 2
        )

        self.get_logger().debug(
            "Environment update | "
            f"Position=({self.drone_x:.2f}, "
            f"{self.drone_y:.2f}, "
            f"{self.drone_z:.2f}) | "
            f"Wind={wind_speed:.2f} m/s | "
            f"Solar={weather_state.solar.glare_intensity:.3f} | "
            f"ThermalDelta="
            f"{weather_state.solar.surface_temp_delta_c:.2f} C | "
            f"EMI="
            f"{weather_state.emi.interference_db:.2f} dB"
        )


# =========================================================
# ROS2 Main
# =========================================================

def main(args=None):
    """
    ROS2 entry point.
    """

    rclpy.init(args=args)

    node = EnvironmentPublisher()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        node.get_logger().info(
            "Environment Publisher stopped."
        )

    finally:
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()

