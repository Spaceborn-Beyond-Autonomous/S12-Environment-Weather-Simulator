cmake_minimum_required(VERSION 3.8)
project(ansa_digital_twin)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

find_package(ament_cmake REQUIRED)
find_package(ros_gz_bridge REQUIRED)   # optional, only if you use its headers
# add other dependencies as needed (e.g., rclcpp, std_msgs...)

# Install Python launch files
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}/
)

# Install config files (if any)
install(DIRECTORY config
  DESTINATION share/${PROJECT_NAME}/
)

# Install world files
install(DIRECTORY worlds
  DESTINATION share/${PROJECT_NAME}/
)

# Install URDF
install(
  FILES urdf/Drone_Full.urdf
  DESTINATION share/${PROJECT_NAME}/urdf/
)

# Install mesh files
install(
  DIRECTORY meshes
  DESTINATION share/${PROJECT_NAME}/
)

# Install Python nodes (if you have any)
# install(PYTHON_EXECUTABLE ... )

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()