# Multi-Phase Flow UI Guide

## How to Use Multi-Phase Fluid Settings

### Accessing Fluid Settings
1. **Open the application** by running `python run.py`
2. **Navigate to the Home tab** in the ribbon menu (top of window)
3. **Click the "Fluid" button** in the "Settings" group
4. The **Fluid Properties Dialog** will open

### Configuring Multi-Phase Flow

#### In the Fluid Properties Dialog:

1. **Enable Multi-Phase Mode**
   - Check the "Enable Multi-Phase Flow" checkbox at the top
   
2. **Single-Phase Properties** (used when multi-phase is disabled):
   - **Density**: Fluid density in kg/m³ (default: 998.0 for water)
   - **Viscosity**: Fluid viscosity in Pa·s (default: 0.001 for water)

3. **Multi-Phase Properties** (enabled when checkbox is checked):
   - **Liquid Density**: Density of liquid phase in kg/m³ (default: 998.0)
   - **Gas Density**: Density of gas phase in kg/m³ (default: 1.2 for air)
   - **Liquid Viscosity**: Viscosity of liquid in Pa·s (default: 0.001)
   - **Gas Viscosity**: Viscosity of gas in Pa·s (default: 1.8e-05 for air)
   - **Surface Tension**: Interfacial tension in N/m (default: 0.072 for water-air)

4. **Click OK** to apply settings

### Configuring Pipes for Multi-Phase Flow

Once multi-phase mode is enabled:

1. **Right-click on any pipe** in the workspace
2. **Select "Edit pipe properties..."**
3. The dialog will show different fields based on mode:

   **Single-Phase Mode:**
   - Length (m)
   - Diameter (m)
   - Roughness (dimensionless)
   - Flow Rate (m³/s)

   **Multi-Phase Mode:**
   - Length (m)
   - Diameter (m)
   - Roughness (dimensionless)
   - **Liquid Flow Rate** (m³/s) - volumetric flow of liquid phase
   - **Gas Flow Rate** (m³/s) - volumetric flow of gas phase

4. **Enter values** and click OK

### Status Bar Indicator

After changing fluid settings, the status bar (bottom of window) will show:
- "Fluid settings updated: Single-Phase mode" or
- "Fluid settings updated: Multi-Phase mode"

This confirms which mode is active.

### Running Simulations

1. Build your network with nodes and pipes
2. Configure fluid properties (single or multi-phase)
3. Set pipe properties (flow rates, dimensions)
4. Click **"Run"** in the Home tab
5. View results by clicking **"Results"**

### Example Workflow

**For a Water-Air Two-Phase System:**

1. Click "Fluid" button → Check "Enable Multi-Phase Flow"
2. Set properties:
   - Liquid Density: 998 kg/m³
   - Gas Density: 1.2 kg/m³
   - Liquid Viscosity: 0.001 Pa·s
   - Gas Viscosity: 0.000018 Pa·s
   - Surface Tension: 0.072 N/m
3. Click OK
4. Create network with nodes and pipes
5. Right-click each pipe → Set liquid and gas flow rates
6. Run simulation

### Notes

- Multi-phase calculations use a simplified Beggs-Brill correlation
- Assumes horizontal pipes (elevation effects not included)
- Flow rates are superficial velocities (as if each phase fills pipe alone)
- Total mixture velocity = liquid velocity + gas velocity
- The simulation calculates mixture properties and pressure drops automatically

### Switching Between Modes

You can switch between single-phase and multi-phase at any time:
- Changes apply to all future simulations
- Existing pipe configurations are preserved
- In multi-phase mode, single-phase flow rate is ignored
- In single-phase mode, liquid/gas flow rates are ignored

