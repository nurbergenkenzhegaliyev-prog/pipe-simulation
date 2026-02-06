"""Solvers package for hydraulic network simulation.

Contains different solver algorithms for computing pressures and flows
in pipe networks.
"""

from app.services.solvers.cycle_finder import CycleFinder
from app.services.solvers.hardy_cross_solver import HardyCrossSolver
from app.services.solvers.newton_raphson_solver import NewtonRaphsonSolver
from app.services.solvers.pressure_propagation import PressurePropagation
from app.services.solvers.network_solver import NetworkSolver, NetworkPressureSolver, SolverMethod

__all__ = [
    'CycleFinder',
    'HardyCrossSolver',
    'NewtonRaphsonSolver',
    'PressurePropagation',
    'NetworkSolver',
    'NetworkPressureSolver',  # Legacy alias
    'SolverMethod',
]
