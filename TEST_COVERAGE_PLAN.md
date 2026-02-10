# Test Coverage Plan - February 2026

## Current Status: 78 tests passing

## Coverage by Category

### ✅ EXCELLENT Coverage (15+ tests)
- [x] Friction correlations - 18 tests
- [x] GUI integration - 20 tests
- [x] Transient solver - 25 tests
- [x] Performance benchmarks - 8 tests

### ⚠️ GOOD Coverage (5-14 tests)
- [x] Multiphase flow - 9 tests
- [x] Pump nodes - 6 tests

### ⚠️ BASIC Coverage (1-4 tests)
- [x] Fitting losses - 4 tests
- [x] Model (pressure drop) - 2 tests
- [x] Network (pressure propagation) - 1 test

### ❌ MISSING Coverage (0 tests)

#### HIGH PRIORITY - Core Business Logic
1. **MainController** (`app/controllers/main_controller.py`)
   - [ ] `build_network_from_scene()` - converts UI to network model
   - [ ] `run_network_simulation()` - main simulation workflow
   - [ ] `run_transient_simulation()` - transient workflow
   - [ ] `set_fluid()` - fluid management
   - [ ] `set_solver_method()` - solver selection

2. **Network Solvers** (`app/services/solvers/`)
   - [ ] `CycleFinder` - cycle detection algorithm
   - [ ] `HardyCrossSolver` - iterative solver
   - [ ] `NewtonRaphsonSolver` - matrix solver (CRITICAL)
   - [ ] `PressurePropagation` - pressure propagation
   - [ ] `NetworkSolver` - solver orchestration

3. **Map/Network Classes** (`app/map/`)
   - [ ] `Node` - node model with properties
   - [ ] `Pipe` - pipe model with equipment
   - [ ] `PipeNetwork` - graph operations (add/remove/query)

4. **Models** (`app/models/`)
   - [ ] `Fluid` - single/multi-phase properties
   - [ ] `Equipment` - pump curves, valves
   - [ ] `EquipmentAdvanced` - advanced equipment

#### MEDIUM PRIORITY - Services
5. **EPANET Parser** (`app/services/parsers/epanet_parser.py`)
   - [ ] Import .INP files
   - [ ] Export to .INP format
   - [ ] Section parsing accuracy

6. **Exporters** (`app/services/exporters/`)
   - [ ] PDF report generation
   - [ ] Results CSV export
   - [ ] DXF CAD export

7. **Analysis Services** (`app/services/`)
   - [ ] `PipePointAnalyzer` - point-by-point analysis
   - [ ] `NetworkOptimizer` - optimization algorithms

#### LOWER PRIORITY - UI Components
8. **UI Dialogs** (`app/ui/dialogs/`)
   - [ ] Dialog input validation
   - [ ] Data conversion accuracy

9. **UI Commands** (`app/ui/commands/`)
   - [ ] Undo/redo commands (basic tests exist)
   - [ ] Command manager state

10. **Scene Components** (`app/ui/scenes/`)
    - [ ] Node/pipe operations
    - [ ] Result application

11. **Validation** (`app/ui/validation/`)
    - [ ] Realtime validator rules
    - [ ] Validation issue detection

---

## Recommended Test Implementation Order

### Phase 1: Core Business Logic (Week 1)
1. **test_main_controller.py** - Controller integration tests
2. **test_network_solvers.py** - All solver algorithms
3. **test_map_models.py** - Node, Pipe, PipeNetwork

### Phase 2: Import/Export (Week 2)
4. **test_epanet_integration.py** - EPANET import/export
5. **test_exporters.py** - PDF, CSV, DXF export

### Phase 3: Services & Analysis (Week 3)
6. **test_pipe_point_analyzer.py** - Point analysis
7. **test_network_optimizer.py** (fix existing)
8. **test_fluid_models.py** - Comprehensive fluid tests

### Phase 4: UI Components (Week 4)
9. **test_dialogs.py** - All dialog functionality
10. **test_commands_extended.py** - Complete command coverage
11. **test_validation_complete.py** - All validation rules

---

## Target Metrics
- **Current**: ~78 tests
- **Phase 1 Target**: 150+ tests
- **Phase 2 Target**: 180+ tests
- **Phase 3 Target**: 220+ tests
- **Phase 4 Target**: 280+ tests

## Critical Test Scenarios

### Must-Have Integration Tests
1. ✅ Simple network (source → pipe → sink)
2. ✅ Looped network (Hardy-Cross)
3. ❌ Complex network (Newton-Raphson vs Hardy-Cross comparison)
4. ❌ Network with pumps (node-based and pipe-based)
5. ❌ Network with valves
6. ❌ Multi-phase flow network
7. ✅ Transient analysis (pump trip, valve closure)
8. ❌ EPANET import → simulate → export workflow
9. ❌ Network build → simulate → export PDF workflow
10. ❌ Network optimization workflow

### Edge Cases to Test
- Empty networks
- Single node networks
- Disconnected networks
- Zero flow scenarios
- Negative pressures (cavitation)
- Very large networks (1000+ nodes)
- Circular reference detection
- Invalid input handling

---

## Next Actions
1. ✅ Create this test coverage plan
2. ⏭️ Implement `test_main_controller.py` (highest priority)
3. ⏭️ Implement `test_network_solvers.py` (Newton-Raphson critical)
4. ⏭️ Implement `test_map_models.py` (foundation)
5. ⏭️ Fix `test_network_optimizer.py` (has errors)
