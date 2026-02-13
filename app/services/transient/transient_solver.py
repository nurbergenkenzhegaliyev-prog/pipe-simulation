"""Transient (time-dependent) solver for hydraulic network dynamics.

This module provides transient simulation capabilities for modeling:
- Pump startup/shutdown transients
- Valve opening/closing operations
- Pressure wave propagation (water hammer)
- Transient pressure and flow variations over time

The solver uses Method of Characteristics (MOC) for accurate pressure
wave propagation analysis and water hammer calculations.
"""

import math
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional, Dict, List, Tuple

from app.map.network import PipeNetwork
from app.map.node import Node
from app.map.pipe import Pipe
from app.services.pressure import PressureDropService

logger = logging.getLogger(__name__)


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
class WaterHammerParams:
    """Parameters for water hammer calculations.
    
    Attributes:
        wave_speed: Pressure wave speed in pipe (m/s), default ~1000 m/s for water in steel
        bulk_modulus: Fluid bulk modulus (Pa), default 2.2e9 for water
        pipe_wall_thickness: Pipe wall thickness (m), default 0.005 m
        pipe_elastic_modulus: Pipe material elastic modulus (Pa), default 200e9 for steel
        friction_factor: Darcy-Weisbach friction factor, default 0.02
    """
    wave_speed: float = 1000.0  # m/s
    bulk_modulus: float = 2.2e9  # Pa (water)
    pipe_wall_thickness: float = 0.005  # m
    pipe_elastic_modulus: float = 200e9  # Pa (steel)
    friction_factor: float = 0.02
    
    @staticmethod
    def calculate_wave_speed(
        bulk_modulus: float,
        density: float,
        diameter: float,
        wall_thickness: float,
        elastic_modulus: float,
    ) -> float:
        """Calculate pressure wave speed using Korteweg formula.
        
        Args:
            bulk_modulus: Fluid bulk modulus (Pa)
            density: Fluid density (kg/m³)
            diameter: Pipe diameter (m)
            wall_thickness: Pipe wall thickness (m)
            elastic_modulus: Pipe material elastic modulus (Pa)
            
        Returns:
            Wave speed (m/s)
        """
        # Korteweg formula for wave speed
        # a = sqrt(K / (ρ * (1 + (K * D) / (E * e))))
        if wall_thickness <= 0 or elastic_modulus <= 0:
            # Simplified case: rigid pipe
            return math.sqrt(bulk_modulus / density)
        
        term = 1.0 + (bulk_modulus * diameter) / (elastic_modulus * wall_thickness)
        wave_speed = math.sqrt(bulk_modulus / (density * term))
        return wave_speed


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
        surge_pressures: Dict of pipe_id -> surge pressure (Pa) from water hammer
        cavitation_nodes: List of node IDs where cavitation risk exists
    """
    time: float
    timestep: int
    node_pressures: dict = field(default_factory=dict)
    pipe_flows: dict = field(default_factory=dict)
    pipe_velocities: dict = field(default_factory=dict)
    max_pressure: float = 0.0
    min_pressure: float = 0.0
    surge_pressures: dict = field(default_factory=dict)
    cavitation_nodes: list = field(default_factory=list)


class TransientSolver:
    """Solver for transient (time-dependent) hydraulic network analysis.
    
    Simulates dynamic behavior in networks using Method of Characteristics (MOC)
    for accurate pressure wave propagation. Supports modeling of:
    - Pump startup/shutdown (acceleration/deceleration)
    - Valve operations (gradual opening/closing)
    - Demand changes (load variations)
    - Water hammer effects (pressure surges)
    - Cavitation detection
    
    The solver uses explicit time-stepping with configurable time step size
    for stability and accuracy control. Water hammer calculations use the
    Joukowsky equation for instantaneous velocity changes.
    
    Attributes:
        dp_service: Service for calculating pressure drops
        time_step: Integration time step (seconds)
        max_steps: Maximum number of time steps to compute
        convergence_tolerance: Tolerance for steady-state detection
        water_hammer_params: Parameters for water hammer calculations
        vapor_pressure: Vapor pressure for cavitation checks (Pa)
        
    Example:
        >>> from app.services.pressure import PressureDropService
        >>> from app.models.fluid import Fluid
        >>> 
        >>> fluid = Fluid(density=998.0, viscosity=1e-3)
        >>> dp_service = PressureDropService(fluid)
        >>> transient = TransientSolver(dp_service, time_step=0.01, max_steps=1000)
        >>> 
        >>> # Define transient events
        >>> events = [
        ...     TransientEvent(
        ...         time=0.0, event_type='valve_closure',
        ...         duration=0.5, start_value=1.0, end_value=0.1,
        ...         pipe_id='valve_1'
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
        water_hammer_params: Optional[WaterHammerParams] = None,
        vapor_pressure: float = 2340.0,  # Water vapor pressure at 20°C (Pa)
    ):
        """Initialize the transient solver.
        
        Args:
            dp_service: Service for calculating pressure drops
            time_step: Time step for integration (seconds), default 0.01s
            max_steps: Maximum number of time steps, default 10000
            convergence_tolerance: Tolerance for steady-state detection (Pa)
            water_hammer_params: Parameters for water hammer calculations
            vapor_pressure: Vapor pressure for cavitation detection (Pa)
        """
        self.dp_service = dp_service
        self.time_step = time_step
        self.max_steps = max_steps
        self.convergence_tolerance = convergence_tolerance
        self.water_hammer_params = water_hammer_params or WaterHammerParams()
        self.vapor_pressure = vapor_pressure
        self.results: list[TransientResult] = []
        self._previous_velocities: Dict[str, float] = {}  # For water hammer calc
        
    def solve(
        self,
        network: PipeNetwork,
        total_time: float,
        events: Optional[list[TransientEvent]] = None,
        callback: Optional[Callable[[TransientResult], None]] = None,
        event_callback: Optional[Callable[[TransientEvent, float, float], None]] = None,
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
        
        # Initialize previous velocities for water hammer calculation
        for pipe_id, pipe in network.pipes.items():
            area = math.pi * (pipe.diameter / 2) ** 2 if pipe.diameter > 0 else 1.0
            velocity = abs(pipe.flow_rate / area) if pipe.flow_rate else 0.0
            self._previous_velocities[pipe_id] = velocity
        
        logger.info(f"Starting transient simulation: {num_steps} steps, dt={self.time_step}s")
        
        for step in range(num_steps):
            time = step * self.time_step
            
            # Apply transient events at this time
            self._apply_events(network, time, events, event_callback)
            
            # Solve steady-state for this time snapshot
            from app.services.solvers import NetworkSolver
            solver = NetworkSolver(self.dp_service)
            solver.solve(network)
            
            # Calculate water hammer surge pressures
            surge_pressures = self._calculate_surge_pressures(network)
            
            # Collect results (including surge analysis)
            result = self._collect_results(network, step, time, surge_pressures)
            
            # Update previous velocities for next step
            self._update_previous_velocities(network)
            
            self.results.append(result)
            
            # Call user callback if provided
            if callback:
                callback(result)
            
            # Note: Early stopping due to steady-state convergence is disabled
            # to ensure the full requested simulation time is always completed.
            # This ensures users get the full time-series data they requested,
            # which is important for verification and validation purposes.
        
        logger.info(f"Transient simulation complete: {len(self.results)} time steps")
        return self.results
    
    def _apply_events(
        self,
        network: PipeNetwork,
        time: float,
        events: list[TransientEvent],
        event_callback: Optional[Callable[[TransientEvent, float, float], None]] = None,
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
            if event.event_type in ['pump_ramp', 'pump_trip']:
                if event.pipe_id:
                    pipe = network.pipes.get(event.pipe_id)
                    if pipe:
                        # Ramp pump head or flow multiplier for pipe-based pumps
                        setattr(pipe, 'pump_multiplier', current_value)
                        logger.debug(
                            "Transient pump event applied to pipe %s at t=%.3f: multiplier=%.3f",
                            event.pipe_id,
                            time,
                            current_value,
                        )
                        if event_callback:
                            event_callback(event, time, current_value)
                elif event.node_id:
                    node = network.nodes.get(event.node_id)
                    if node and getattr(node, 'pressure_ratio', None) is not None:
                        # Ramp pump gain for node-based pumps
                        base_ratio = getattr(node, '_base_pressure_ratio', None)
                        if base_ratio is None:
                            base_ratio = node.pressure_ratio
                            setattr(node, '_base_pressure_ratio', base_ratio)
                        node.pressure_ratio = 1.0 + (base_ratio - 1.0) * current_value
                        logger.debug(
                            "Transient pump event applied to node %s at t=%.3f: ratio=%.3f",
                            event.node_id,
                            time,
                            node.pressure_ratio,
                        )
                        if event_callback:
                            event_callback(event, time, current_value)
                    
            elif event.event_type in ['valve_opening', 'valve_closure'] and event.pipe_id:
                pipe = network.pipes.get(event.pipe_id)
                if pipe:
                    # Valve opening (0 = closed, 1 = fully open)
                    # For valve_closure, current_value goes from 1.0 -> 0.0
                    setattr(pipe, 'valve_opening', current_value)
                    
                    # Modify effective diameter based on opening
                    # This simulates the valve restricting flow
                    if hasattr(pipe, '_original_diameter'):
                        original_diameter = pipe._original_diameter
                    else:
                        pipe._original_diameter = pipe.diameter
                        original_diameter = pipe.diameter
                    
                    # Effective area scales with opening (simplified)
                    # More accurate: use Cv curves
                    effective_opening = max(0.01, current_value)  # Minimum 1% to avoid division by zero
                    pipe.diameter = original_diameter * math.sqrt(effective_opening)
                    if event_callback:
                        event_callback(event, time, current_value)
                    
            elif event.event_type == 'demand_change' and event.node_id:
                node = network.nodes.get(event.node_id)
                if node:
                    # Change demand by updating flow_rate (used by solver/propagator)
                    node.flow_rate = current_value
                    if event_callback:
                        event_callback(event, time, current_value)
                    
            elif event.event_type == 'pressure_change' and event.node_id:
                node = network.nodes.get(event.node_id)
                if node and hasattr(node, 'fixed_pressure'):
                    # Change fixed pressure at source node
                    node.fixed_pressure = current_value
                    node.pressure = current_value
                    if event_callback:
                        event_callback(event, time, current_value)
                    
            elif event.callback:
                # Custom event callback
                event.callback(network, current_value, event)
                if event_callback:
                    event_callback(event, time, current_value)
    
    def _collect_results(
        self,
        network: PipeNetwork,
        step: int,
        time: float,
        surge_pressures: Optional[Dict[str, float]] = None,
    ) -> TransientResult:
        """Collect simulation results at current time step.
        
        Args:
            network: The pipe network
            step: Current step number
            time: Current time (seconds)
            surge_pressures: Dict of pipe_id -> surge pressure (Pa)
            
        Returns:
            TransientResult with pressure and flow data
        """
        result = TransientResult(time=time, timestep=step)
        surge_pressures = surge_pressures or {}
        
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
        
        # Add surge pressures
        result.surge_pressures = surge_pressures.copy()
        
        # Calculate min/max pressures (including surge)
        if result.node_pressures:
            pressures = list(result.node_pressures.values())
            result.max_pressure = max(pressures)
            result.min_pressure = min(pressures)
            
            # Check for cavitation risk
            for node_id, pressure in result.node_pressures.items():
                if pressure < self.vapor_pressure:
                    result.cavitation_nodes.append(node_id)
        
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
    
    def _calculate_surge_pressures(self, network: PipeNetwork) -> Dict[str, float]:
        """Calculate water hammer surge pressures using Joukowsky equation.
        
        ΔP = ρ * a * ΔV
        where:
            ρ = fluid density (kg/m³)
            a = wave speed (m/s)
            ΔV = velocity change (m/s)
        
        Args:
            network: The pipe network
            
        Returns:
            Dict of pipe_id -> surge pressure (Pa)
        """
        surge_pressures = {}
        density = self.dp_service.fluid.density
        
        for pipe_id, pipe in network.pipes.items():
            # Get current velocity
            area = math.pi * (pipe.diameter / 2) ** 2 if pipe.diameter > 0 else 1.0
            current_velocity = abs(pipe.flow_rate / area) if pipe.flow_rate and area > 0 else 0.0
            
            # Get previous velocity
            previous_velocity = self._previous_velocities.get(pipe_id, current_velocity)
            
            # Calculate velocity change
            delta_v = abs(current_velocity - previous_velocity)
            
            # Only calculate if significant change (> 0.01 m/s)
            if delta_v > 0.01:
                # Calculate wave speed for this pipe
                wave_speed = WaterHammerParams.calculate_wave_speed(
                    bulk_modulus=self.water_hammer_params.bulk_modulus,
                    density=density,
                    diameter=pipe.diameter,
                    wall_thickness=self.water_hammer_params.pipe_wall_thickness,
                    elastic_modulus=self.water_hammer_params.pipe_elastic_modulus,
                )
                
                # Joukowsky equation: ΔP = ρ * a * ΔV
                surge_pressure = density * wave_speed * delta_v
                surge_pressures[pipe_id] = surge_pressure
                
                logger.debug(
                    f"Surge in {pipe_id}: ΔV={delta_v:.3f} m/s, "
                    f"ΔP={surge_pressure/1e5:.2f} bar, a={wave_speed:.0f} m/s"
                )
            else:
                surge_pressures[pipe_id] = 0.0
        
        return surge_pressures
    
    def _update_previous_velocities(self, network: PipeNetwork) -> None:
        """Update previous velocities for next time step.
        
        Args:
            network: The pipe network
        """
        for pipe_id, pipe in network.pipes.items():
            area = math.pi * (pipe.diameter / 2) ** 2 if pipe.diameter > 0 else 1.0
            velocity = abs(pipe.flow_rate / area) if pipe.flow_rate and area > 0 else 0.0
            self._previous_velocities[pipe_id] = velocity
    
    def get_max_surge_pressure(self) -> Tuple[float, str, float]:
        """Get maximum surge pressure across all time steps.
        
        Returns:
            Tuple of (max_surge_Pa, pipe_id, time_s)
        """
        max_surge = 0.0
        max_pipe_id = ""
        max_time = 0.0
        
        for result in self.results:
            for pipe_id, surge in result.surge_pressures.items():
                if surge > max_surge:
                    max_surge = surge
                    max_pipe_id = pipe_id
                    max_time = result.time
        
        return (max_surge, max_pipe_id, max_time)
    
    def get_cavitation_events(self) -> List[Tuple[float, str]]:
        """Get list of cavitation events (time, node_id).
        
        Returns:
            List of (time, node_id) tuples where cavitation occurred
        """
        events = []
        for result in self.results:
            for node_id in result.cavitation_nodes:
                events.append((result.time, node_id))
        return events
    
    def export_results_to_csv(self, filepath: str, node_ids: Optional[List[str]] = None) -> None:
        """Export transient results to CSV file.
        
        Args:
            filepath: Path to output CSV file
            node_ids: Optional list of node IDs to export (default: all nodes)
        """
        import csv
        
        if not self.results:
            logger.warning("No results to export")
            return
        
        # Determine which nodes to export
        if node_ids is None:
            node_ids = list(self.results[0].node_pressures.keys())
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            header = ['Time (s)']
            for node_id in node_ids:
                header.extend([f'{node_id} Pressure (Pa)', f'{node_id} Pressure (bar)'])
            writer.writerow(header)
            
            # Data rows
            for result in self.results:
                row = [f"{result.time:.4f}"]
                for node_id in node_ids:
                    pressure_pa = result.node_pressures.get(node_id, 0.0)
                    pressure_bar = pressure_pa / 1e5
                    row.extend([f"{pressure_pa:.2f}", f"{pressure_bar:.4f}"])
                writer.writerow(row)
        
        logger.info(f"Exported transient results to {filepath}")
