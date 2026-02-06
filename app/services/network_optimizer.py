"""Network optimization solver for hydraulic systems.

This module provides optimization capabilities to:
- Minimize pump power consumption
- Balance flow rates across parallel paths
- Satisfy pressure/flow constraints
- Optimize pipe sizing
- Find optimal pump operating points

Uses scipy.optimize for constraint-based optimization.
"""

import math
from dataclasses import dataclass, field
from typing import Callable, Optional
from enum import Enum

import numpy as np
from scipy.optimize import minimize, LinearConstraint, Bounds

from app.map.network import PipeNetwork
from app.services.pressure import PressureDropService
from app.services.solvers import NetworkSolver


class ObjectiveType(Enum):
    """Types of optimization objectives."""
    MINIMIZE_POWER = "minimize_power"
    MINIMIZE_PRESSURE = "minimize_pressure"
    BALANCE_FLOWS = "balance_flows"
    MINIMIZE_PIPE_COST = "minimize_pipe_cost"


@dataclass
class OptimizationConstraint:
    """A constraint for network optimization.
    
    Attributes:
        constraint_type: Type of constraint ('pressure', 'flow', 'velocity')
        node_id: Node affected (for pressure constraints)
        pipe_id: Pipe affected (for flow/velocity constraints)
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        priority: Priority level (1=critical, 2=important, 3=optional)
    """
    constraint_type: str  # 'pressure', 'flow', 'velocity'
    min_value: float
    max_value: float
    node_id: Optional[str] = None
    pipe_id: Optional[str] = None
    priority: int = 2  # 1=critical, 2=important, 3=optional


@dataclass
class OptimizationResult:
    """Results from network optimization.
    
    Attributes:
        success: Whether optimization converged
        iterations: Number of iterations performed
        objective_value: Final objective function value
        improvement_percent: Percentage improvement vs baseline
        constraints_satisfied: Dict of constraint satisfaction status
        optimized_flows: Dict of pipe_id -> optimized flow rate
        optimized_pressures: Dict of node_id -> optimized pressure
        message: Optimization status message
    """
    success: bool
    iterations: int
    objective_value: float
    improvement_percent: float
    constraints_satisfied: dict = field(default_factory=dict)
    optimized_flows: dict = field(default_factory=dict)
    optimized_pressures: dict = field(default_factory=dict)
    message: str = ""


class NetworkOptimizer:
    """Optimizer for hydraulic network design and operation.
    
    Provides methods to optimize network parameters subject to constraints:
    - Minimize pump power consumption
    - Balance flows across parallel pipes
    - Meet pressure/velocity requirements
    - Optimize pump operating points
    
    Uses SciPy's constrained optimization algorithms.
    
    Attributes:
        dp_service: Pressure drop service for calculations
        solver: Network pressure solver
        
    Example:
        >>> from app.services.pressure_drop_service import PressureDropService
        >>> from app.models.fluid import Fluid
        >>> 
        >>> fluid = Fluid(density=998.0, viscosity=1e-3)
        >>> dp_service = PressureDropService(fluid)
        >>> optimizer = NetworkOptimizer(dp_service)
        >>> 
        >>> # Define constraints
        >>> constraints = [
        ...     OptimizationConstraint(
        ...         constraint_type='velocity',
        ...         pipe_id='main_pipe',
        ...         min_value=0.5,
        ...         max_value=2.5
        ...     )
        ... ]
        >>> 
        >>> # Optimize for minimum power
        >>> result = optimizer.optimize(
        ...     network,
        ...     objective=ObjectiveType.MINIMIZE_POWER,
        ...     constraints=constraints
        ... )
    """
    
    def __init__(
        self,
        dp_service: PressureDropService,
        solver: Optional[NetworkPressureSolver] = None,
    ):
        """Initialize the network optimizer.
        
        Args:
            dp_service: Pressure drop service for calculations
            solver: Optional custom network solver (default: NetworkPressureSolver)
        """
        self.dp_service = dp_service
        self.solver = solver or NetworkPressureSolver(dp_service)
        self.last_result: Optional[OptimizationResult] = None
        self._baseline_pump_flows: Optional[dict[str, float]] = None
        
    def optimize(
        self,
        network: PipeNetwork,
        objective: ObjectiveType = ObjectiveType.MINIMIZE_POWER,
        constraints: Optional[list[OptimizationConstraint]] = None,
        pump_ids: Optional[list[str]] = None,
        max_iterations: int = 100,
        tolerance: float = 1e-6,
    ) -> OptimizationResult:
        """Optimize network for specified objective and constraints.
        
        Args:
            network: The pipe network to optimize
            objective: Optimization objective (default: minimize pump power)
            constraints: List of constraints to satisfy
            pump_ids: List of pump pipe IDs to optimize (default: all pumps)
            max_iterations: Maximum optimization iterations
            tolerance: Optimization tolerance
            
        Returns:
            OptimizationResult with optimized parameters
            
        Raises:
            ValueError: If network invalid or optimization fails
        """
        if not network.nodes or not network.pipes:
            raise ValueError("Network must have at least one node and one pipe")
        
        constraints = constraints or []
        
        # Identify pump pipes if not specified
        if pump_ids is None:
            pump_ids = [
                p_id for p_id, pipe in network.pipes.items()
                if pipe.pump_curve is not None
            ]
        
        # Baseline: solve without optimization
        self.solver.solve(network)
        baseline_power = self._calculate_total_power(network, pump_ids)
        baseline_values = self._extract_network_values(network)
        self._baseline_pump_flows = {
            pump_id: (network.pipes[pump_id].flow_rate or 0.0)
            for pump_id in pump_ids
            if pump_id in network.pipes
        }
        
        # Set up optimization problem
        initial_values = self._extract_pump_parameters(network, pump_ids)
        
        def objective_func(x):
            """Objective function to minimize."""
            self._apply_pump_parameters(network, pump_ids, x)
            self.solver.solve(network)
            
            if objective == ObjectiveType.MINIMIZE_POWER:
                return self._calculate_total_power(network, pump_ids)
            elif objective == ObjectiveType.MINIMIZE_PRESSURE:
                return self._calculate_max_pressure(network)
            elif objective == ObjectiveType.BALANCE_FLOWS:
                return self._calculate_flow_balance_cost(network)
            else:
                return 0.0
        
        def constraint_func(x, constraint: OptimizationConstraint) -> float:
            """Constraint satisfaction function."""
            self._apply_pump_parameters(network, pump_ids, x)
            self.solver.solve(network)
            
            if constraint.constraint_type == 'pressure' and constraint.node_id:
                node = network.nodes.get(constraint.node_id)
                if node:
                    pressure = getattr(node, 'pressure', 0.0)
                    if pressure < constraint.min_value:
                        return constraint.min_value - pressure  # Penalty
                    if pressure > constraint.max_value:
                        return pressure - constraint.max_value  # Penalty
                    
            elif constraint.constraint_type == 'flow' and constraint.pipe_id:
                pipe = network.pipes.get(constraint.pipe_id)
                if pipe:
                    flow = getattr(pipe, 'flow_rate', 0.0)
                    if flow < constraint.min_value:
                        return constraint.min_value - flow
                    if flow > constraint.max_value:
                        return flow - constraint.max_value
                        
            elif constraint.constraint_type == 'velocity' and constraint.pipe_id:
                pipe = network.pipes.get(constraint.pipe_id)
                if pipe and pipe.diameter > 0:
                    flow = getattr(pipe, 'flow_rate', 0.0)
                    area = math.pi * (pipe.diameter / 2) ** 2
                    velocity = abs(flow) / area if area > 0 else 0.0
                    if velocity < constraint.min_value:
                        return constraint.min_value - velocity
                    if velocity > constraint.max_value:
                        return velocity - constraint.max_value
            
            return 0.0
        
        # Build constraint functions
        constraint_funcs = [
            {'type': 'ineq', 'fun': lambda x, c=c: -constraint_func(x, c)}
            for c in constraints
        ]
        
        # Bounds for pump parameters (flow multiplier 0.0 to 2.0)
        bounds = Bounds(
            lb=[0.0] * len(initial_values),
            ub=[2.0] * len(initial_values)
        )
        
        # Run optimization
        result = minimize(
            objective_func,
            initial_values,
            method='SLSQP',
            bounds=bounds,
            constraints=constraint_funcs,
            options={'maxiter': max_iterations, 'ftol': tolerance},
        )
        
        # Apply optimized values
        self._apply_pump_parameters(network, pump_ids, result.x)
        self.solver.solve(network)
        
        # Calculate results
        optimized_power = self._calculate_total_power(network, pump_ids)
        improvement = ((baseline_power - optimized_power) / baseline_power * 100
                      if baseline_power > 0 else 0.0)
        
        opt_result = OptimizationResult(
            success=result.success,
            iterations=getattr(result, 'nit', 0),
            objective_value=result.fun,
            improvement_percent=improvement,
            optimized_flows=self._extract_pipe_flows(network),
            optimized_pressures=self._extract_node_pressures(network),
            message=getattr(result, 'message', ''),
        )
        
        # Check constraint satisfaction
        for constraint in constraints:
            satisfied = constraint_func(result.x, constraint) <= 0.0
            opt_result.constraints_satisfied[
                f"{constraint.constraint_type}_{constraint.node_id or constraint.pipe_id}"
            ] = satisfied
        
        self.last_result = opt_result
        self._baseline_pump_flows = None
        return opt_result
    
    def balance_flows(
        self,
        network: PipeNetwork,
        pipe_ids: list[str],
        tolerance: float = 0.05,
    ) -> OptimizationResult:
        """Balance flows across specified parallel pipes.
        
        Args:
            network: The pipe network
            pipe_ids: List of pipe IDs to balance
            tolerance: Flow balance tolerance (fraction)
            
        Returns:
            OptimizationResult with balanced flows
        """
        # Create balance constraints
        constraints = [
            OptimizationConstraint(
                constraint_type='flow_balance',
                pipe_id=pipe_ids[0],
                min_value=-tolerance,
                max_value=tolerance,
            )
        ]
        
        return self.optimize(
            network,
            objective=ObjectiveType.BALANCE_FLOWS,
            constraints=constraints,
        )
    
    def _extract_network_values(self, network: PipeNetwork) -> dict:
        """Extract current network state."""
        return {
            'flows': self._extract_pipe_flows(network),
            'pressures': self._extract_node_pressures(network),
        }
    
    def _extract_pump_parameters(
        self,
        network: PipeNetwork,
        pump_ids: list[str],
    ) -> np.ndarray:
        """Extract pump parameters as optimization variables."""
        params = []
        for pump_id in pump_ids:
            pipe = network.pipes.get(pump_id)
            if pipe:
                # Use current flow multiplier or default to 1.0
                multiplier = getattr(pipe, 'pump_multiplier', 1.0)
                params.append(multiplier)
        return np.array(params, dtype=float)
    
    def _apply_pump_parameters(
        self,
        network: PipeNetwork,
        pump_ids: list[str],
        values: np.ndarray,
    ) -> None:
        """Apply optimization variables back to network."""
        for i, pump_id in enumerate(pump_ids):
            if i < len(values):
                pipe = network.pipes.get(pump_id)
                if pipe:
                    setattr(pipe, 'pump_multiplier', float(values[i]))
                    if self._baseline_pump_flows is not None and pump_id in self._baseline_pump_flows:
                        base_flow = self._baseline_pump_flows[pump_id]
                        pipe.flow_rate = base_flow * float(values[i])
    
    def _calculate_total_power(
        self,
        network: PipeNetwork,
        pump_ids: list[str],
    ) -> float:
        """Calculate total pump power consumption.
        
        Power = ρ * g * Q * H (Watts)
        where Q is flow rate, H is head
        """
        total_power = 0.0
        rho = self.dp_service.fluid.density or 998.0
        g = 9.81
        
        for pump_id in pump_ids:
            pipe = network.pipes.get(pump_id)
            if pipe and pipe.pump_curve:
                flow = getattr(pipe, 'flow_rate', 0.0)
                head = pipe.pump_curve.pressure_gain(flow) / (rho * g)
                power = rho * g * flow * head / 1000  # Convert to kW
                total_power += max(0.0, power)  # Only count positive power
        
        return total_power
    
    def _calculate_max_pressure(self, network: PipeNetwork) -> float:
        """Calculate maximum pressure in network."""
        pressures = [
            p for p in (
                getattr(node, 'pressure', None)
                for node in network.nodes.values()
            )
            if p is not None
        ]
        return max(pressures) if pressures else 0.0
    
    def _calculate_flow_balance_cost(self, network: PipeNetwork) -> float:
        """Calculate flow balance cost (std dev of flows)."""
        flows = [
            abs(getattr(pipe, 'flow_rate', 0.0))
            for pipe in network.pipes.values()
        ]
        if not flows or len(flows) < 2:
            return 0.0
        return np.std(flows)
    
    def _extract_pipe_flows(self, network: PipeNetwork) -> dict:
        """Extract all pipe flow rates."""
        return {
            pipe_id: getattr(pipe, 'flow_rate', 0.0)
            for pipe_id, pipe in network.pipes.items()
        }
    
    def _extract_node_pressures(self, network: PipeNetwork) -> dict:
        """Extract all node pressures."""
        return {
            node_id: getattr(node, 'pressure', 0.0)
            for node_id, node in network.nodes.items()
        }
    
    def get_optimization_summary(self) -> str:
        """Get human-readable summary of last optimization."""
        if not self.last_result:
            return "No optimization performed yet"
        
        summary = []
        summary.append(f"Optimization Success: {self.last_result.success}")
        summary.append(f"Iterations: {self.last_result.iterations}")
        summary.append(f"Objective Value: {self.last_result.objective_value:.2f}")
        summary.append(f"Power Improvement: {self.last_result.improvement_percent:.1f}%")
        summary.append(f"Constraints Satisfied: {sum(self.last_result.constraints_satisfied.values())}/{len(self.last_result.constraints_satisfied)}")
        
        return "\n".join(summary)
