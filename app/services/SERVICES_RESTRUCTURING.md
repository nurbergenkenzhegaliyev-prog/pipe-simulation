# Services Folder Restructuring - February 2026

## Overview

The `app/services` folder has been reorganized into a modular structure with clear separation of concerns. This makes the codebase more maintainable and easier to navigate.

## New Structure

```
app/services/
├── __init__.py                      # Main services package
├── solvers/                         # Network solver algorithms
│   ├── __init__.py
│   ├── cycle_finder.py              # Cycle detection (BFS)
│   ├── hardy_cross_solver.py        # Hardy-Cross method
│   ├── newton_raphson_solver.py     # Newton-Raphson method (NEW!)
│   ├── pressure_propagation.py      # Pressure propagation
│   └── network_solver.py            # Main solver with method selection
├── pressure/                        # Pressure drop calculations
│   ├── __init__.py
│   ├── pressure_drop_service.py     # Main pressure drop service
│   ├── pressure_drop_components.py  # Single/multi-phase components
│   ├── friction_correlations.py     # Friction factor correlations
│   └── fitting_losses.py            # Minor loss coefficients
├── exporters/                       # Export services
│   ├── __init__.py
│   ├── pdf_report_generator.py      # PDF report export
│   ├── results_exporter.py          # CSV export
│   └── cad_exporter.py              # DXF/CAD export
├── parsers/                         # Import parsers
│   ├── __init__.py
│   └── epanet_parser.py             # EPANET INP parser
├── network_optimizer.py             # Network optimization (stays at root)
├── pipe_point_analyzer.py           # Pipe point analysis (stays at root)
└── transient_solver.py              # Transient solver (stays at root)
```

## Key Changes

### 1. **Solvers Subfolder** (`solvers/`)

All network solving algorithms are now in one place:

- **CycleFinder**: Detects loops in the network using BFS
- **HardyCrossSolver**: Traditional iterative method (KEPT for backward compatibility)
- **NewtonRaphsonSolver**: NEW! Modern method with faster convergence
- **PressurePropagation**: Propagates pressures from sources
- **NetworkSolver**: Main solver class with method selection

**Usage:**
```python
from app.services.solvers import NetworkSolver, SolverMethod

# Create solver with Newton-Raphson (default)
solver = NetworkSolver(dp_service, method=SolverMethod.NEWTON_RAPHSON)

# Or use Hardy-Cross
solver = NetworkSolver(dp_service, method=SolverMethod.HARDY_CROSS)

solver.solve(network)
```

### 2. **Pressure Subfolder** (`pressure/`)

Pressure drop calculations and friction correlations:

- **PressureDropService**: Main service for pressure calculations
- **SinglePhasePressureDrop**: Darcy-Weisbach equation
- **MultiPhasePressureDrop**: Lockhart-Martinelli correlation
- **FrictionFactorCalculator**: 5 friction factor methods
- **FittingK**: Minor loss coefficients library

**Usage:**
```python
from app.services.pressure import PressureDropService, FrictionCorrelation

dp_service = PressureDropService(fluid)
dp = dp_service.calculate_pipe_dp(pipe)
```

### 3. **Exporters Subfolder** (`exporters/`)

All export functionality:

- **PDFReportGenerator**: Professional PDF reports with charts
- **ResultsExporter**: CSV export for nodes/pipes
- **DXFExporter**: CAD export

**Usage:**
```python
from app.services.exporters.pdf_report_generator import PDFReportGenerator

generator = PDFReportGenerator()
generator.generate_report(network, fluid, "report.pdf")
```

### 4. **Parsers Subfolder** (`parsers/`)

Import parsers for various formats:

- **EPANETParser**: EPANET INP file import

**Usage:**
```python
from app.services.parsers.epanet_parser import EPANETParser

parser = EPANETParser()
network = parser.parse_file("network.inp")
```

## Newton-Raphson Solver

### What is Newton-Raphson?

Newton-Raphson is a numerical method that solves the network equations simultaneously rather than iteratively balancing each loop. It typically converges faster than Hardy-Cross for complex networks.

### Comparison: Hardy-Cross vs Newton-Raphson

| Feature | Hardy-Cross | Newton-Raphson |
|---------|------------|----------------|
| **Method** | Iterative loop balancing | Simultaneous equation solving |
| **Convergence** | 5-20 iterations | 3-10 iterations |
| **Speed** | Good | Faster |
| **Accuracy** | Good | Excellent |
| **Complexity** | Simple | Moderate |
| **Best for** | Small-medium networks | Medium-large networks |

### Performance

Newton-Raphson typically requires **30-50% fewer iterations** than Hardy-Cross for looped networks.

## Solver Method Selection

### Default Method

**Newton-Raphson** is now the default solver method (as of February 2026).

### Changing the Solver Method

#### In UI:
1. Click **"Simulation Settings"** button in HOME tab
2. Select solver method from dropdown
3. Click OK

#### In Code:
```python
from app.services.solvers import SolverMethod

# Via controller
controller.set_solver_method(SolverMethod.NEWTON_RAPHSON)
controller.set_solver_method(SolverMethod.HARDY_CROSS)

# Via solver
solver = NetworkSolver(dp_service, method=SolverMethod.NEWTON_RAPHSON)
solver.set_method(SolverMethod.HARDY_CROSS)
```

## Backward Compatibility

All old imports still work through legacy aliases:

```python
# OLD (still works)
from app.services.pressure_drop_service import PressureDropService
from app.services.network_pressure_solver import NetworkPressureSolver

# NEW (recommended)
from app.services.pressure import PressureDropService
from app.services.solvers import NetworkSolver
```

`NetworkPressureSolver` is now an alias for `NetworkSolver`.

## Migration Guide

### For Existing Code

**Option 1: Keep old imports** (works but deprecated)
```python
from app.services.pressure_drop_service import PressureDropService
from app.services.network_pressure_solver import NetworkPressureSolver
```

**Option 2: Update to new imports** (recommended)
```python
from app.services.pressure import PressureDropService
from app.services.solvers import NetworkSolver

# Change this:
solver = NetworkPressureSolver(dp_service)

# To this:
solver = NetworkSolver(dp_service)  # Uses Newton-Raphson by default
```

### For New Code

Always use the new imports:

```python
from app.services.solvers import NetworkSolver, SolverMethod
from app.services.pressure import PressureDropService
from app.services.exporters.pdf_report_generator import PDFReportGenerator
from app.services.parsers.epanet_parser import EPANETParser
```

## Benefits

1. **Better Organization**: Related functionality grouped together
2. **Easier Navigation**: Clear folder structure
3. **Scalability**: Easy to add new solvers, exporters, parsers
4. **Maintainability**: Changes isolated to specific subfolders
5. **Performance**: Newton-Raphson provides faster convergence
6. **Flexibility**: Easy to switch between solver methods

## Testing

All tests have been updated to use the new structure:

```bash
# Run tests
pytest tests/test_network.py -v
pytest tests/test_performance.py -v

# Test both solver methods
pytest tests/ -v -k solver
```

## Future Enhancements

Planned additions to the new structure:

- **solvers/gradient_descent_solver.py**: Optimization-based solver
- **exporters/excel_exporter.py**: Excel export with formulas
- **parsers/csv_parser.py**: Simple CSV import
- **pressure/compressible_flow.py**: Gas flow calculations

## Questions?

See the main [README.md](../../README.md) or [APPLICATION_FULL_DESCRIPTION.txt](../../APPLICATION_FULL_DESCRIPTION.txt) for full documentation.

---

**Last Updated**: February 6, 2026  
**Version**: 2.0  
**Author**: Development Team
