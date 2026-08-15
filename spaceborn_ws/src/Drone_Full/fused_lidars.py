import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField
from sensor_msgs_py import point_cloud2
import message_filters
import numpy as np
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

class LidarMerger(Node):
    def __init__(self):
        super().__init__('lidar_merger')

        # Use SensorDataQoS to handle high-frequency sensor data
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            depth=10
        )

        # 1. Subscribers
        self.sub1 = message_filters.Subscriber(self, PointCloud2, '/rover/lidar/points', qos_profile=qos_profile)
        self.sub2 = message_filters.Subscriber(self, PointCloud2, '/drone/lidar/points', qos_profile=qos_profile)

        # 2. Synchronizer: Increased slop to 1.0s to account for lower publishing rates
        self.ts = message_filters.ApproximateTimeSynchronizer([self.sub1, self.sub2], queue_size=10, slop=1.0)
        self.ts.registerCallback(self.callback)

        # 3. Publisher
        self.publisher = self.create_publisher(PointCloud2, '/fusion/lidar', 10)
        self.get_logger().info('Lidar Merger Node initialized and waiting for data...')

    def callback(self, cloud1, cloud2):
        try:
            # 1. Convert to numpy arrays
            pts1 = np.array(list(point_cloud2.read_points(cloud1, field_names=("x", "y", "z"), skip_nans=True)))
            pts2 = np.array(list(point_cloud2.read_points(cloud2, field_names=("x", "y", "z"), skip_nans=True)))

            # 2. Concatenate along the first axis (rows) to handle differing point counts
            merged_pts = np.concatenate((pts1, pts2), axis=0)

            # 3. Create new PointCloud2 message
            header = cloud1.header
            fields = [
                PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
                PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
                PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1)
            ]
            
            merged_msg = point_cloud2.create_cloud(header, fields, merged_pts)
            self.publisher.publish(merged_msg)
            
            # Debug log to confirm success
            self.get_logger().info(f"Published merged cloud with {merged_pts.shape[0]} points.")
            
        except Exception as e:
            self.get_logger().error(f"Error merging clouds: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = LidarMerger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()