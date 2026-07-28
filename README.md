# S12 – Environment & Weather Simulator

## Phase 1: Architecture Overview

## Purpose

The Environment & Weather Simulator is responsible for generating realistic environmental conditions for simulation. It provides a centralized weather model that can be consumed by other modules through well-defined integration interfaces.

This document describes the project architecture only. Implementation details will be added after all development phases are completed.

---

# Project Structure

```
S12-Environment-Weather-Simulator
│
├── config/
├── docs/
├── environment_weather_simulator/
│   ├── api.py
│   ├── engine.py
│   ├── scenario_loader.py
│   ├── timeline.py
│   ├── precipitation/
│   ├── wind/
│   ├── solar_thermal/
│   ├── emi/
│   └── integration/
├── launch/
├── resource/
├── test/
├── package.xml
├── setup.py
└── README.md
```

---

# Architecture

```
                Configuration Files
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
      ┌────────────────┼────────────────┐
      │                │                │
      ▼                ▼                ▼
 Precipitation      Wind         Solar/Thermal
      │                │                │
      └────────────────┼────────────────┘
                       │
                       ▼
                  EMI Module
                       │
                       ▼
                 Weather State
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
Digital Twin     Digital Earth     Vision
   Bridge            Bridge         Bridge
        │
        ├──────────────┐
        ▼              ▼
Navigation Bridge   LiDAR Bridge
```

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

