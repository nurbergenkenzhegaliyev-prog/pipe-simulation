# Pipe Network Simulation Application

A professional PyQt6-based hydraulic network modeling and simulation application with advanced features for engineering analysis.

## 🌟 Features

### Core Simulation Capabilities
- ✅ **Single-Phase Flow** - Water and other single-phase fluids
- ✅ **Multi-Phase Flow** - Gas-liquid mixture modeling  
- ✅ **Hardy-Cross Solver** - For looped network analysis
- ✅ **Pressure Drop Calculation** - Darcy-Weisbach with friction factors
- ✅ **Network Validation** - Real-time feedback on network integrity

### Equipment Models
- **Pipes** - Length, diameter, roughness, flow properties
- **Nodes** - Sources (fixed pressure), sinks (fixed demand), junctions
- **Pumps** - Quadratic curves and manufacturer data support
- **Valves** - Loss coefficient (K) and flow coefficient (Cv) models
- **Tanks & Reservoirs** - Dynamic level tracking

### User Interface
- **Visual Network Builder** - Drag-and-drop interface
- **Color-Coded Visualization** - Pressure and flow overlays
- **Flow Direction Arrows** - Visual flow indicators
- **Real-Time Validation** - Immediate feedback on errors/warnings
- **Undo/Redo** - Full command history (50 actions)

### Results & Export
- **CSV Export** - Nodes, pipes, and summary tables
- **PDF Reports** - Professional reports with charts and graphs
- **Charts** - Pressure, flow, and velocity distributions
- **EPANET Import/Export** - Industry-standard INP format

### Development Features
- **Comprehensive Testing** - Unit, integration, and performance tests
- **Performance Benchmarks** - Tested up to 200+ nodes
- **Modular Architecture** - Clean separation of concerns
- **Type Hints** - Full Python type annotations

## 📋 Requirements

- **Python** 3.10 or higher
- **PyQt6** - GUI framework
- **reportlab** - PDF generation
- **matplotlib** - Charts and graphs
- **pytest** - Testing framework (optional)

## 🚀 Quick Start

### Installation

```bash
# Clone or download the repository
cd myapp

# Create virtual environment
python -m venv env
env\Scripts\activate  # Windows
# source env/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
python run.py
```

## 📖 User Guide

### Building a Network

1. **Add Nodes**:
   - Click "Source" tool and click on canvas to add a source node
   - Click "Sink" tool and click on canvas to add a sink node
   - Click "Node" tool for junction nodes

2. **Connect with Pipes**:
   - Click "Pipe" tool
   - Click on first node, then second node
   - Pipe is created automatically

3. **Set Properties**:
   - Right-click on any node or pipe
   - Select "Edit properties..."
   - Set pressure, flow rate, diameter, length, etc.

4. **Add Equipment**:
   - Use "Pump" and "Valve" tools
   - Right-click to edit characteristics

### Running Simulation

1. Click **"Run"** button in the ribbon
2. Network is validated automatically
3. Solver calculates pressures and flows
4. Results are displayed:
   - Color overlay on pipes/nodes
   - Flow direction arrows
   - Numerical values in labels

### Viewing Results

1. Click **"Results"** button
2. View tables for nodes and pipes
3. Export to CSV or PDF

### Exporting Results

#### CSV Export
- Click "Export Nodes to CSV", "Export Pipes to CSV", or "Export Summary to CSV"
- Choose save location
- Open in Excel or other spreadsheet software

#### PDF Report
- Click **"Export PDF Report"** (green button)
- Includes:
  - Network summary
  - Node results table
  - Pipe results table
  - Pressure distribution chart
  - Flow distribution chart
  - Velocity distribution chart

### EPANET Import

1. Click **"Import EPANET"** in File menu
2. Select a `.inp` file
3. Network is automatically created
4. Adjust layout if needed

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run specific test files
pytest tests/test_network.py
pytest tests/test_multiphase.py
pytest tests/test_performance.py
pytest tests/test_gui_integration.py

# Run with verbose output
pytest -v -s

# Run performance benchmarks
pytest tests/test_performance.py -v -s
```

## 🏗️ Architecture

### Project Structure

```
myapp/
├── app/
│   ├── core/           # Application core
│   ├── models/         # Data models (Node, Pipe, Fluid, Equipment)
│   ├── map/            # Network graph (PipeNetwork)
│   ├── services/       # Business logic (solvers, exporters)
│   ├── controllers/    # UI-to-model bridge
│   └── ui/             # PyQt6 user interface
│       ├── windows/    # Main window
│       ├── views/      # Panels and tabs
│       ├── scenes/     # Graphics scene
│       ├── items/      # Graphics items (nodes, pipes)
│       ├── dialogs/    # Dialogs
│       ├── commands/   # Undo/redo commands
│       └── validation/ # Real-time validation
├── tests/              # Test suite
├── docs/               # Documentation
└── examples/           # Example networks
```

### Key Components

- **PipeNetwork** - Graph structure for nodes and pipes
- **NetworkPressureSolver** - Hardy-Cross + pressure propagation
- **PressureDropService** - Single-phase and multi-phase calculations
- **RealtimeNetworkValidator** - Live validation with visual feedback
- **PDFReportGenerator** - Professional report generation
- **EPANETParser** - Industry format compatibility

## 📊 Performance

Tested performance on various network sizes:

| Network Size | Topology | Solution Time |
|--------------|----------|---------------|
| 10 nodes     | Linear   | < 1 second    |
| 50 nodes     | Branched | < 2 seconds   |
| 100 nodes    | Linear   | < 5 seconds   |
| 200 nodes    | Linear   | < 10 seconds  |
| 25 nodes     | 5×5 Grid | < 5 seconds   |

## 🔧 Configuration

### Fluid Properties

Click **"Fluid"** in Settings to configure:
- Single-phase or multi-phase mode
- Density and viscosity
- Multi-phase properties (liquid/gas densities, viscosities, surface tension)

### Solver Settings

Currently uses default tolerances. Future versions will support:
- Convergence criteria
- Maximum iterations
- Relaxation factors

## 🤝 Contributing

Contributions are welcome! Areas for contribution:
- Additional equipment models
- Enhanced visualization
- Transient analysis
- Optimization tools
- Additional export formats

## 📄 License

[Your License Here]

## 🐛 Known Issues

- Grid layout for EPANET import may need manual adjustment
- Large networks (>500 nodes) may experience slower rendering
- Multi-phase flow validation could be enhanced

## 📞 Support

For issues, questions, or feature requests, please open an issue on GitHub or contact the development team.

## 🎯 Roadmap

See [development_suggestions.txt](development_suggestions.txt) for detailed roadmap.

### Upcoming Features
- GUI integration test automation
- Advanced equipment models with manufacturer data
- Sphinx API documentation
- CAD format export
- Transient analysis
- Network optimization tools

## 📚 Additional Resources

- [UML Architecture Diagram](UML_ARCHITECTURE.md)
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md)
- [Multi-Phase Flow Guide](docs/multiphase_ui_guide.md)
- [Validation Documentation](VALIDATION_FIXES.md)

---

**Version**: 1.0.0  
**Last Updated**: February 2026
