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

    # Resolve mesh file paths for Gazebo Harmonic/Ignition
    meshes_dir = os.path.join(pkg, 'meshes')
    robot_desc = robot_desc.replace(
        'package://ansa_digital_twin/meshes/',
        'file://' + meshes_dir + '/'
    )

    # 1. Start Gazebo with the Rain World
    gazebo = ExecuteProcess(
        cmd=['gz', 'sim', '-r',
             os.path.join(pkg, 'worlds', 'ansa_world_rain.sdf')],
        output='screen'
    )

    # 2. Spawn drone — wait 6 seconds for Gazebo simulation server to initialize
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

    # 3. Comprehensive ROS2 ↔ Gazebo Bridge (Sensors + Control + Rain Physics)
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='sim_rain_bridge',
        arguments=[
            # Sensor Topics (Gz -> ROS 2)
            '/imu/data@sensor_msgs/msg/Imu[gz.msgs.IMU',
            '/gps/fix@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat',
            '/baro/data@sensor_msgs/msg/FluidPressure[gz.msgs.FluidPressure',
            '/model/ansa_drone/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/model/ansa_drone/battery/ansa_drone_battery/state@sensor_msgs/msg/BatteryState[gz.msgs.BatteryState',
            
            # Control Topics (ROS 2 -> Gz)
            '/ansa_drone/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/ansa_drone/enable@std_msgs/msg/Bool]gz.msgs.Boolean',
            
            # Rain Physics External Wrench Topic (ROS 2 -> Gz)
            '/ansa_drone/gazebo/external_wrench@geometry_msgs/msg/Wrench]gz.msgs.Wrench',
        ],
        remappings=[
            ('/model/ansa_drone/battery/ansa_drone_battery/state', '/battery_state'),
        ],
        output='screen'
    )

    # 4. Robot State Publisher
    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_desc}],
        output='screen'
    )

    # 5. Rain Physics Node
    rain_node = Node(
        package='ansa_digital_twin',
        executable='rain_physics_node.py',
        name='rain_physics_node',
        output='screen',
        parameters=[{
            'rain_intensity_mm_hr': 35.0,     # Heavy rain intensity
            'droplet_terminal_velocity': 9.0,  # Vertical impact speed (m/s)
            'drone_top_area_m2': 0.08,        # Effective top area (m²)
            'wind_velocity_x': 2.0,           # Horizontal rain slant X (m/s)
            'wind_velocity_y': 1.0            # Horizontal rain slant Y (m/s)
        }]
    )

    return LaunchDescription([
        gazebo,
        rsp,
        bridge,
        spawn,
        rain_node
    ])