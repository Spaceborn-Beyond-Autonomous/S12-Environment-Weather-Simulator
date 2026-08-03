# S12 – Environment & Weather Simulator

## Phase 1: Architecture Overview

## Purpose

The Environment & Weather Simulator is responsible for generating realistic environmental conditions for simulation. It provides a centralized weather model that can be consumed by other modules through well-defined integration interfaces.

This document describes the project architecture only. Implementation details will be added after all development phases are completed.

---

# Project Structure
## Repository Structure

```
S12-Environment-Weather-Simulator/
│
├── config/
│   ├── clear_weather.yaml
│   ├── default.yaml
│   ├── dust_storm.yaml
│   ├── fog.yaml
│   ├── rain.yaml
│   ├── snow.yaml
│   └── storm.yaml
│
├── docs/
│   ├── architecture.md
│   ├── interface_spec.md
│   └── user_guide.md
│
├── environment_weather_simulator/
│   │
│   ├── api.py
│   ├── engine.py
│   ├── scenario_loader.py
│   ├── timeline.py
│   │
│   ├── gazebo/
│   │   ├── world_generator.py
│   │   ├── effects/
│   │   └── worlds/
│   │
│   ├── precipitation/
│   │   ├── rain_model.py
│   │   ├── snow_model.py
│   │   ├── fog_dust_model.py
│   │   └── attenuation.py
│   │
│   ├── wind/
│   │   ├── wind_field.py
│   │   ├── gust_shear.py
│   │   └── turbulence.py
│   │
│   ├── solar_thermal/
│   │   ├── solar_model.py
│   │   └── thermal_model.py
│   │
│   ├── emi/
│   │   └── emi_model.py
│   │
│   └── integration/
│       ├── digital_twin_bridge.py
│       ├── digital_earth_bridge.py
│       ├── lidar_bridge.py
│       ├── nav_bridge.py
│       ├── vision_bridge.py
│       ├── weather_camera.py
│       ├── weather_gps.py
│       ├── weather_imu.py
│       └── dt_server.py
│
├── launch/
│   ├── environment_weather.launch.py
│   ├── sensor_noise.launch.py
│   └── weather.launch.py
│
├── resource/
├── test/
├── package.xml
├── setup.py
└── README.md
```
---

# Architecture

# Simulator Workflow

The Environment & Weather Simulator follows a centralized execution pipeline. Rather than maintaining separate launch files for each weather condition, the simulator uses a single configurable launch file that generates the required environment based on the selected weather effect.

## Execution Flow

```
User Command
      │
      ▼
weather.launch.py
      │
      ▼
Load YAML Configuration
      │
      ▼
Scenario Loader
      │
      ▼
Timeline Manager
      │
      ▼
Environment Engine
      │
      ├───────────────────────────────────────┐
      │                                       │
      ▼                                       ▼
Weather Models                         World Generator
(Rain, Fog, Snow, Wind,               (Generate SDF World)
 Storm, Dust, Solar,
 Thermal, EMI)
      │                                       │
      └──────────────────┬────────────────────┘
                         ▼
                Generated Weather State
                         │
                         ▼
          Gazebo Simulation Environment
                         │
                         ▼
            Integration Interfaces
      ├──────────────┬──────────────┬──────────────┐
      ▼              ▼              ▼              ▼
 Digital Twin   Navigation      Vision         LiDAR
        │
        ├──────────────┐
        ▼              ▼
 Weather GPS      Weather IMU
```

## Weather Selection

A single launch file is responsible for all supported weather conditions.

Example:

```bash
ros2 launch environment_weather_simulator weather.launch.py effect:=clear
ros2 launch environment_weather_simulator weather.launch.py effect:=rain
ros2 launch environment_weather_simulator weather.launch.py effect:=fog
ros2 launch environment_weather_simulator weather.launch.py effect:=snow
ros2 launch environment_weather_simulator weather.launch.py effect:=dust
ros2 launch environment_weather_simulator weather.launch.py effect:=storm
```

The launch file automatically:

1. Reads the selected weather effect.
2. Loads the corresponding YAML configuration.
3. Initializes the Environment Engine.
4. Generates the required Gazebo world.
5. Inserts the required environmental effects.
6. Starts the simulation using the generated world.

No separate launch files are required for individual weather conditions. All weather modes are controlled through a single configurable launch interface.
---

# Module Responsibilities

## Configuration

Stores predefined weather scenarios such as clear weather, rain, fog, snow, storm, and dust storm.

---

## Scenario Loader

Loads scenario configurations from YAML files and prepares them for execution.

---

## Timeline

Controls simulation timing, transitions, scheduling, and progression of environmental events.

---

## Environment Engine

Acts as the core controller of the simulator.

Responsibilities include:

* Coordinating all weather modules
* Managing simulation state
* Producing the current Weather State
* Providing a unified interface for integration modules

The Environment Engine is the central component of the project.

---

## Weather Modules

The simulator is divided into independent weather models:

* Precipitation
* Wind
* Solar & Thermal
* EMI (Electromagnetic Interference)

Each module is responsible only for its own environmental domain.

---

## Integration Layer

The Integration layer exports weather information to external systems.

Available integrations:

* Digital Twin
* Digital Earth
* Navigation
* Vision
* LiDAR

Each bridge acts as an adapter between the Environment Engine and an external consumer. Bridges do not implement weather simulation logic.

---

# Design Principles

* Modular architecture
* Separation of responsibilities
* Independent weather models
* Centralized Environment Engine
* Decoupled integration interfaces
* ROS 2 compatible design
* Extensible for future weather models and external systems

---

# Development Status

| Module               | Status                   |
| -------------------- | ------------------------ |
| Project Architecture | ✅ Completed              |
| Configuration        | ✅ Completed              |
| Scenario Design      | ✅ Completed              |
| Timeline Design      | ✅ Completed              |
| Engine Design        | ⏳ Pending Implementation |
| Weather Modules      | ⏳ Pending Implementation |
| Integration Bridges  | ⏳ Pending Implementation |
| Testing              | ⏳ Pending                |
| Documentation        | ⏳ Ongoing                |

---

## Note

This document represents the Phase 1 architectural design of the Environment & Weather Simulator. It is intended to help team members understand the overall system organization and module responsibilities before implementation. The documentation will be updated in later phases as the simulator is fully implemented and integrated with other project components.

