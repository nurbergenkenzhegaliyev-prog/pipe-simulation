# Getting Started Guide

## For Users

### Installation

1. **Install Python 3.10+**
   ```bash
   python --version  # Should be 3.10 or higher
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Application**
   ```bash
   python run.py
   ```

### Basic Workflow

#### 1. Building a Network
- Select **Source** tool from Insert tab
- Click on canvas to place source nodes
- Select **Sink** tool and place sink nodes
- Select **Node** tool and place junction nodes
- Select **Pipe** tool and click two nodes to create connections

#### 2. Configuring Equipment
- Right-click a node to edit properties
- Select **"Edit node properties..."** to set:
  - Source pressure (Pa)
  - Flow rates (m^3/s)
  - Pump pressure ratio
  - Valve Cv coefficient

- Right-click a pipe to edit:
  - Diameter (m)
  - Length (m)
  - Roughness coefficient
  - Minor loss coefficients

#### 3. Running Simulation
1. Click **"Run"** button in HOME tab
2. Select **Simulation Settings** to choose solver method:
   - **Newton-Raphson** (Default, Faster) - Recommended
   - **Hardy-Cross** (Traditional) - Classic method
3. View results in **Results** panel

#### 4. Exporting Results
- **PDF Report**: Results → "Generate PDF Report"
- **CSV Export**: Results → "Export as CSV"
- **CAD Drawing**: Results → "Export to DXF"
- **EPANET Format**: File → "Export as EPANET"

#### 5. Importing Networks
- **EPANET Files**: File → "Import from EPANET"
- **Load Saved**: File → "Open"

### Settings

#### Fluid Properties
- Click **"Fluid Settings"** in HOME tab
- Configure:
  - Fluid type (Single/Multi-phase)
  - Density
  - Viscosity
  - Gas fraction (for multi-phase)

#### Simulation Method
- Click **"Simulation Settings"** in HOME tab
- Choose:
  - **Newton-Raphson**: Faster, more accurate (recommended)
  - **Hardy-Cross**: Traditional, well-tested

### Keyboard Shortcuts
- **Delete**: Remove selected node/pipe
- **Escape**: Switch to SELECT tool
- **Ctrl+Z**: Undo
- **Ctrl+Y**: Redo

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

### Folder Structure Overview

```
app/services/
├── solvers/          ← Network solving algorithms
├── pressure/         ← Pressure drop calculations
├── exporters/        ← PDF, CSV, CAD export
└── parsers/          ← EPANET, etc. import
```

### When to Use Each Solver

#### Newton-Raphson (Recommended)
- Default method
- Faster convergence (3-10 iterations)
- Better for large networks
- More accurate results

**Use when:**
- Network has 50+ nodes
- Network has many loops
- Fast solving is important
- High accuracy needed

#### Hardy-Cross (Traditional)
- Well-tested and proven
- Simple algorithm
- Lower memory usage
- Good for teaching

**Use when:**
- Small networks (< 50 nodes)
- Debugging/verification needed
- Comparing against known results
- Educational purposes

### Common Development Tasks

#### Export Results to PDF
```python
from app.services.exporters.pdf_report_generator import PDFReportGenerator

generator = PDFReportGenerator()
generator.generate_report(network, fluid, "output.pdf")
```

#### Export Results to CSV
```python
from app.services.exporters.results_exporter import ResultsExporter

exporter = ResultsExporter()
exporter.export_nodes(network, "nodes.csv")
exporter.export_pipes(network, "pipes.csv")
```

#### Import EPANET File
```python
from app.services.parsers.epanet_parser import EPANETParser

parser = EPANETParser()
network = parser.parse_file("network.inp")
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_network.py -v

# Run with coverage
pytest tests/ --cov=app -v

# Run performance tests
pytest tests/test_performance.py -v -s
```

---

## Architecture Overview

The application follows a clean architecture with clear separation of concerns:

```
PyQt6 UI Layer
  |
  v
Controllers (MainController)
  |
  v
Services (Solvers, Exporters, Parsers, Pressure)
  |
  v
Models (Network, Pipe, Node, Fluid, Equipment)
  |
  v
Core Domain Logic
```

### Key Components

**UI Layer** (`app/ui/`)
- Window management
- Scene/canvas for network visualization
- Dialogs for configuration
- Commands for undo/redo

**Controllers** (`app/controllers/`)
- MainController: Coordinates UI and services

**Services** (`app/services/`)
- `solvers/`: Network solving (Newton-Raphson, Hardy-Cross)
- `pressure/`: Pressure drop calculations
- `exporters/`: PDF, CSV, DXF, EPANET export
- `parsers/`: EPANET INP import

**Models** (`app/models/`)
- Fluid, Network, Pipe, Node
- Equipment: Pump, Valve, Tank, Reservoir

**Utilities** (`app/utils/`)
- Helpers and common functions

---

## Debugging Tips

### View Debug Output
```python
# Enable logging
from app.core.logger import setup_logger
logger = setup_logger(__name__)
logger.debug("Debug message")
```

### Test Network Creation
```python
from app.models.network import Network
from app.models.pipe import Pipe
from app.models.node import Node

network = Network()
n1 = Node("N1", 0, 0, is_source=True, pressure=10e5)
n2 = Node("N2", 100, 0, is_sink=True, flow_rate=0.05)
p1 = Pipe("P1", n1, n2, length=100, diameter=0.2)
network.add_node(n1)
network.add_node(n2)
network.add_pipe(p1)
```

### Check Simulation Results
```python
# After solving
for pipe in network.pipes:
    print(f"{pipe.id}: Q={pipe.flow_rate:.4f} m^3/s, dP={pipe.pressure_drop:.0f} Pa")
```

---

## Common Issues

### "ModuleNotFoundError: No module named 'PyQt6'"
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### "Solver failed to converge"
**Options**:
1. Try Newton-Raphson method (usually more robust)
2. Check network connectivity (all nodes must be connected)
3. Verify boundary conditions (sources and sinks)

### "Slow simulation on large networks"
**Solutions**:
1. Use Newton-Raphson solver (faster convergence)
2. Check network for unnecessary complexity
3. Run on a faster machine for 100+ node networks

---

## Next Steps

- **For Users**: Check [Multiphase Flow Guide](./guides/multiphase-ui-guide.md) for advanced features
- **For Developers**: Read [Architecture Overview](./architecture/uml-architecture.md) for detailed design
- **For Contributors**: See [Development Roadmap](./roadmap/development-roadmap.md) for planned features

---

**Last Updated**: February 9, 2026  
**Version**: 2.0
