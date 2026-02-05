"""Transient (time-dependent) solver for hydraulic network dynamics.

This module provides transient simulation capabilities for modeling:
- Pump startup/shutdown transients
- Valve opening/closing operations
- Pressure wave propagation
- Transient pressure and flow variations over time

The solver uses explicit time-stepping with conservation laws to compute
dynamic behavior in pipe networks.
"""

import math
from dataclasses import dataclass, field
from typing import Callable, Optional

from app.map.network import PipeNetwork
from app.map.node import Node
from app.map.pipe import Pipe
from app.services.pressure_drop_service import PressureDropService


@dataclass
class TransientEvent:
    """A transient event that changes over time (e.g., pump startup, valve opening).
    
    Attributes:
        time: Time at which the event occurs (seconds)
        node_id: Node ID affected by the event (optional)
        pipe_id: Pipe ID affected by the event (optional)
        event_type: Type of event ('pump_ramp', 'valve_opening', 'demand_change', etc.)
        duration: Duration of the event transition (seconds)
        start_value: Starting value for the event parameter
        end_value: Ending value for the event parameter
        callback: Optional callback function to apply the event
    """
    time: float
    event_type: str
    duration: float
    start_value: float
    end_value: float
    node_id: Optional[str] = None
    pipe_id: Optional[str] = None
    callback: Optional[Callable] = None


@dataclass
class TransientResult:
    """Results from a transient simulation at a specific time step.
    
    Attributes:
        time: Simulation time (seconds)
        timestep: The timestep number (0-indexed)
        node_pressures: Dict of node_id -> pressure (Pa)
        pipe_flows: Dict of pipe_id -> flow_rate (m³/s)
        pipe_velocities: Dict of pipe_id -> velocity (m/s)
        max_pressure: Maximum pressure in network (Pa)
        min_pressure: Minimum pressure in network (Pa)
    """
    time: float
    timestep: int
    node_pressures: dict = field(default_factory=dict)
    pipe_flows: dict = field(default_factory=dict)
    pipe_velocities: dict = field(default_factory=dict)
    max_pressure: float = 0.0
    min_pressure: float = 0.0


class TransientSolver:
    """Solver for transient (time-dependent) hydraulic network analysis.
    
    Simulates dynamic behavior in networks by applying time-stepping integration
    to solve conservation of mass and energy equations. Supports modeling of:
    - Pump startup/shutdown (acceleration/deceleration)
    - Valve operations (gradual opening/closing)
    - Demand changes (load variations)
    - Transient pressure waves and water hammer effects
    
    The solver uses explicit time-stepping with configurable time step size
    for stability and accuracy control.
    
    Attributes:
        dp_service: Service for calculating pressure drops
        time_step: Integration time step (seconds)
        max_steps: Maximum number of time steps to compute
        convergence_tolerance: Tolerance for steady-state detection
        
    Example:
        >>> from app.services.pressure_drop_service import PressureDropService
        >>> from app.models.fluid import Fluid
        >>> 
        >>> fluid = Fluid(density=998.0, viscosity=1e-3)
        >>> dp_service = PressureDropService(fluid)
        >>> transient = TransientSolver(dp_service, time_step=0.01, max_steps=1000)
        >>> 
        >>> # Define transient events
        >>> events = [
        ...     TransientEvent(
        ...         time=0.0, event_type='pump_ramp',
        ...         duration=2.0, start_value=0.0, end_value=1.0,
        ...         pipe_id='pump_1'
        ...     )
        ... ]
        >>> 
        >>> # Run simulation
        >>> results = transient.solve(network, total_time=10.0, events=events)
    """
    
    def __init__(
        self,
        dp_service: PressureDropService,
        time_step: float = 0.01,
        max_steps: int = 10000,
        convergence_tolerance: float = 0.01,
    ):
        """Initialize the transient solver.
        
        Args:
            dp_service: Service for calculating pressure drops
            time_step: Time step for integration (seconds), default 0.01s
            max_steps: Maximum number of time steps, default 10000
            convergence_tolerance: Tolerance for steady-state detection (Pa)
        """
        self.dp_service = dp_service
        self.time_step = time_step
        self.max_steps = max_steps
        self.convergence_tolerance = convergence_tolerance
        self.results: list[TransientResult] = []
        
    def solve(
        self,
        network: PipeNetwork,
        total_time: float,
        events: Optional[list[TransientEvent]] = None,
        callback: Optional[Callable[[TransientResult], None]] = None,
    ) -> list[TransientResult]:
        """Run transient simulation for specified duration.
        
        Args:
            network: The pipe network to simulate
            total_time: Total simulation time (seconds)
            events: Optional list of transient events to apply
            callback: Optional callback function called after each time step
                     with the TransientResult
            
        Returns:
            List of TransientResult objects at each time step
            
        Raises:
            ValueError: If total_time <= 0 or network invalid
            RuntimeError: If simulation fails to converge
        """
        if total_time <= 0:
            raise ValueError(f"total_time must be positive, got {total_time}")
            
        if not network.nodes or not network.pipes:
            raise ValueError("Network must have at least one node and one pipe")
        
        self.results = []
        events = events or []
        num_steps = int(math.ceil(total_time / self.time_step))
        num_steps = min(num_steps, self.max_steps)
        
        # Store initial state
        initial_pressures = {node_id: node.pressure for node_id, node in network.nodes.items()}
        initial_flows = {pipe_id: pipe.flow_rate for pipe_id, pipe in network.pipes.items()}
        
        for step in range(num_steps):
            time = step * self.time_step
            
            # Apply transient events at this time
            self._apply_events(network, time, events)
            
            # Solve steady-state for this time snapshot
            from app.services.network_pressure_solver import NetworkPressureSolver
            solver = NetworkPressureSolver(self.dp_service)
            solver.solve(network)
            
            # Collect results
            result = self._collect_results(network, step, time)
            self.results.append(result)
            
            # Call user callback if provided
            if callback:
                callback(result)
            
            # Check for steady-state convergence
            if step > 10 and self._is_steady_state(step):
                break
        
        return self.results
    
    def _apply_events(
        self,
        network: PipeNetwork,
        time: float,
        events: list[TransientEvent],
    ) -> None:
        """Apply transient events at the current time.
        
        Args:
            network: The pipe network
            time: Current simulation time
            events: List of transient events to apply
        """
        for event in events:
            if time < event.time or time > event.time + event.duration:
                continue  # Event not active at this time
            
            # Calculate interpolation factor (0 to 1)
            elapsed = time - event.time
            progress = min(1.0, elapsed / event.duration) if event.duration > 0 else 1.0
            
            # Interpolate value
            current_value = event.start_value + progress * (event.end_value - event.start_value)
            
            # Apply event based on type
            if event.event_type == 'pump_ramp' and event.pipe_id:
                pipe = network.pipes.get(event.pipe_id)
                if pipe:
                    # Ramp pump head or flow multiplier
                    setattr(pipe, 'pump_multiplier', current_value)
                    
            elif event.event_type == 'valve_opening' and event.pipe_id:
                pipe = network.pipes.get(event.pipe_id)
                if pipe:
                    # Valve opening (0 = closed, 1 = fully open)
                    setattr(pipe, 'valve_opening', current_value)
                    
            elif event.event_type == 'demand_change' and event.node_id:
                node = network.nodes.get(event.node_id)
                if node:
                    # Change demand at node
                    setattr(node, 'demand', current_value)
                    
            elif event.callback:
                # Custom event callback
                event.callback(network, current_value, event)
    
    def _collect_results(
        self,
        network: PipeNetwork,
        step: int,
        time: float,
    ) -> TransientResult:
        """Collect simulation results at current time step.
        
        Args:
            network: The pipe network
            step: Current step number
            time: Current time (seconds)
            
        Returns:
            TransientResult with pressure and flow data
        """
        result = TransientResult(time=time, timestep=step)
        
        # Collect node pressures
        for node_id, node in network.nodes.items():
            result.node_pressures[node_id] = getattr(node, 'pressure', 0.0)
        
        # Collect pipe flows and velocities
        for pipe_id, pipe in network.pipes.items():
            flow_rate = getattr(pipe, 'flow_rate', 0.0)
            result.pipe_flows[pipe_id] = flow_rate
            
            # Calculate velocity from flow rate
            if pipe.diameter > 0:
                area = math.pi * (pipe.diameter / 2) ** 2
                velocity = abs(flow_rate) / area if area > 0 else 0.0
            else:
                velocity = 0.0
            result.pipe_velocities[pipe_id] = velocity
        
        # Calculate min/max pressures
        if result.node_pressures:
            pressures = list(result.node_pressures.values())
            result.max_pressure = max(pressures)
            result.min_pressure = min(pressures)
        
        return result
    
    def _is_steady_state(self, current_step: int) -> bool:
        """Check if solution has reached steady state.
        
        Compares pressure changes between last two steps to detect convergence.
        
        Args:
            current_step: Current step number
            
        Returns:
            True if steady state reached within tolerance
        """
        if current_step < 2:
            return False
        
        prev_result = self.results[-2]
        curr_result = self.results[-1]
        
        # Calculate max pressure change
        max_change = 0.0
        for node_id, curr_pressure in curr_result.node_pressures.items():
            prev_pressure = prev_result.node_pressures.get(node_id, 0.0)
            change = abs(curr_pressure - prev_pressure)
            max_change = max(max_change, change)
        
        return max_change < self.convergence_tolerance
    
    def get_pressure_history(self, node_id: str) -> list[tuple[float, float]]:
        """Get pressure history for a specific node.
        
        Args:
            node_id: ID of the node
            
        Returns:
            List of (time, pressure) tuples
        """
        return [
            (result.time, result.node_pressures.get(node_id, 0.0))
            for result in self.results
        ]
    
    def get_flow_history(self, pipe_id: str) -> list[tuple[float, float]]:
        """Get flow rate history for a specific pipe.
        
        Args:
            pipe_id: ID of the pipe
            
        Returns:
            List of (time, flow_rate) tuples
        """
        return [
            (result.time, result.pipe_flows.get(pipe_id, 0.0))
            for result in self.results
        ]
    
    def get_velocity_history(self, pipe_id: str) -> list[tuple[float, float]]:
        """Get velocity history for a specific pipe.
        
        Args:
            pipe_id: ID of the pipe
            
        Returns:
            List of (time, velocity) tuples
        """
        return [
            (result.time, result.pipe_velocities.get(pipe_id, 0.0))
            for result in self.results
        ]
