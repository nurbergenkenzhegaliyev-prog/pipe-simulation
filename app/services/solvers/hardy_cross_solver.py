"""Hardy-Cross iterative solver for looped pipe networks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from app.map.network import PipeNetwork
    from app.services.pressure_drop_service import PressureDropService
    from app.services.solvers.cycle_finder import Cycle


@dataclass
class HardyCrossSolver:
    """Hardy-Cross method for solving flow distribution in looped networks.
    
    Iteratively adjusts flow rates in each cycle until pressure drops balance.
    Uses the formula: ΔQ = -Σ(ΔP) / Σ(2|ΔP|/|Q|)
    
    Attributes:
        dp_service: Pressure drop calculation service
        max_iter: Maximum iterations (default: 50)
        tol: Convergence tolerance in Pa (default: 0.01)
    
    Example:
        >>> solver = HardyCrossSolver(dp_service, max_iter=50, tol=0.01)
        >>> solver.apply(network, cycles)
    """
    
    dp_service: 'PressureDropService'
    max_iter: int = 50
    tol: float = 1e-2

    def apply(self, network: 'PipeNetwork', cycles: Sequence['Cycle']) -> None:
        """Apply Hardy-Cross method to balance flows in all cycles.
        
        Args:
            network: The pipe network
            cycles: List of cycles (from CycleFinder)
            
        Raises:
            ValueError: If any pipe has no flow rate
        """
        for iteration in range(self.max_iter):
            max_imbalance = 0.0
            
            for cycle in cycles:
                sum_dp = 0.0
                sum_d = 0.0
                
                # Calculate pressure imbalance around the cycle
                for pipe, direction in cycle:
                    if pipe.flow_rate is None:
                        raise ValueError(f"Pipe {pipe.id} has no flow rate for Hardy-Cross")
                    
                    q = pipe.flow_rate
                    if q == 0:
                        q = 1e-6  # Avoid division by zero
                    
                    dp = self.dp_service.calculate_pipe_dp(pipe)
                    signed_dp = direction * dp
                    sum_dp += signed_dp
                    sum_d += 2.0 * abs(dp) / abs(q)

                if sum_d == 0:
                    continue

                # Calculate flow correction
                delta_q = -sum_dp / sum_d
                max_imbalance = max(max_imbalance, abs(sum_dp))

                # Apply correction to all pipes in cycle
                for pipe, direction in cycle:
                    pipe.flow_rate += direction * delta_q

            # Check convergence
            if max_imbalance < self.tol:
                break
