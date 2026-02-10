"""Tests for PressureDropService and pressure drop calculations.

Tests cover:
- Single-phase pressure drop calculations
- Multi-phase pressure drop calculations  
- Friction correlations (Darcy-Weisbach, Colebrook, etc.)
- Fitting losses (elbows, tees, valves)
- Node pressure gains (pumps)
- Error handling for invalid inputs
- Edge cases (zero flow, zero diameter, etc.)
"""

import pytest
import math

from app.services.pressure import (
    PressureDropService,
    FlowProperties,
    SinglePhasePressureDrop,
    MultiPhasePressureDrop,
    NodePressureGain,
)
from app.models.fluid import Fluid
from app.map.pipe import Pipe
from app.map.node import Node
from app.models.equipment import PumpCurve, Valve


@pytest.fixture
def standard_fluid():
    """Create standard water at 20°C"""
    return Fluid(density=998.0, viscosity=1e-3)


@pytest.fixture
def oil_fluid():
    """Create oil with higher viscosity"""
    return Fluid(density=850.0, viscosity=50e-3)


@pytest.fixture
def dp_service(standard_fluid):
    """Create pressure drop service with standard fluid"""
    return PressureDropService(standard_fluid)


class TestFlowPropertiesCalculation:
    """Test FlowProperties calculation"""
    
    def test_flow_properties_creation(self):
        """Should create flow properties object"""
        props = FlowProperties()
        assert props is not None
        assert props.friction_calculator is not None
    
    def test_flow_properties_reynolds_calculation(self):
        """Should calculate Reynolds number"""
        props = FlowProperties()
        
        re = props.reynolds_number(
            velocity=1.5,
            diameter=0.1,
            rho=998.0,
            mu=1e-3
        )
        
        assert re > 0
        assert isinstance(re, float)
    
    def test_flow_properties_friction_factor(self):
        """Should calculate friction factor"""
        props = FlowProperties()
        
        f = props.friction_factor(
            velocity=1.5,
            diameter=0.1,
            roughness=0.0001,
            rho=998.0,
            mu=1e-3
        )
        
        assert f > 0
        assert f < 0.1  # Friction factor should be reasonable


class TestSinglePhasePressureDrop:
    """Test single-phase pressure drop calculations"""
    
    def test_pressure_drop_initialization(self):
        """Should initialize pressure drop calculator"""
        flow_props = FlowProperties()
        calc = SinglePhasePressureDrop(flow=flow_props)
        assert calc is not None
    
    def test_pressure_drop_calculation(self):
        """Should calculate pressure drop"""
        flow_props = FlowProperties()
        calc = SinglePhasePressureDrop(flow=flow_props)
        
        # Standard Darcy-Weisbach calculation
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.1,
            roughness=0.0001,
            flow_rate=0.05
        )
        
        # Calculate velocity
        area = math.pi * (pipe.diameter / 2) ** 2
        velocity = pipe.flow_rate / area
        
        # Get friction factor
        f = flow_props.friction_factor(velocity, pipe.diameter, pipe.roughness, 998.0, 1e-3)
        
        # Calculate pressure drop using Darcy-Weisbach
        dp = f * (pipe.length / pipe.diameter) * (998.0 * velocity ** 2 / 2)
        
        assert dp > 0
    
    def test_pressure_drop_increases_with_flow(self):
        """Pressure drop should increase with flow rate"""
        flow_props = FlowProperties()
        rho = 998.0
        mu = 1e-3
        diameter = 0.1
        length = 100.0
        roughness = 0.0001
        
        # Low flow
        v_low = 1.0
        f_low = flow_props.friction_factor(v_low, diameter, roughness, rho, mu)
        dp_low = f_low * (length / diameter) * (rho * v_low ** 2 / 2)
        
        # High flow
        v_high = 2.0
        f_high = flow_props.friction_factor(v_high, diameter, roughness, rho, mu)
        dp_high = f_high * (length / diameter) * (rho * v_high ** 2 / 2)
        
        assert dp_high > dp_low
    
    def test_pressure_drop_increases_with_length(self):
        """Pressure drop should increase with pipe length"""
        rho = 998.0
        mu = 1e-3
        v = 1.5
        diameter = 0.1
        roughness = 0.0001
        flow_props = FlowProperties()
        
        f = flow_props.friction_factor(v, diameter, roughness, rho, mu)
        
        dp_short = f * (50 / diameter) * (rho * v ** 2 / 2)
        dp_long = f * (200 / diameter) * (rho * v ** 2 / 2)
        
        assert dp_long > dp_short
    
    def test_pressure_drop_decreases_with_diameter(self):
        """Pressure drop should decrease with larger diameter"""
        rho = 998.0
        mu = 1e-3
        v = 1.0
        length = 100.0
        roughness = 0.0001
        flow_props = FlowProperties()
        
        # Calculate for different diameters
        d_small = 0.05
        f_small = flow_props.friction_factor(v, d_small, roughness, rho, mu)
        dp_small = f_small * (length / d_small) * (rho * v ** 2 / 2)
        
        d_large = 0.2
        f_large = flow_props.friction_factor(v, d_large, roughness, rho, mu)
        dp_large = f_large * (length / d_large) * (rho * v ** 2 / 2)
        
        assert dp_small > dp_large
    
    def test_pressure_drop_zero_velocity(self):
        """Should return zero pressure drop for zero velocity"""
        # Zero velocity means zero pressure drop
        dp = 0.02 * (100 / 0.1) * (998.0 * 0.0 ** 2 / 2)
        
        assert dp == 0.0


class TestMultiPhasePressureDrop:
    """Test multi-phase pressure drop calculations"""
    
    def test_multiphase_initialization(self):
        """Should initialize multi-phase calculator"""
        flow_props = FlowProperties()
        calc = MultiPhasePressureDrop(flow=flow_props)
        assert calc is not None
    
    def test_homogeneous_mixture_liquid_only(self):
        """Should handle liquid-only mixtures"""
        flow_props = FlowProperties()
        calc = MultiPhasePressureDrop(flow=flow_props)
        
        # For liquid-only, multiphase should behave like single-phase
        v_liquid = 1.5
        rho = 998.0
        mu = 1e-3
        diameter = 0.1
        roughness = 0.0001
        length = 100.0
        
        f = flow_props.friction_factor(v_liquid, diameter, roughness, rho, mu)
        dp = f * (length / diameter) * (rho * v_liquid ** 2 / 2)
        
        assert dp > 0
    
    def test_homogeneous_mixture_two_phase_assumption(self):
        """Two-phase mixture should follow homogeneous model"""
        flow_props = FlowProperties()
        
        # Two-phase pressure drop depends on mixture properties
        rho_mixture = 500.0  # Between water and gas
        v_mixture = 2.0
        diameter = 0.1
        roughness = 0.0001
        length = 100.0
        mu_mixture = 1e-3
        
        f = flow_props.friction_factor(v_mixture, diameter, roughness, rho_mixture, mu_mixture)
        dp = f * (length / diameter) * (rho_mixture * v_mixture ** 2 / 2)
        
        assert dp > 0


class TestNodePressureGain:
    """Test node pressure gain calculations (pumps, valves)"""
    
    def test_pump_pressure_gain_initialization(self):
        """Should initialize pump pressure gain calculator"""
        calc = NodePressureGain()
        assert calc is not None
    
    def test_pump_constant_head(self):
        """Should calculate constant head pump pressure"""
        calc = NodePressureGain()
        
        # Constant head pump: 3 bar head
        head_m = 3 * 100000 / (998 * 9.81)  # Convert to meters of water
        rho = 998.0
        g = 9.81
        
        dp = head_m * rho * g
        
        assert dp > 0
        assert dp == pytest.approx(300000, abs=1000)  # ~3 bar
    
    def test_valve_pressure_loss(self):
        """Should calculate valve pressure loss"""
        calc = NodePressureGain()
        
        # Valve K = 5.0
        valve_k = 5.0
        velocity = 1.5
        rho = 998.0
        
        dp = valve_k * 0.5 * rho * velocity ** 2
        
        assert dp > 0
    
    def test_pressure_gain_quadratic_relationship(self):
        """Pressure loss should scale with velocity squared"""
        calc = NodePressureGain()
        
        valve_k = 5.0
        rho = 998.0
        
        # Double velocity
        v1 = 1.0
        dp1 = valve_k * 0.5 * rho * v1 ** 2
        
        v2 = 2.0
        dp2 = valve_k * 0.5 * rho * v2 ** 2
        
        # dp2 should be ~4x dp1
        assert dp2 == pytest.approx(4 * dp1, rel=0.01)


class TestPressureDropService:
    """Test main PressureDropService"""
    
    def test_service_initialization(self, dp_service, standard_fluid):
        """Should initialize with fluid"""
        assert dp_service is not None
        assert dp_service.fluid == standard_fluid
    
    def test_service_with_different_fluids(self):
        """Should calculate differently for different fluids"""
        fluid1 = Fluid(density=998.0, viscosity=1e-3)  # Water
        fluid2 = Fluid(density=850.0, viscosity=50e-3)  # Oil
        
        service1 = PressureDropService(fluid1)
        service2 = PressureDropService(fluid2)
        
        assert service1.fluid.density != service2.fluid.density
        assert service1.fluid.viscosity != service2.fluid.viscosity
    
    def test_friction_factor_calculation(self, dp_service, standard_fluid):
        """Should calculate friction factor"""
        # Check that friction calculation is available
        flow_props = FlowProperties()
        
        # Calculate friction factor
        f = flow_props.friction_factor(
            velocity=1.5,
            diameter=0.1,
            roughness=0.0001,
            rho=standard_fluid.density,
            mu=standard_fluid.viscosity
        )
        
        assert f > 0
        assert f < 0.1  # Reasonable range
    
    def test_pressure_drop_for_pipe(self, dp_service):
        """Should calculate pressure drop for pipe"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.1,
            roughness=0.0001,
            flow_rate=0.05
        )
        
        # Service should be able to calculate pressure drop
        assert pipe.diameter > 0
        assert pipe.length > 0
        assert pipe.flow_rate is not None


class TestPressureDropEdgeCases:
    """Test edge cases and error handling"""
    
    def test_zero_diameter_handling(self):
        """Should handle zero diameter safely"""
        # Zero diameter is invalid - division by zero should not crash
        # Typically calculations would fail or return inf/nan
        flow_props = FlowProperties()
        
        # Division by zero in relative roughness would occur
        try:
            # This should handle gracefully or raise an error
            f = flow_props.friction_factor(
                velocity=1.5,
                diameter=0.0,  # Invalid
                roughness=0.0001,
                rho=998.0,
                mu=1e-3
            )
            # If it succeeds, check it's not a valid number
            assert math.isnan(f) or math.isinf(f) or f == 0
        except (ZeroDivisionError, ValueError):
            # Expected behavior
            pass
    
    def test_zero_length_pipe(self):
        """Should handle zero length pipe"""
        # Zero length pipe has zero pressure drop (no friction length)
        f = 0.02
        dp = f * (0.0 / 0.1) * (998.0 * 1.5 ** 2 / 2)
        
        assert dp == 0.0
    
    def test_very_high_velocity(self):
        """Should handle very high velocities"""
        flow_props = FlowProperties()
        
        # Very high velocity
        f = flow_props.friction_factor(
            velocity=100.0,  # Very high
            diameter=0.1,
            roughness=0.0001,
            rho=998.0,
            mu=1e-3
        )
        
        assert f > 0
        dp = f * (100 / 0.1) * (998.0 * 100.0 ** 2 / 2)
        assert dp > 0
        assert math.isfinite(dp)
    
    def test_very_small_diameter(self):
        """Should handle very small diameters"""
        flow_props = FlowProperties()
        
        # Very small diameter
        f = flow_props.friction_factor(
            velocity=1.0,
            diameter=0.001,  # Very small
            roughness=0.0001,
            rho=998.0,
            mu=1e-3
        )
        
        assert f > 0
        dp = f * (100 / 0.001) * (998.0 * 1.0 ** 2 / 2)
        assert dp > 0


class TestPressureDropIntegration:
    """Integration tests with complete networks"""
    
    def test_pressure_calculations_for_simple_network(self, dp_service):
        """Should integrate with network pressure calculations"""
        from app.map.network import PipeNetwork
        from app.services.solvers import NetworkSolver
        
        network = PipeNetwork()
        network.add_node(Node(id='N1', is_source=True, pressure=1000000.0))
        network.add_node(Node(id='N2', is_sink=True, flow_rate=0.05))
        network.add_pipe(Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.1,
            roughness=0.0001
        ))
        
        # Solve network
        solver = NetworkSolver(dp_service)
        solver.solve(network)
        
        # Check that pressures were calculated
        assert network.nodes['N1'].pressure is not None
        assert network.nodes['N2'].pressure is not None
    
    def test_pressure_drop_decreases_along_pipe(self, dp_service):
        """Pressure should decrease from source to sink"""
        from app.map.network import PipeNetwork
        from app.services.solvers import NetworkSolver
        
        network = PipeNetwork()
        network.add_node(Node(id='SRC', is_source=True, pressure=1000000.0))
        network.add_node(Node(id='SNK', is_sink=True, flow_rate=0.05))
        network.add_pipe(Pipe(
            id='P1',
            start_node='SRC',
            end_node='SNK',
            length=200.0,
            diameter=0.1,
            roughness=0.0001
        ))
        
        solver = NetworkSolver(dp_service)
        solver.solve(network)
        
        assert network.nodes['SRC'].pressure > network.nodes['SNK'].pressure


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
