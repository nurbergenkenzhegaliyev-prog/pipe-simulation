"""Friction factor correlations for pipe flow calculations.

This module provides multiple correlations for calculating the Darcy-Weisbach
friction factor, allowing users to select the most appropriate method for their
application. Different correlations have varying accuracy and computational
efficiency for different flow regimes.

Correlations implemented:
- Colebrook-White (implicit, most accurate, current default)
- Swamee-Jain (explicit, good for rough pipes)
- Haaland (explicit, accurate approximation)
- Churchill (explicit, all Reynolds numbers)
- Serghides (explicit, very accurate)

Reference: Moody diagram and various fluid mechanics textbooks
"""

import math
from enum import Enum
from typing import Optional


class FrictionCorrelation(Enum):
    """Available friction factor correlation methods."""
    COLEBROOK_WHITE = "colebrook_white"
    SWAMEE_JAIN = "swamee_jain"
    HAALAND = "haaland"
    CHURCHILL = "churchill"
    SERGHIDES = "serghides"


class FrictionFactorCalculator:
    """Calculate Darcy-Weisbach friction factor using various correlations.
    
    Provides multiple methods for calculating friction factor, each with
    different characteristics in terms of accuracy, computational cost,
    and applicability range.
    
    Attributes:
        correlation: Selected correlation method
        max_iterations: Maximum iterations for implicit methods (default: 50)
        tolerance: Convergence tolerance for implicit methods (default: 1e-6)
        
    Example:
        >>> calc = FrictionFactorCalculator(FrictionCorrelation.SWAMEE_JAIN)
        >>> Re = 10000
        >>> relative_roughness = 0.001
        >>> f = calc.calculate(Re, relative_roughness)
        >>> print(f"Friction factor: {f:.6f}")
    """
    
    def __init__(
        self,
        correlation: FrictionCorrelation = FrictionCorrelation.COLEBROOK_WHITE,
        max_iterations: int = 50,
        tolerance: float = 1e-6
    ):
        """Initialize friction factor calculator.
        
        Args:
            correlation: Correlation method to use
            max_iterations: Max iterations for implicit methods
            tolerance: Convergence tolerance for implicit methods
        """
        self.correlation = correlation
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        
    def calculate(self, reynolds_number: float, relative_roughness: float) -> float:
        """Calculate friction factor for given conditions.
        
        Automatically handles laminar/turbulent transition and delegates
        to the appropriate correlation method.
        
        Args:
            reynolds_number: Reynolds number (dimensionless)
            relative_roughness: Relative roughness (ε/D, dimensionless)
            
        Returns:
            Darcy-Weisbach friction factor (dimensionless)
            
        Raises:
            ValueError: If Reynolds number is invalid or negative
            
        Example:
            >>> calc = FrictionFactorCalculator(FrictionCorrelation.HAALAND)
            >>> f = calc.calculate(Re=50000, relative_roughness=0.0002)
        """
        if reynolds_number <= 0:
            raise ValueError(f"Reynolds number must be positive, got {reynolds_number}")
        
        # Laminar flow (Re < 2300)
        if reynolds_number < 2300:
            return 64.0 / reynolds_number
        
        # Turbulent flow - use selected correlation
        if self.correlation == FrictionCorrelation.COLEBROOK_WHITE:
            return self._colebrook_white(reynolds_number, relative_roughness)
        elif self.correlation == FrictionCorrelation.SWAMEE_JAIN:
            return self._swamee_jain(reynolds_number, relative_roughness)
        elif self.correlation == FrictionCorrelation.HAALAND:
            return self._haaland(reynolds_number, relative_roughness)
        elif self.correlation == FrictionCorrelation.CHURCHILL:
            return self._churchill(reynolds_number, relative_roughness)
        elif self.correlation == FrictionCorrelation.SERGHIDES:
            return self._serghides(reynolds_number, relative_roughness)
        else:
            raise ValueError(f"Unknown correlation: {self.correlation}")
    
    def _colebrook_white(self, Re: float, eps_D: float) -> float:
        """Colebrook-White equation (implicit, iterative).
        
        Most accurate correlation, considered the standard. Requires
        iterative solution.
        
        Equation: 1/√f = -2 log₁₀(ε/D / 3.7 + 2.51 / (Re √f))
        
        Valid range: Re > 4000, all ε/D
        Accuracy: Reference standard (±0%)
        
        Args:
            Re: Reynolds number
            eps_D: Relative roughness (ε/D)
            
        Returns:
            Friction factor
        """
        # Initial guess using Haaland equation
        f = self._haaland(Re, eps_D)
        
        # Newton-Raphson iteration
        for _ in range(self.max_iterations):
            # Colebrook-White equation rearranged
            term1 = eps_D / 3.7
            term2 = 2.51 / (Re * math.sqrt(f))
            f_new = (-2.0 * math.log10(term1 + term2)) ** -2
            
            # Check convergence
            if abs(f_new - f) < self.tolerance:
                return f_new
            
            f = f_new
        
        return f  # Return last value if not converged
    
    def _swamee_jain(self, Re: float, eps_D: float) -> float:
        """Swamee-Jain equation (explicit).
        
        Explicit approximation to Colebrook-White, good for rough pipes.
        Simple and fast, widely used in practice.
        
        Equation: f = 0.25 / [log₁₀(ε/D / 3.7 + 5.74 / Re^0.9)]²
        
        Valid range: 5000 < Re < 10⁸, 10⁻⁶ < ε/D < 10⁻²
        Accuracy: ±1% vs Colebrook-White
        
        Args:
            Re: Reynolds number
            eps_D: Relative roughness (ε/D)
            
        Returns:
            Friction factor
        """
        numerator = eps_D / 3.7
        denominator = 5.74 / (Re ** 0.9)
        log_term = math.log10(numerator + denominator)
        return 0.25 / (log_term ** 2)
    
    def _haaland(self, Re: float, eps_D: float) -> float:
        """Haaland equation (explicit).
        
        Very accurate explicit approximation to Colebrook-White.
        Better than Swamee-Jain for smooth pipes.
        
        Equation: 1/√f = -1.8 log₁₀[(ε/D / 3.7)^1.11 + 6.9 / Re]
        
        Valid range: Re > 4000, all ε/D
        Accuracy: ±1.5% vs Colebrook-White
        
        Args:
            Re: Reynolds number
            eps_D: Relative roughness (ε/D)
            
        Returns:
            Friction factor
        """
        term1 = (eps_D / 3.7) ** 1.11
        term2 = 6.9 / Re
        log_term = math.log10(term1 + term2)
        inv_sqrt_f = -1.8 * log_term
        return (1.0 / inv_sqrt_f) ** 2
    
    def _churchill(self, Re: float, eps_D: float) -> float:
        """Churchill equation (explicit, all Reynolds numbers).
        
        Works for both laminar and turbulent flow, smooth transition.
        Good for wide range of conditions, including transitional flow.
        
        Equation: Complex, see Churchill (1977)
        
        Valid range: All Re > 0, all ε/D
        Accuracy: ±5% (slightly less accurate but more robust)
        
        Args:
            Re: Reynolds number
            eps_D: Relative roughness (ε/D)
            
        Returns:
            Friction factor
        """
        # Term A: Laminar contribution
        A = (2.457 * math.log(1.0 / ((7.0 / Re) ** 0.9 + 0.27 * eps_D))) ** 16
        
        # Term B: High Reynolds number contribution
        B = (37530.0 / Re) ** 16
        
        # Churchill correlation
        f = 8.0 * ((8.0 / Re) ** 12 + 1.0 / ((A + B) ** 1.5)) ** (1.0 / 12.0)
        
        return f
    
    def _serghides(self, Re: float, eps_D: float) -> float:
        """Serghides equation (explicit, very accurate).
        
        Three-step explicit approximation to Colebrook-White.
        More accurate than Swamee-Jain or Haaland, but more complex.
        
        Valid range: 4000 < Re < 10⁸, 10⁻⁶ < ε/D < 5×10⁻²
        Accuracy: ±0.15% vs Colebrook-White
        
        Args:
            Re: Reynolds number
            eps_D: Relative roughness (ε/D)
            
        Returns:
            Friction factor
        """
        # Three approximations
        A = -2.0 * math.log10(eps_D / 3.7 + 12.0 / Re)
        B = -2.0 * math.log10(eps_D / 3.7 + 2.51 * A / Re)
        C = -2.0 * math.log10(eps_D / 3.7 + 2.51 * B / Re)
        
        # Serghides formula
        inv_sqrt_f = A - ((B - A) ** 2) / (C - 2 * B + A)
        
        return (1.0 / inv_sqrt_f) ** 2


def get_correlation_info(correlation: FrictionCorrelation) -> dict:
    """Get information about a friction correlation.
    
    Provides details about applicability, accuracy, and characteristics
    of each correlation method.
    
    Args:
        correlation: Correlation to get info about
        
    Returns:
        Dictionary with keys: name, description, valid_range, accuracy, type
        
    Example:
        >>> info = get_correlation_info(FrictionCorrelation.HAALAND)
        >>> print(info['description'])
    """
    info_dict = {
        FrictionCorrelation.COLEBROOK_WHITE: {
            "name": "Colebrook-White",
            "description": "Implicit iterative method, most accurate (reference standard)",
            "valid_range": "Re > 4000, all ε/D",
            "accuracy": "Reference (±0%)",
            "type": "Implicit",
            "speed": "Slow (iterative)"
        },
        FrictionCorrelation.SWAMEE_JAIN: {
            "name": "Swamee-Jain",
            "description": "Explicit approximation, good for rough pipes",
            "valid_range": "5000 < Re < 10⁸, 10⁻⁶ < ε/D < 10⁻²",
            "accuracy": "±1%",
            "type": "Explicit",
            "speed": "Fast"
        },
        FrictionCorrelation.HAALAND: {
            "name": "Haaland",
            "description": "Explicit approximation, accurate for all conditions",
            "valid_range": "Re > 4000, all ε/D",
            "accuracy": "±1.5%",
            "type": "Explicit",
            "speed": "Fast"
        },
        FrictionCorrelation.CHURCHILL: {
            "name": "Churchill",
            "description": "Explicit, works for all Reynolds numbers (laminar + turbulent)",
            "valid_range": "All Re > 0, all ε/D",
            "accuracy": "±5%",
            "type": "Explicit",
            "speed": "Fast"
        },
        FrictionCorrelation.SERGHIDES: {
            "name": "Serghides",
            "description": "Explicit, very accurate three-step approximation",
            "valid_range": "4000 < Re < 10⁸, 10⁻⁶ < ε/D < 5×10⁻²",
            "accuracy": "±0.15%",
            "type": "Explicit",
            "speed": "Medium"
        }
    }
    
    return info_dict.get(correlation, {})
