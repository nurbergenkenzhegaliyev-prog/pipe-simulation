"""Tests for equipment models (pumps, valves) and fluid properties.

Tests cover:
- Pump curve representations and pressure calculations
- Valve loss characteristics
- Fluid properties and temperature effects
- Equipment integration in networks
"""

import pytest
import math

from app.models.equipment import PumpCurve, Valve
from app.models.fluid import Fluid
from app.map.pipe import Pipe
from app.map.node import Node
from app.map.network import PipeNetwork


class TestPumpCurveBasics:
    """Test pump curve creation and evaluation"""
    
    def test_pump_curve_constant_head(self):
        """Should represent constant head pump (linear curve)"""
        # dp = a + b*Q + c*Q^2
        # For constant head: a=1000 Pa, b=0, c=0
        pump = PumpCurve(a=1000.0, b=0.0, c=0.0)
        
        assert pump.a == 1000.0
        assert pump.b == 0.0
        assert pump.c == 0.0
    
    def test_pump_curve_centrifugal_typical(self):
        """Should represent typical centrifugal pump curve"""
        # Decreasing head with increasing flow: a=5000, b=-1000, c=-500
        pump = PumpCurve(a=5000.0, b=-1000.0, c=-500.0)
        
        assert pump.a == 5000.0
        assert pump.b == -1000.0
        assert pump.c == -500.0
    
    def test_pump_pressure_gain_at_zero_flow(self):
        """Should return maximum pressure at zero flow"""
        pump = PumpCurve(a=10000.0, b=-1000.0, c=-500.0)
        
        dp = pump.pressure_gain(0.0)
        assert dp == 10000.0  # Shutoff head
    
    def test_pump_pressure_gain_at_rated_flow(self):
        """Should calculate pressure gain at rated flow"""
        pump = PumpCurve(a=10000.0, b=-1000.0, c=-500.0)
        
        # At Q=0.05 m³/s: dp = 10000 - 1000*0.05 - 500*0.05^2
        dp = pump.pressure_gain(0.05)
        expected = 10000.0 - (1000.0 * 0.05) - (500.0 * 0.05**2)
        
        assert dp == pytest.approx(expected)
        assert dp < 10000.0  # Pressure decreases with flow
    
    def test_pump_curve_positive_displacement(self):
        """Should model positive displacement pump"""
        # PD pumps maintain constant pressure regardless of flow
        pump = PumpCurve(a=15000.0, b=0.0, c=0.0)
        
        # Pressure is constant for all flows
        dp1 = pump.pressure_gain(0.0)
        dp2 = pump.pressure_gain(0.1)
        
        assert dp1 == dp2 == 15000.0
    
    def test_pump_power_calculation(self):
        """Should calculate power requirement"""
        pump = PumpCurve(a=10000.0, b=-1000.0, c=-500.0)
        
        flow = 0.05  # m³/s
        dp_pa = pump.pressure_gain(flow)  # Pascals
        
        # Power = Q * dp (W)
        power = flow * dp_pa
        
        assert power > 0
        assert power == pytest.approx(497.4375, rel=0.01)


class TestValveModels:
    """Test valve loss coefficient models"""
    
    def test_valve_creation(self):
        """Should create valve with loss coefficient"""
        valve = Valve(k=0.5)
        assert valve.k == 0.5
    
    def test_globe_valve_k_factor(self):
        """Globe valve has high K factor"""
        # Typical K for globe valve: 10
        valve = Valve(k=10.0)
        assert valve.k == 10.0
    
    def test_ball_valve_k_factor(self):
        """Ball valve has low K factor when open"""
        # Typical K for ball valve: 0.05
        valve = Valve(k=0.05)
        assert valve.k == 0.05
    
    def test_check_valve_k_factor(self):
        """Check valve has moderate K factor"""
        # Typical K for swing check valve: 2.0
        valve = Valve(k=2.0)
        assert valve.k == 2.0
    
    def test_valve_pressure_drop_calculation(self):
        """Should calculate pressure drop across valve"""
        valve = Valve(k=1.0)
        
        # dp = K * (rho * v^2 / 2)
        rho = 998.0  # kg/m³ (water)
        velocity = 1.0  # m/s
        
        dp = valve.pressure_drop(rho, velocity)
        expected = 1.0 * (998.0 * 1.0**2 / 2)
        
        assert dp == pytest.approx(expected)
    
    def test_valve_pressure_drop_with_high_velocity(self):
        """Pressure drop is proportional to velocity squared"""
        valve = Valve(k=1.0)
        rho = 998.0
        
        dp1 = valve.pressure_drop(rho, 1.0)
        dp2 = valve.pressure_drop(rho, 2.0)
        
        # Doubling velocity should quadruple pressure drop
        assert dp2 == pytest.approx(4 * dp1)
    
    def test_valve_pressure_drop_with_different_fluids(self):
        """Pressure drop depends on fluid density"""
        valve = Valve(k=1.0)
        velocity = 1.0
        
        # Water vs oil
        dp_water = valve.pressure_drop(998.0, velocity)
        dp_oil = valve.pressure_drop(850.0, velocity)
        
        # Heavier fluid (water) has more pressure drop
        assert dp_water > dp_oil


class TestFluidProperties:
    """Test fluid property calculations and temperature effects"""
    
    def test_water_default_properties(self):
        """Should have water as default fluid"""
        water = Fluid()
        
        assert water.density == 998.0
        assert water.viscosity == 1e-3
        assert water.temperature_c is None
    
    def test_water_at_20c(self):
        """Should track temperature of fluid"""
        water = Fluid(
            density=998.0,
            viscosity=1.002e-3,
            temperature_c=20
        )
        
        assert water.temperature_c == 20
    
    def test_effective_density_at_reference_temp(self):
        """Should return reference density at reference temperature"""
        fluid = Fluid(
            density=998.0,
            reference_temperature_c=20.0,
            temperature_c=20.0
        )
        
        eff_density = fluid.effective_density()
        assert eff_density == pytest.approx(998.0)
    
    def test_effective_density_temperature_dependent(self):
        """Density should decrease with temperature"""
        fluid = Fluid(
            reference_density=998.0,
            reference_temperature_c=20.0,
            temperature_c=30.0,  # 10°C higher
            thermal_expansion_coeff=0.0003
        )
        
        eff_density = fluid.effective_density()
        # At 30°C, density should be lower than 998
        assert eff_density < 998.0
    
    def test_effective_viscosity_at_reference_temp(self):
        """Should return reference viscosity at reference temperature"""
        fluid = Fluid(
            viscosity=1e-3,
            reference_viscosity=1e-3,
            reference_temperature_c=20.0,
            temperature_c=20.0
        )
        
        eff_visc = fluid.effective_viscosity()
        assert eff_visc == pytest.approx(1e-3)
    
    def test_effective_viscosity_temperature_dependent(self):
        """Viscosity should decrease with temperature"""
        fluid = Fluid(
            reference_viscosity=1e-3,
            reference_temperature_c=20.0,
            temperature_c=40.0,  # 20°C higher
            viscosity_temp_coeff=0.02
        )
        
        eff_visc = fluid.effective_viscosity()
        # Higher temperature should give lower viscosity
        assert eff_visc < 1e-3
    
    def test_oil_properties(self):
        """Should create oil fluid properties"""
        oil = Fluid(
            density=850.0,
            viscosity=32e-3,  # Much higher than water
            temperature_c=40
        )
        
        assert oil.density == 850.0
        assert oil.viscosity > 30 * 1e-3  # Much more viscous
    
    def test_kinematic_viscosity_calculation(self):
        """Should calculate kinematic viscosity (nu = mu / rho)"""
        fluid = Fluid(density=998.0, viscosity=1.002e-3)
        
        # Calculate kinematic viscosity manually
        nu = fluid.viscosity / fluid.density
        
        assert nu > 0
        assert nu == pytest.approx(1.004e-6, rel=0.01)


class TestEquipmentInNetwork:
    """Test equipment integration into pipe networks"""
    
    def test_pump_curve_in_pipe(self):
        """Should assign pump curve to pipe"""
        pump = PumpCurve(a=10000.0, b=-1000.0, c=-500.0)
        
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,  # 50mm in meters
            roughness=0.000045,
            pump_curve=pump
        )
        
        assert pipe.pump_curve is pump
        assert pipe.pump_curve.pressure_gain(0.05) > 0
    
    def test_valve_in_pipe(self):
        """Should assign valve to pipe"""
        valve = Valve(k=1.0)
        
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            valve=valve
        )
        
        assert pipe.valve is valve
    
    def test_pump_node_in_network(self):
        """Should represent pump as node in network"""
        network = PipeNetwork()
        
        pump_node = Node(
            id='PUMP',
            is_pump=True,
            pressure_ratio=1.5
        )
        
        network.add_node(pump_node)
        
        assert network.nodes['PUMP'].is_pump is True
        assert network.nodes['PUMP'].pressure_ratio == 1.5
    
    def test_valve_node_in_network(self):
        """Should represent valve as node in network"""
        network = PipeNetwork()
        
        valve_node = Node(
            id='VALVE',
            is_valve=True,
            valve_k=0.5
        )
        
        network.add_node(valve_node)
        
        assert network.nodes['VALVE'].is_valve is True
        assert network.nodes['VALVE'].valve_k == 0.5
    
    def test_simple_pump_network(self):
        """Should create simple pump-fed network"""
        network = PipeNetwork()
        fluid = Fluid(density=998.0, viscosity=1e-3)
        
        # Source pump node
        pump_node = Node(id='PUMP', is_pump=True, is_source=True)
        network.add_node(pump_node)
        
        # Destination sink node
        sink_node = Node(id='SINK', is_sink=True)
        network.add_node(sink_node)
        
        # Connecting pipe with pump curve
        pump_curve = PumpCurve(a=10000.0, b=-1000.0, c=-500.0)
        pipe = Pipe(
            id='P1',
            start_node='PUMP',
            end_node='SINK',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            pump_curve=pump_curve
        )
        network.add_pipe(pipe)
        
        assert len(network.nodes) == 2
        assert len(network.pipes) == 1
        assert network.pipes['P1'].pump_curve is not None


class TestEquipmentEdgeCases:
    """Test edge cases in equipment behavior"""
    
    def test_pump_at_shutoff(self):
        """Should handle pump at shutoff (zero flow)"""
        pump = PumpCurve(a=10000.0, b=-1000.0, c=-500.0)
        
        dp_shutoff = pump.pressure_gain(0.0)
        assert dp_shutoff == 10000.0  # Maximum pressure
    
    def test_pump_high_flow(self):
        """Should handle pump at high flow"""
        pump = PumpCurve(a=10000.0, b=-1000.0, c=-500.0)
        
        dp_high_flow = pump.pressure_gain(0.2)
        # dp = 10000 - 1000*0.2 - 500*0.2^2
        expected = 10000.0 - (1000.0 * 0.2) - (500.0 * 0.2**2)
        
        assert dp_high_flow == pytest.approx(expected)
        assert dp_high_flow < 10000.0  # Lower than shutoff
    
    def test_valve_zero_velocity(self):
        """Should handle valve at zero velocity"""
        valve = Valve(k=1.0)
        
        dp = valve.pressure_drop(998.0, 0.0)
        assert dp == 0.0
    
    def test_valve_very_high_velocity(self):
        """Should calculate pressure drop at high velocity"""
        valve = Valve(k=1.0)
        
        dp = valve.pressure_drop(998.0, 10.0)  # 10 m/s
        expected = 1.0 * (998.0 * 10.0**2 / 2)
        
        assert dp == pytest.approx(expected)
        assert dp > 0
    
    def test_fluid_extreme_temperature(self):
        """Should handle extreme temperatures"""
        fluid = Fluid(
            reference_temperature_c=20.0,
            temperature_c=100.0  # Boiling point of water
        )
        
        eff_density = fluid.effective_density()
        assert eff_density > 0  # Must remain positive
    
    def test_multi_phase_fluid_initialization(self):
        """Should initialize multi-phase fluid properties"""
        fluid = Fluid(
            is_multiphase=True,
            liquid_density=998.0,
            gas_density=1.2,
            liquid_viscosity=1e-3,
            gas_viscosity=1.8e-5
        )
        
        assert fluid.is_multiphase is True
        assert fluid.liquid_density == 998.0
        assert fluid.gas_density == 1.2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
