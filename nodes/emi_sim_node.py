import rclpy
from rclpy.node import Node
import math
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float32

class EMISimulatorNode(Node):
    def __init__(self):
        super().__init__('emi_simulator_node')
        
        # EMI Tower Position (from SDF)
        self.tower_x = 5.0
        self.tower_y = 5.0
        self.tower_z = 4.0  # Midpoint of 8m tower
        self.base_intensity = 50.0  # Max interference factor

        # Subscriptions
        self.pose_sub = self.create_subscription(
            PoseStamped, '/ansa_drone/pose', self.pose_callback, 10)

        # EMI Intensity Publisher (for monitoring/logging)
        self.emi_pub = self.create_publisher(Float32, '/ansa_drone/emi_intensity', 10)

    def pose_callback(self, msg):
        dx = msg.pose.position.x - self.tower_x
        dy = msg.pose.position.y - self.tower_y
        dz = msg.pose.position.z - self.tower_z
        
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        dist = max(dist, 0.5)  # Avoid division by zero near tower core

        # Inverse square law: I = I_0 / d^2
        emi_field = self.base_intensity / (dist**2)

        out_msg = Float32()
        out_msg.data = emi_field
        self.emi_pub.publish(out_msg)

def main():
    rclpy.init()
    node = EMISimulatorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()