cmake_minimum_required(VERSION 3.8)
project(ansa_digital_twin)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find ROS 2 dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(std_msgs REQUIRED)

# -------------------------------------------------------------------
# 1. Install Python Environment & Package Modules
# -------------------------------------------------------------------
ament_python_install_package(environment_weather_simulator)

# -------------------------------------------------------------------
# 2. Install Python Executable Nodes
# -------------------------------------------------------------------
install(PROGRAMS
  nodes/rain_physics_node.py
  nodes/wind_simulation_node.py
  nodes/dt_server.py
  DESTINATION lib/${PROJECT_NAME}
)

# -------------------------------------------------------------------
# 3. Install Package Resource Directories
# -------------------------------------------------------------------
install(DIRECTORY
  config
  launch
  meshes
  urdf
  worlds
  DESTINATION share/${PROJECT_NAME}
)

# -------------------------------------------------------------------
# 4. Include & C++ Target Setup (if any C++ sources exist in src/)
# -------------------------------------------------------------------
include_directories(include)

ament_package()