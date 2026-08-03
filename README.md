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
---
# Gazebo World Generation

Directory:

```text
environment_weather_simulator/gazebo/
```

Files:

```text
world_generator.py

effects/
worlds/
```

The simulator automatically creates a simulation world based on the selected weather configuration.

Current functionality includes:

- Loading base world
- Selecting weather effects
- Inserting SDF effect models
- Generating final simulation world
- Exporting generated SDF world

Generated worlds are ready for Gazebo simulation.

---

## Weather Effect Assets

Current available weather assets:

```text
effects/
├── rain.sdf
├── fog.sdf
├── snow.sdf
├── dust.sdf
└── storm.sdf
```

---

# World Generation Pipeline

```text
Base World
      │
      ▼
Weather Configuration
      │
      ▼
World Generator
      │
      ▼
Insert Weather Effects
      │
      ▼
Generate SDF World
      │
      ▼
Generated World
      │
      ▼
Gazebo Simulation
```

---

# Configuration System

The simulator uses YAML configuration files to describe weather conditions.

Configuration directory:

```text
config/
```

Current configuration files:

```text
clear_weather.yaml
default.yaml
dust_storm.yaml
fog.yaml
rain.yaml
snow.yaml
storm.yaml
```

Each configuration defines weather parameters that are loaded by the Scenario Loader before the simulation begins.

---

# Launch System

Unlike many simulation projects, this repository does **not** maintain separate launch files for every weather condition.

Instead, a **single configurable launch file** controls the complete simulator.

Launch file:

```text
launch/weather.launch.py
```

This launch file:

- Reads the selected weather effect
- Loads the corresponding YAML configuration
- Initializes the Environment Engine
- Calls the World Generator
- Generates the final Gazebo world
- Starts the simulation

This approach keeps the simulator modular and avoids maintaining multiple nearly identical launch files.

---

# Running Different Weather Effects

Examples:

```bash
# Clear Weather
ros2 launch environment_weather_simulator weather.launch.py effect:=clear

# Rain
ros2 launch environment_weather_simulator weather.launch.py effect:=rain

# Fog
ros2 launch environment_weather_simulator weather.launch.py effect:=fog

# Snow
ros2 launch environment_weather_simulator weather.launch.py effect:=snow

# Dust Storm
ros2 launch environment_weather_simulator weather.launch.py effect:=dust

# Thunder Storm
ros2 launch environment_weather_simulator weather.launch.py effect:=storm
```

Only the value of the **effect** argument changes.

No additional launch files are required.

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

