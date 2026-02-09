# Pipe Simulation App - UML Architecture

## Class Diagram

```mermaid
classDiagram
    %% Core Models
    class Node {
        -id: str
        -pressure: float | None
        -flow_rate: float | None
        -elevation: float
        -is_source: bool
        -is_sink: bool
        -is_pump: bool
        -is_valve: bool
        -pressure_ratio: float | None
        -valve_k: float | None
    }

    class Pipe {
        -id: str
        -start_node: str
        -end_node: str
        -length: float
        -diameter: float
        -roughness: float
        -flow_rate: float | None
        -liquid_flow_rate: float | None
        -gas_flow_rate: float | None
        -pressure_drop: float | None
        -pump_curve: PumpCurve | None
        -valve: Valve | None
        +area() float
    }

    class PipeNetwork {
        -nodes: dict[str, Node]
        -pipes: dict[str, Pipe]
        +add_node(node: Node)
        +add_pipe(pipe: Pipe)
        +get_outgoing_pipes(node_id: str)
        +get_incoming_pipes(node_id: str)
    }

    %% Equipment Models
    class PumpCurve {
        -a: float
        -b: float
        -c: float
        +pressure_gain(flow_rate: float) float
    }

    class Valve {
        -k: float
        +pressure_drop(rho: float, velocity: float) float
    }

    class Fluid {
        -density: float
        -viscosity: float
        -is_multiphase: bool
        -liquid_density: float
        -gas_density: float
        -liquid_viscosity: float
        -gas_viscosity: float
        -surface_tension: float
    }

    %% Services - Pressure Drop Components
    class FlowProperties {
    }

    class SinglePhasePressureDrop {
        -flow: FlowProperties
        +calculate(pipe: Pipe, fluid: Fluid) float
    }

    class MultiPhasePressureDrop {
        -flow: FlowProperties
        +calculate(pipe: Pipe, fluid: Fluid) float
    }

    class NodePressureGain {
        +calculate(node, inlet_pressure: float) float
    }

    class PressureDropService {
        -fluid: Fluid
        -flow: FlowProperties
        -single_phase: SinglePhasePressureDrop
        -multi_phase: MultiPhasePressureDrop
        -node_gain: NodePressureGain
        +calculate_pipe_dp(pipe: Pipe) float
        +calculate_multiphase_dp(pipe: Pipe) float
        +valve_loss(k: float, pipe: Pipe) float
        +calculate_node_pressure_gain(node, inlet_pressure: float) float
    }

    %% Services - Solver Components
    class CycleFinder {
        +find_cycles(network: PipeNetwork) list
    }

    class HardyCrossSolver {
        -dp_service: PressureDropService
        +apply(network: PipeNetwork, cycles: list)
    }

    class PressurePropagation {
        -dp_service: PressureDropService
        +propagate(network: PipeNetwork)
    }

    class NetworkPressureSolver {
        -dp_service: PressureDropService
        -cycle_finder: CycleFinder
        -hardy_cross: HardyCrossSolver
        -propagator: PressurePropagation
        +solve(network: PipeNetwork)
    }

    %% Controller
    class MainController {
        -scene: Scene
        -fluid: Fluid
        +set_fluid(fluid: Fluid)
        +build_network_from_scene() PipeNetwork
        +run_network_simulation() PipeNetwork
    }

    %% Relationships
    PipeNetwork --> Node: contains
    PipeNetwork --> Pipe: contains
    Pipe --> PumpCurve: uses
    Pipe --> Valve: uses
    PressureDropService --> Fluid: uses
    PressureDropService --> FlowProperties: uses
    PressureDropService --> SinglePhasePressureDrop: uses
    PressureDropService --> MultiPhasePressureDrop: uses
    PressureDropService --> NodePressureGain: uses
    NetworkPressureSolver --> PressureDropService: uses
    NetworkPressureSolver --> CycleFinder: uses
    NetworkPressureSolver --> HardyCrossSolver: uses
    NetworkPressureSolver --> PressurePropagation: uses
    HardyCrossSolver --> PressureDropService: uses
    PressurePropagation --> PressureDropService: uses
    MainController --> PipeNetwork: creates
    MainController --> Fluid: manages
    MainController --> PressureDropService: creates
    MainController --> NetworkPressureSolver: creates
```

## Architecture Overview

### Core Layers

**Data Models Layer** (`app/models/`)
- `Node`: Represents network nodes (sources, sinks, pumps, valves)
- `Pipe`: Represents pipes with flow and equipment properties
- `PumpCurve`: Quadratic pump performance model
- `Valve`: Valve loss coefficient model
- `Fluid`: Single-phase and multi-phase fluid properties

**Network Layer** (`app/map/`)
- `PipeNetwork`: Graph structure managing nodes and pipes
- Provides connectivity queries (incoming/outgoing pipes)

**Service Layer** (`app/services/`)

1. **Pressure Drop Service**
   - `FlowProperties`: Base flow calculation properties
   - `SinglePhasePressureDrop`: Single-phase pressure drop calculation
   - `MultiPhasePressureDrop`: Multi-phase flow pressure drop
   - `NodePressureGain`: Pump and valve pressure changes
   - `PressureDropService`: Orchestrates all pressure drop calculations

2. **Solver Service**
   - `CycleFinder`: Identifies loops in network
   - `HardyCrossSolver`: Iterative solver for looped networks
   - `PressurePropagation`: Propagates pressures through tree networks
   - `NetworkPressureSolver`: Orchestrates the complete solving process

**Controller Layer** (`app/controllers/`)
- `MainController`: Bridges UI and simulation
  - Builds network from UI scene
  - Manages fluid properties
  - Orchestrates simulation execution

## Data Flow

```
User Input (UI Scene)
    ↓
MainController.build_network_from_scene()
    ↓
PipeNetwork (in-memory graph)
    ↓
MainController.run_network_simulation()
    ↓
NetworkPressureSolver.solve()
    ├→ CycleFinder.find_cycles()
    ├→ HardyCrossSolver.apply() [if cycles exist]
    └→ PressurePropagation.propagate()
    ↓
Simulation Results
    ↓
Results View (UI Display)
```

## Key Design Patterns

- **Dependency Injection**: Services receive dependencies via constructor
- **Separation of Concerns**: UI, models, services, and solving are isolated
- **Graph Processing**: Network represented as adjacency dict for efficiency
- **Component-based Architecture**: Pressure drop calculations modularized
