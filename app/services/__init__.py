"""Services package for pipe network simulation.

This package is now organized into subfolders:
- pressure/: Pressure drop calculations and friction correlations
- solvers/: Network solvers (Hardy-Cross, Newton-Raphson, etc.)
- exporters/: Export services (PDF, CSV, CAD)
- parsers/: Import parsers (EPANET, etc.)
"""

# Legacy imports for backward compatibility
from app.services.solvers import NetworkSolver, NetworkPressureSolver, SolverMethod
from app.services.pressure import PressureDropService

__all__ = [
    'NetworkSolver',
    'NetworkPressureSolver',  # Legacy alias
    'SolverMethod',
    'PressureDropService',
]
