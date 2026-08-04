import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node

def generate_launch_description():
    pkg = get_package_share_directory('ansa_digital_twin')
    urdf_path = os.path.join(pkg, 'urdf', 'Drone_Full.urdf')

    # Read the plain URDF
    with open(urdf_path, 'r') as f:
        robot_desc = f.read()

    # Get absolute path to meshes folder (no trailing slash)
    meshes_dir = os.path.join(pkg, 'meshes')
    # Replace "package://ansa_digital_twin/meshes/" with "file://" + absolute path
    # (Gazebo understands file:// URIs)
    robot_desc = robot_desc.replace(
        'package://ansa_digital_twin/meshes/',
        'file://' + meshes_dir + '/'
    )

    # 1. Start Gazebo
    gazebo = ExecuteProcess(
        cmd=['gz', 'sim', '-r',
             os.path.join(pkg, 'worlds', 'ansa_world.sdf')],
        output='screen'
    )

    # 2. Spawn drone — wait 6 seconds for Gazebo to be ready
    spawn = TimerAction(period=6.0, actions=[
        ExecuteProcess(
            cmd=['ros2', 'run', 'ros_gz_sim', 'create',
                 '-name', 'ansa_drone',
                 '-string', robot_desc,
                 '-x', '0', '-y', '0', '-z', '0.5',
                 '-world', 'default'],
            output='screen'
        )
    ])

    # 3. ROS2 ↔ Gazebo bridge (unchanged)
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/imu/data@sensor_msgs/msg/Imu@gz.msgs.IMU',
            '/gps/fix@sensor_msgs/msg/NavSatFix@gz.msgs.NavSat',
            '/baro/data@sensor_msgs/msg/FluidPressure@gz.msgs.FluidPressure',
            '/model/ansa_drone/odometry@nav_msgs/msg/Odometry@gz.msgs.Odometry',
            '/model/ansa_drone/battery/ansa_drone_battery/state@sensor_msgs/msg/BatteryState@gz.msgs.BatteryState',            
            '/ansa_drone/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/ansa_drone/enable@std_msgs/msg/Bool@gz.msgs.Boolean',
            
        ],



        remappings=[
        ('/model/ansa_drone/battery/ansa_drone_battery/state', '/battery_state'),
    ],

        output='screen'
    )

    # 4. Robot state publisher
    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_desc}],
        output='screen'
    )

    return LaunchDescription([gazebo, rsp, bridge, spawn])
