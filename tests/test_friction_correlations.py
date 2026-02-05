"""Tests for friction factor correlations.

Tests all implemented friction factor calculation methods against known
values and verifies they produce reasonable results within expected ranges.
"""

import pytest
import math
from app.services.friction_correlations import (
    FrictionFactorCalculator,
    FrictionCorrelation,
    get_correlation_info
)


class TestFrictionFactorCalculator:
    """Test friction factor calculations."""
    
    def test_laminar_flow_all_correlations(self):
        """Laminar flow should give f = 64/Re for all correlations."""
        Re = 1000  # Laminar
        eps_D = 0.001
        
        for correlation in FrictionCorrelation:
            calc = FrictionFactorCalculator(correlation)
            f = calc.calculate(Re, eps_D)
            expected = 64.0 / Re
            assert abs(f - expected) < 1e-10, f"{correlation}: {f} != {expected}"
    
    def test_turbulent_smooth_pipe(self):
        """Test turbulent flow in smooth pipe (eps/D ≈ 0)."""
        Re = 100000
        eps_D = 1e-7  # Very smooth
        
        # All correlations should give similar results for smooth pipes
        results = {}
        for correlation in FrictionCorrelation:
            calc = FrictionFactorCalculator(correlation)
            results[correlation.value] = calc.calculate(Re, eps_D)
        
        # Check all results are in reasonable range (0.01 - 0.02 for smooth pipe, high Re)
        for name, f in results.items():
            assert 0.01 < f < 0.02, f"{name}: f={f} out of range"
    
    def test_turbulent_rough_pipe(self):
        """Test turbulent flow in rough pipe."""
        Re = 50000
        eps_D = 0.01  # Rough pipe
        
        results = {}
        for correlation in FrictionCorrelation:
            calc = FrictionFactorCalculator(correlation)
            results[correlation.value] = calc.calculate(Re, eps_D)
        
        # Rough pipes have higher friction factors
        for name, f in results.items():
            assert 0.02 < f < 0.10, f"{name}: f={f} out of range for rough pipe"
    
    def test_colebrook_white_convergence(self):
        """Test Colebrook-White iteration converges."""
        calc = FrictionFactorCalculator(FrictionCorrelation.COLEBROOK_WHITE)
        Re = 10000
        eps_D = 0.001
        
        f = calc.calculate(Re, eps_D)
        
        # Verify it converged to a reasonable value
        assert 0.015 < f < 0.050
        
        # Verify Colebrook-White equation is satisfied
        # 1/√f = -2 log₁₀(ε/D / 3.7 + 2.51 / (Re √f))
        inv_sqrt_f = 1.0 / math.sqrt(f)
        rhs = -2.0 * math.log10(eps_D / 3.7 + 2.51 / (Re * math.sqrt(f)))
        assert abs(inv_sqrt_f - rhs) < 1e-4
    
    def test_swamee_jain_accuracy(self):
        """Test Swamee-Jain against known Moody chart values."""
        # Test case: Re=10^5, ε/D=0.001
        Re = 100000
        eps_D = 0.001
        
        calc_sw = FrictionFactorCalculator(FrictionCorrelation.SWAMEE_JAIN)
        calc_cw = FrictionFactorCalculator(FrictionCorrelation.COLEBROOK_WHITE)
        
        f_sw = calc_sw.calculate(Re, eps_D)
        f_cw = calc_cw.calculate(Re, eps_D)
        
        # Swamee-Jain should be within 1% of Colebrook-White
        error = abs(f_sw - f_cw) / f_cw
        assert error < 0.01, f"Swamee-Jain error {error*100:.2f}% > 1%"
    
    def test_haaland_accuracy(self):
        """Test Haaland against Colebrook-White."""
        Re = 50000
        eps_D = 0.0005
        
        calc_h = FrictionFactorCalculator(FrictionCorrelation.HAALAND)
        calc_cw = FrictionFactorCalculator(FrictionCorrelation.COLEBROOK_WHITE)
        
        f_h = calc_h.calculate(Re, eps_D)
        f_cw = calc_cw.calculate(Re, eps_D)
        
        # Haaland should be within 1.5% of Colebrook-White
        error = abs(f_h - f_cw) / f_cw
        assert error < 0.015, f"Haaland error {error*100:.2f}% > 1.5%"
    
    def test_churchill_all_reynolds(self):
        """Test Churchill works for all Reynolds numbers."""
        calc = FrictionFactorCalculator(FrictionCorrelation.CHURCHILL)
        eps_D = 0.001
        
        # Test various Reynolds numbers including transitional
        test_Re = [500, 1000, 2000, 2500, 5000, 10000, 100000]
        
        for Re in test_Re:
            f = calc.calculate(Re, eps_D)
            assert f > 0, f"Invalid friction factor for Re={Re}"
            assert f < 0.2, f"Unreasonably high friction factor for Re={Re}"
    
    def test_serghides_accuracy(self):
        """Test Serghides very high accuracy."""
        Re = 75000
        eps_D = 0.002
        
        calc_s = FrictionFactorCalculator(FrictionCorrelation.SERGHIDES)
        calc_cw = FrictionFactorCalculator(FrictionCorrelation.COLEBROOK_WHITE)
        
        f_s = calc_s.calculate(Re, eps_D)
        f_cw = calc_cw.calculate(Re, eps_D)
        
        # Serghides should be within 0.2% of Colebrook-White
        error = abs(f_s - f_cw) / f_cw
        assert error < 0.002, f"Serghides error {error*100:.2f}% > 0.2%"
    
    def test_invalid_reynolds_number(self):
        """Test error handling for invalid Reynolds number."""
        calc = FrictionFactorCalculator(FrictionCorrelation.SWAMEE_JAIN)
        
        with pytest.raises(ValueError):
            calc.calculate(-1000, 0.001)
        
        with pytest.raises(ValueError):
            calc.calculate(0, 0.001)
    
    def test_consistency_across_correlations(self):
        """All correlations should give similar results for typical conditions."""
        Re = 30000
        eps_D = 0.0015
        
        results = []
        for correlation in FrictionCorrelation:
            calc = FrictionFactorCalculator(correlation)
            f = calc.calculate(Re, eps_D)
            results.append(f)
        
        # All results should be within 5% of each other for typical conditions
        f_mean = sum(results) / len(results)
        for f in results:
            deviation = abs(f - f_mean) / f_mean
            assert deviation < 0.05, f"Deviation {deviation*100:.1f}% too large"


class TestCorrelationInfo:
    """Test correlation information retrieval."""
    
    def test_get_correlation_info(self):
        """Test retrieving information about correlations."""
        info = get_correlation_info(FrictionCorrelation.COLEBROOK_WHITE)
        
        assert "name" in info
        assert "description" in info
        assert "valid_range" in info
        assert "accuracy" in info
        assert info["name"] == "Colebrook-White"
    
    def test_all_correlations_have_info(self):
        """All correlations should have information available."""
        for correlation in FrictionCorrelation:
            info = get_correlation_info(correlation)
            assert info != {}
            assert "name" in info
            assert "description" in info


class TestMoodyDiagramComparison:
    """Test against known Moody diagram values."""
    
    @pytest.mark.parametrize("Re,eps_D,f_expected", [
        (10000, 0.0001, 0.031037),   # Smooth pipe, moderate Re
        (100000, 0.0001, 0.018514),  # Smooth pipe, high Re
        (10000, 0.01, 0.043127),     # Rough pipe, moderate Re
        (100000, 0.001, 0.022175),   # Moderate roughness, high Re
    ])
    def test_moody_diagram_values(self, Re, eps_D, f_expected):
        """Compare against known Moody diagram values.
        
        Values taken from standard Moody diagram (approximate).
        """
        calc = FrictionFactorCalculator(FrictionCorrelation.COLEBROOK_WHITE)
        f = calc.calculate(Re, eps_D)
        
        # Allow 5% tolerance due to reading accuracy from Moody chart
        error = abs(f - f_expected) / f_expected
        assert error < 0.05, f"Re={Re}, ε/D={eps_D}: f={f:.4f}, expected≈{f_expected:.4f}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
