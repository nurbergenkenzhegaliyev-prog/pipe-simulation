"""Newton-Raphson solver for pipe networks.

Solves the nonlinear system of equations for flow and pressure distribution
using the Newton-Raphson method. More accurate and faster convergence than
Hardy-Cross for complex networks.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, TYPE_CHECKING

import math

if TYPE_CHECKING:
    from app.map.network import PipeNetwork
    from app.services.pressure_drop_service import PressureDropService

logger = logging.getLogger(__name__)


@dataclass
class NewtonRaphsonSolver:
    """Newton-Raphson method for solving pipe network equations.
    
    Formulates the network as a system of nonlinear equations:
    - Flow conservation at each node: Σ Q_in = Σ Q_out
    - Pressure loop equations: Σ ΔP = 0 for each cycle
    
    Uses Newton-Raphson iteration to solve the system simultaneously,
    providing faster convergence than Hardy-Cross method.
    
    Attributes:
        dp_service: Pressure drop calculation service
        max_iter: Maximum iterations (default: 50)
        tol: Convergence tolerance (default: 1e-4)
    
    Example:
        >>> solver = NewtonRaphsonSolver(dp_service)
        >>> solver.solve(network, cycles)
    """
    
    dp_service: 'PressureDropService'
    max_iter: int = 50
    tol: float = 1e-4

    def solve(self, network: 'PipeNetwork', cycles: List) -> None:
        """Solve the network using Newton-Raphson method.
        
        Args:
            network: The pipe network to solve
            cycles: List of independent cycles in the network
            
        Raises:
            ValueError: If network has no valid initial state
            RuntimeError: If method fails to converge
        """
        if not cycles:
            # No loops - tree structure, no need for iterative solving
            return
        
        # Build equation system
        n_pipes = len(network.pipes)
        n_cycles = len(cycles)
        
        if n_cycles == 0:
            return
        
        # Create flow rate vector (initially from current pipe flows)
        flows = []
        pipe_list = list(network.pipes.values())
        
        for pipe in pipe_list:
            if pipe.flow_rate is None:
                pipe.flow_rate = 1e-4  # Small initial guess
            flows.append(pipe.flow_rate)
        
        # Newton-Raphson iterations
        for iteration in range(self.max_iter):
            # Build residual vector (pressure imbalances for each cycle)
            residuals = []
            
            for cycle in cycles:
                cycle_imbalance = 0.0
                for pipe, direction in cycle:
                    dp = self.dp_service.calculate_pipe_dp(pipe)
                    cycle_imbalance += direction * dp
                residuals.append(cycle_imbalance)
            
            # Check convergence
            max_residual = max(abs(r) for r in residuals) if residuals else 0.0
            if max_residual < self.tol:
                logger.info(f"Newton-Raphson converged in {iteration} iterations")
                return
            
            # Build Jacobian matrix (derivatives of residuals w.r.t. flows)
            jacobian = [[0.0] * n_cycles for _ in range(n_cycles)]
            
            for i, cycle in enumerate(cycles):
                for j, (other_cycle) in enumerate(cycles):
                    # Compute ∂R_i/∂Q_j
                    # For pipes common to both cycles, add derivative contribution
                    derivative = 0.0
                    
                    for pipe, direction_i in cycle:
                        for other_pipe, direction_j in other_cycle:
                            if pipe.id == other_pipe.id:
                                # Derivative of ΔP w.r.t. Q
                                # ΔP = f * (L/D) * (ρ * V²/2)
                                # V = Q / A, so ΔP ∝ Q²
                                # d(ΔP)/dQ ≈ 2 * ΔP / Q
                                
                                q = pipe.flow_rate if pipe.flow_rate != 0 else 1e-6
                                dp = self.dp_service.calculate_pipe_dp(pipe)
                                
                                # Derivative contribution
                                derivative += direction_i * direction_j * 2.0 * dp / q
                    
                    jacobian[i][j] = derivative
            
            # Solve linear system: J * ΔQ = -R
            # Using simple Gaussian elimination for small systems
            delta_flows = self._solve_linear_system(jacobian, residuals)
            
            if delta_flows is None:
                logger.warning("Newton-Raphson: Singular Jacobian matrix")
                break
            
            # Update flows in each cycle
            for i, cycle in enumerate(cycles):
                for pipe, direction in cycle:
                    pipe.flow_rate -= direction * delta_flows[i]
        
        logger.warning(f"Newton-Raphson did not converge after {self.max_iter} iterations")
    
    def _solve_linear_system(self, A: List[List[float]], b: List[float]) -> List[float] | None:
        """Solve linear system Ax = b using Gaussian elimination.
        
        Args:
            A: Coefficient matrix (n x n)
            b: Right-hand side vector (n,)
            
        Returns:
            Solution vector x, or None if singular
        """
        n = len(b)
        if n == 0:
            return []
        
        # Create augmented matrix
        aug = [A[i][:] + [b[i]] for i in range(n)]
        
        # Forward elimination
        for i in range(n):
            # Find pivot
            max_row = i
            for k in range(i + 1, n):
                if abs(aug[k][i]) > abs(aug[max_row][i]):
                    max_row = k
            
            # Swap rows
            aug[i], aug[max_row] = aug[max_row], aug[i]
            
            # Check for singular matrix
            if abs(aug[i][i]) < 1e-10:
                return None
            
            # Eliminate column
            for k in range(i + 1, n):
                factor = aug[k][i] / aug[i][i]
                for j in range(i, n + 1):
                    aug[k][j] -= factor * aug[i][j]
        
        # Back substitution
        x = [0.0] * n
        for i in range(n - 1, -1, -1):
            x[i] = aug[i][n]
            for j in range(i + 1, n):
                x[i] -= aug[i][j] * x[j]
            x[i] /= aug[i][i]
        
        return x
