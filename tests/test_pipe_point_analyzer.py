"""Tests for PipePointAnalyzer service.

Tests cover:
- Pipe analysis at multiple points
- Pressure drop calculation along pipe
- Velocity calculations
- Integration with pressure drop service
- Edge cases (zero flow, zero length)
"""

import pytest

from app.services.analysis import PipePointAnalyzer, PipePointData
from app.services.pressure import PressureDropService
from app.map.pipe import Pipe
from app.models.fluid import Fluid


@pytest.fixture
def fluid():
    """Standard water properties"""
    return Fluid(density=998.0, viscosity=1e-3)


@pytest.fixture
def dp_service(fluid):
    """Pressure drop service for tests"""
    return PressureDropService(fluid)


@pytest.fixture
def analyzer(dp_service):
    """Pipe point analyzer"""
    return PipePointAnalyzer(dp_service)


class TestPipePointDataBasics:
    """Test PipePointData class"""
    
    def test_pipe_point_data_creation(self):
        """Should create pipe point data"""
        data = PipePointData(
            distance=50.0,
            pressure=100000.0,
            velocity=1.5,
            pressure_drop=5000.0
        )
        
        assert data.distance == 50.0
        assert data.pressure == 100000.0
        assert data.velocity == 1.5
        assert data.pressure_drop == 5000.0
    
    def test_pipe_point_data_at_start(self):
        """Should represent data at pipe start"""
        data = PipePointData(
            distance=0.0,
            pressure=200000.0,
            velocity=2.0,
            pressure_drop=0.0  # No drop at start
        )
        
        assert data.distance == 0.0
        assert data.pressure_drop == 0.0
    
    def test_pipe_point_data_at_end(self):
        """Should represent data at pipe end"""
        data = PipePointData(
            distance=100.0,
            pressure=190000.0,
            velocity=2.0,
            pressure_drop=10000.0
        )
        
        assert data.distance == 100.0
        assert data.pressure < 200000.0  # Pressure dropped


class TestAnalyzerBasics:
    """Test basic analyzer functionality"""
    
    def test_analyzer_creation(self, analyzer):
        """Should create analyzer with service"""
        assert analyzer is not None
        assert analyzer.service is not None
    
    def test_analyze_pipe_with_flow(self, analyzer):
        """Should analyze pipe with flow"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0)
        
        assert len(results) > 0
        assert all(isinstance(r, PipePointData) for r in results)
    
    def test_analyze_pipe_zero_flow(self, analyzer):
        """Should handle pipe with zero flow"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=None  # No flow
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0)
        
        assert results == []
    
    def test_analyze_pipe_default_num_points(self, analyzer):
        """Should use default number of analysis points"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0)
        
        # Default should be 4 points
        assert len(results) == 4


class TestAnalyzerPointCounts:
    """Test different numbers of analysis points"""
    
    def test_analyze_with_2_points(self, analyzer):
        """Should analyze at minimum 2 points (start and end)"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=2)
        
        assert len(results) == 2
        assert results[0].distance == 0.0  # Start
        assert results[1].distance == 100.0  # End
    
    def test_analyze_with_5_points(self, analyzer):
        """Should analyze at 5 points"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=5)
        
        assert len(results) == 5
    
    def test_analyze_with_10_points(self, analyzer):
        """Should analyze at 10 points"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=10)
        
        assert len(results) == 10
    
    def test_analyze_enforces_minimum_points(self, analyzer):
        """Should enforce minimum of 2 points even if 1 requested"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=1)
        
        assert len(results) == 2  # Minimum enforced


class TestAnalyzerDistances:
    """Test distance calculations along pipe"""
    
    def test_distances_start_at_zero(self, analyzer):
        """First point should be at distance 0"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=4)
        
        assert results[0].distance == 0.0
    
    def test_distances_end_at_length(self, analyzer):
        """Last point should be at pipe length"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=4)
        
        assert results[-1].distance == pytest.approx(100.0)
    
    def test_distances_evenly_spaced(self, analyzer):
        """Distances should be evenly spaced"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=5)
        
        # Distances should be: 0, 25, 50, 75, 100
        expected_distances = [0, 25, 50, 75, 100]
        for i, expected in enumerate(expected_distances):
            assert results[i].distance == pytest.approx(expected)


class TestAnalyzerPressure:
    """Test pressure calculations"""
    
    def test_pressure_decreases_along_pipe(self, analyzer):
        """Pressure should decrease with distance"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=4)
        
        # Pressure at start
        start_pressure = results[0].pressure
        # Pressure at end
        end_pressure = results[-1].pressure
        
        assert end_pressure < start_pressure
    
    def test_pressure_at_start_point(self, analyzer):
        """Pressure at start should match input"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        start_pressure = 150000.0
        results = analyzer.analyze_pipe(pipe, start_pressure=start_pressure, num_points=2)
        
        # Start point should have initial pressure
        assert results[0].pressure == pytest.approx(start_pressure, rel=0.01)
    
    def test_pressure_monotonically_decreasing(self, analyzer):
        """Pressure should monotonically decrease"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=10)
        
        # Each point should have lower or equal pressure than previous
        for i in range(len(results) - 1):
            assert results[i].pressure >= results[i+1].pressure


class TestAnalyzerVelocity:
    """Test velocity calculations"""
    
    def test_velocity_constant_along_pipe(self, analyzer):
        """Velocity should be constant along pipe (incompressible flow)"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=5)
        
        # All velocities should be nearly equal
        velocities = [r.velocity for r in results]
        for v in velocities[1:]:
            assert v == pytest.approx(velocities[0])
    
    def test_velocity_from_flow_rate(self, analyzer):
        """Velocity should be calculated from flow rate"""
        flow_rate = 0.05  # m³/s
        diameter = 0.05  # m
        
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=diameter,
            roughness=0.000045,
            flow_rate=flow_rate
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=2)
        
        # Check velocity is reasonable
        assert results[0].velocity > 0


class TestAnalyzerPressureDrop:
    """Test pressure drop calculations"""
    
    def test_pressure_drop_at_start(self, analyzer):
        """Pressure drop at start should be zero"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=2)
        
        assert results[0].pressure_drop == pytest.approx(0.0, abs=1)
    
    def test_pressure_drop_increases(self, analyzer):
        """Pressure drop should increase with distance"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=5)
        
        # Pressure drop should increase or stay same
        for i in range(len(results) - 1):
            assert results[i].pressure_drop <= results[i+1].pressure_drop
    
    def test_pressure_drop_zero_length_pipe(self, analyzer):
        """Should handle zero-length pipe gracefully"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=0.0,  # Zero length
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=2)
        
        # Should still return results
        assert len(results) > 0


class TestAnalyzerDifferentPipeSizes:
    """Test analysis with different pipe sizes"""
    
    def test_analyze_small_diameter_pipe(self, analyzer):
        """Should analyze small diameter pipe"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.01,  # 10mm
            roughness=0.000045,
            flow_rate=0.001  # Small flow
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=3)
        
        assert len(results) == 3
        # Smaller pipe should have more pressure drop
        assert results[-1].pressure < results[0].pressure
    
    def test_analyze_large_diameter_pipe(self, analyzer):
        """Should analyze large diameter pipe"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.5,  # 500mm
            roughness=0.000045,
            flow_rate=0.5  # Large flow
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=3)
        
        assert len(results) == 3
    
    def test_analyze_long_pipe(self, analyzer):
        """Should analyze long pipe"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=1000.0,  # 1km
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=5)
        
        assert len(results) == 5
        # Long pipe should have significant pressure drop
        assert results[-1].pressure < results[0].pressure - 1000


class TestAnalyzerDifferentFluids:
    """Test analysis with different fluids"""
    
    def test_analyze_with_oil(self):
        """Should analyze with oil fluid"""
        oil = Fluid(density=850.0, viscosity=50e-3)
        dp_service = PressureDropService(oil)
        analyzer = PipePointAnalyzer(dp_service)
        
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=3)
        
        assert len(results) == 3
    
    def test_analyze_with_different_viscosities(self):
        """Should handle different fluid viscosities"""
        # Low viscosity
        fluid_low = Fluid(density=998.0, viscosity=1e-4)
        analyzer_low = PipePointAnalyzer(PressureDropService(fluid_low))
        
        # High viscosity
        fluid_high = Fluid(density=998.0, viscosity=1e-1)
        analyzer_high = PipePointAnalyzer(PressureDropService(fluid_high))
        
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        results_low = analyzer_low.analyze_pipe(pipe, start_pressure=100000.0, num_points=2)
        results_high = analyzer_high.analyze_pipe(pipe, start_pressure=100000.0, num_points=2)
        
        assert len(results_low) == 2
        assert len(results_high) == 2


class TestAnalyzerEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_analyze_very_high_flow(self, analyzer):
        """Should handle very high flow rates"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=1.0  # 1 m³/s
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=2)
        
        assert len(results) == 2
        # High flow should have significant pressure drop
        assert results[-1].pressure < results[0].pressure
    
    def test_analyze_very_low_flow(self, analyzer):
        """Should handle very low flow rates"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.001  # 0.001 m³/s
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=100000.0, num_points=2)
        
        assert len(results) == 2
    
    def test_analyze_high_pressure(self, analyzer):
        """Should handle high pressure values"""
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.05
        )
        
        results = analyzer.analyze_pipe(pipe, start_pressure=10e6, num_points=2)  # 10 MPa
        
        assert len(results) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
