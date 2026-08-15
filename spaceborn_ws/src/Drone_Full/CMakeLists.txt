cmake_minimum_required(VERSION 3.8)
project(Drone_Full)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY
    config
    launch
    meshes
    textures
    urdf
    worlds
    models
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
