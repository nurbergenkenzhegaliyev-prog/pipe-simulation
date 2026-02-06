# Quick Start Guide - New Services Structure

## For Users

### Changing Solver Method

1. **Open Simulation Settings**
   - Click **"Simulation Settings"** button in HOME tab (Settings group)

2. **Select Method**
   - **Newton-Raphson (Default, Faster)** - Recommended for most cases
   - **Hardy-Cross (Traditional)** - Classic method, well-tested

3. **Run Simulation**
   - Click **"Run"** button
   - Selected method is used automatically

---

## For Developers

### Quick Import Reference

```python
# Solvers
from app.services.solvers import NetworkSolver, SolverMethod

# Pressure calculations
from app.services.pressure import PressureDropService

# Exporters
from app.services.exporters.pdf_report_generator import PDFReportGenerator
from app.services.exporters.results_exporter import ResultsExporter

# Parsers
from app.services.parsers.epanet_parser import EPANETParser
```

### Creating a Network Solver

```python
from app.models.fluid import Fluid
from app.services.pressure import PressureDropService
from app.services.solvers import NetworkSolver, SolverMethod

# Setup
fluid = Fluid(density=998.0, viscosity=1e-3)
dp_service = PressureDropService(fluid)

# Method 1: Newton-Raphson (default)
solver = NetworkSolver(dp_service)

# Method 2: Hardy-Cross
solver = NetworkSolver(dp_service, method=SolverMethod.HARDY_CROSS)

# Solve
solver.solve(network)
```

### Switching Methods at Runtime

```python
# Change method
solver.set_method(SolverMethod.NEWTON_RAPHSON)
solver.solve(network)

solver.set_method(SolverMethod.HARDY_CROSS)
solver.solve(network)
```

### In MainController

```python
# Set solver method
controller.set_solver_method(SolverMethod.NEWTON_RAPHSON)

# Run simulation (uses stored method)
network = controller.run_network_simulation()
```

---

## Folder Structure at a Glance

```
app/services/
├── solvers/          ← Network solving algorithms
├── pressure/         ← Pressure drop calculations
├── exporters/        ← PDF, CSV, CAD export
└── parsers/          ← EPANET, etc. import
```

---

## When to Use Each Solver

### Newton-Raphson (Recommended)
✅ Default method  
✅ Faster convergence (3-10 iterations)  
✅ Better for large networks  
✅ More accurate results  
✅ Recommended for production  

**Use when:**
- Network has 50+ nodes
- Network has many loops
- Fast solving is important
- High accuracy needed

### Hardy-Cross (Traditional)
✅ Well-tested and proven  
✅ Simple algorithm  
✅ Lower memory usage  
✅ Good for teaching  

**Use when:**
- Small networks (< 50 nodes)
- Debugging/verification needed
- Comparing against known results
- Educational purposes

---

## Common Tasks

### Export Results to PDF
```python
from app.services.exporters.pdf_report_generator import PDFReportGenerator

generator = PDFReportGenerator()
generator.generate_report(network, fluid, "output.pdf")
```

### Export Results to CSV
```python
from app.services.exporters.results_exporter import ResultsExporter

exporter = ResultsExporter()
exporter.export_nodes(network, "nodes.csv")
exporter.export_pipes(network, "pipes.csv")
```

### Import EPANET File
```python
from app.services.parsers.epanet_parser import EPANETParser

parser = EPANETParser()
network = parser.parse_file("network.inp")
```

---

## Need More Help?

- **Full Documentation**: See [SERVICES_RESTRUCTURING.md](SERVICES_RESTRUCTURING.md)
- **Implementation Details**: See [RESTRUCTURING_SUMMARY_FEB_2026.md](RESTRUCTURING_SUMMARY_FEB_2026.md)
- **Application Guide**: See [APPLICATION_FULL_DESCRIPTION.txt](APPLICATION_FULL_DESCRIPTION.txt)

---

**Last Updated**: February 6, 2026
