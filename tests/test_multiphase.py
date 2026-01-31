import pytest
import logging
from app.map.pipe import Pipe
from app.models.fluid import Fluid
from app.services.pressure_drop_service import PressureDropService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s', force=True)
logger = logging.getLogger(__name__)


class TestMultiPhaseFlow:
    """Tests for multi-phase flow pressure drop calculations"""

    def test_multiphase_fluid_initialization(self):
        """Test creating a multi-phase fluid with custom properties"""
        fluid = Fluid(
            is_multiphase=True,
            liquid_density=1000.0,
            gas_density=1.2,
            liquid_viscosity=1e-3,
            gas_viscosity=1.8e-5,
            surface_tension=0.072
        )
        
        assert fluid.is_multiphase is True
        assert fluid.liquid_density == 1000.0
        assert fluid.gas_density == 1.2
        assert fluid.liquid_viscosity == 1e-3
        assert fluid.gas_viscosity == 1.8e-5
        assert fluid.surface_tension == 0.072

    def test_multiphase_pipe_initialization(self):
        """Test creating a pipe with multi-phase flow rates"""
        pipe = Pipe(
            id="test_pipe",
            start_node="A",
            end_node="B",
            length=100.0,
            diameter=0.1,
            roughness=0.005,
            liquid_flow_rate=0.01,
            gas_flow_rate=0.005
        )
        
        assert pipe.liquid_flow_rate == 0.01
        assert pipe.gas_flow_rate == 0.005

    def test_multiphase_pressure_drop_calculation(self):
        """Test pressure drop calculation for two-phase flow"""
        fluid = Fluid(
            is_multiphase=True,
            liquid_density=998.0,
            gas_density=1.2,
            liquid_viscosity=1e-3,
            gas_viscosity=1.8e-5,
            surface_tension=0.072
        )
        
        service = PressureDropService(fluid)
        
        pipe = Pipe(
            id="test_pipe",
            start_node="A",
            end_node="B",
            length=100.0,
            diameter=0.1,
            roughness=0.005,
            liquid_flow_rate=0.01,
            gas_flow_rate=0.005
        )
        
        dp = service.calculate_pipe_dp(pipe)
        
        assert dp > 0, "Pressure drop should be positive"
        assert pipe.pressure_drop == dp, "Pipe should store calculated pressure drop"
        logger.info(f"Calculated multi-phase pressure drop: {dp:.2f} Pa")

    def test_multiphase_high_gas_fraction(self):
        """Test pressure drop with high gas volume fraction"""
        fluid = Fluid(
            is_multiphase=True,
            liquid_density=998.0,
            gas_density=1.2,
            liquid_viscosity=1e-3,
            gas_viscosity=1.8e-5,
            surface_tension=0.072
        )
        
        service = PressureDropService(fluid)
        
        pipe = Pipe(
            id="test_pipe",
            start_node="A",
            end_node="B",
            length=100.0,
            diameter=0.1,
            roughness=0.005,
            liquid_flow_rate=0.001,  # Low liquid
            gas_flow_rate=0.020      # High gas
        )
        
        dp = service.calculate_pipe_dp(pipe)
        
        assert dp > 0, "Pressure drop should be positive even with high gas fraction"
        logger.info(f"High gas fraction pressure drop: {dp:.2f} Pa")

    def test_multiphase_high_liquid_fraction(self):
        """Test pressure drop with high liquid volume fraction"""
        fluid = Fluid(
            is_multiphase=True,
            liquid_density=998.0,
            gas_density=1.2,
            liquid_viscosity=1e-3,
            gas_viscosity=1.8e-5,
            surface_tension=0.072
        )
        
        service = PressureDropService(fluid)
        
        pipe = Pipe(
            id="test_pipe",
            start_node="A",
            end_node="B",
            length=100.0,
            diameter=0.1,
            roughness=0.005,
            liquid_flow_rate=0.020,  # High liquid
            gas_flow_rate=0.001      # Low gas
        )
        
        dp = service.calculate_pipe_dp(pipe)
        
        assert dp > 0, "Pressure drop should be positive with high liquid fraction"
        logger.info(f"High liquid fraction pressure drop: {dp:.2f} Pa")

    def test_multiphase_zero_gas_flow(self):
        """Test pressure drop with zero gas flow (essentially single-phase liquid)"""
        fluid = Fluid(
            is_multiphase=True,
            liquid_density=998.0,
            gas_density=1.2,
            liquid_viscosity=1e-3,
            gas_viscosity=1.8e-5,
            surface_tension=0.072
        )
        
        service = PressureDropService(fluid)
        
        pipe = Pipe(
            id="test_pipe",
            start_node="A",
            end_node="B",
            length=100.0,
            diameter=0.1,
            roughness=0.005,
            liquid_flow_rate=0.01,
            gas_flow_rate=0.0  # No gas
        )
        
        dp = service.calculate_pipe_dp(pipe)
        
        assert dp > 0, "Pressure drop should be positive"
        logger.info(f"Zero gas flow pressure drop: {dp:.2f} Pa")

    def test_multiphase_missing_flow_rates(self):
        """Test that error is raised when flow rates are missing"""
        fluid = Fluid(is_multiphase=True)
        service = PressureDropService(fluid)
        
        pipe = Pipe(
            id="test_pipe",
            start_node="A",
            end_node="B",
            length=100.0,
            diameter=0.1,
            roughness=0.005
            # Missing liquid_flow_rate and gas_flow_rate
        )
        
        with pytest.raises(ValueError, match="needs liquid_flow_rate and gas_flow_rate"):
            service.calculate_pipe_dp(pipe)

    def test_single_phase_still_works(self):
        """Ensure single-phase calculations still work after multi-phase implementation"""
        fluid = Fluid(
            is_multiphase=False,
            density=998.0,
            viscosity=1e-3
        )
        
        service = PressureDropService(fluid)
        
        pipe = Pipe(
            id="test_pipe",
            start_node="A",
            end_node="B",
            length=100.0,
            diameter=0.1,
            roughness=0.005,
            flow_rate=0.01
        )
        
        dp = service.calculate_pipe_dp(pipe)
        
        assert dp > 0, "Single-phase pressure drop should be positive"
        logger.info(f"Single-phase pressure drop: {dp:.2f} Pa")

    def test_multiphase_vs_single_phase_comparison(self):
        """Compare multi-phase and single-phase calculations for reference"""
        # Single-phase liquid
        fluid_single = Fluid(
            is_multiphase=False,
            density=998.0,
            viscosity=1e-3
        )
        
        service_single = PressureDropService(fluid_single)
        
        pipe_single = Pipe(
            id="single",
            start_node="A",
            end_node="B",
            length=100.0,
            diameter=0.1,
            roughness=0.005,
            flow_rate=0.01
        )
        
        dp_single = service_single.calculate_pipe_dp(pipe_single)
        
        # Multi-phase (all liquid, no gas)
        fluid_multi = Fluid(
            is_multiphase=True,
            liquid_density=998.0,
            gas_density=1.2,
            liquid_viscosity=1e-3,
            gas_viscosity=1.8e-5
        )
        
        service_multi = PressureDropService(fluid_multi)
        
        pipe_multi = Pipe(
            id="multi",
            start_node="A",
            end_node="B",
            length=100.0,
            diameter=0.1,
            roughness=0.005,
            liquid_flow_rate=0.01,
            gas_flow_rate=0.0
        )
        
        dp_multi = service_multi.calculate_pipe_dp(pipe_multi)
        
        logger.info(f"Single-phase dp: {dp_single:.2f} Pa")
        logger.info(f"Multi-phase dp (no gas): {dp_multi:.2f} Pa")
        
        # They should be similar (not exact due to slight implementation differences)
        assert abs(dp_single - dp_multi) / dp_single < 0.1, "Similar flow should give similar results"
