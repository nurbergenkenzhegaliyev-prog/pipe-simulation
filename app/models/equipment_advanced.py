"""Advanced equipment models for hydraulic network simulation"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
import math


@dataclass
class PumpCurve:
    """Enhanced pump curve model with manufacturer data support
    
    Supports both simple quadratic curves and manufacturer tabular data.
    Pressure gain: dp = a + b*Q + c*Q^2 (Pa)
    """
    # Quadratic coefficients
    a: float
    b: float
    c: float
    
    # Optional manufacturer data points (flow_rate, head) in m³/s and m
    manufacturer_data: Optional[List[Tuple[float, float]]] = None
    
    # Pump specifications
    rated_flow: Optional[float] = None  # m³/s
    rated_head: Optional[float] = None  # m
    rated_power: Optional[float] = None  # W
    efficiency: float = 0.75  # Default efficiency
    speed: float = 1500.0  # RPM
    impeller_diameter: Optional[float] = None  # m
    
    def pressure_gain(self, flow_rate: float) -> float:
        """Calculate pressure gain for given flow rate
        
        Args:
            flow_rate: Volumetric flow rate in m³/s
            
        Returns:
            Pressure gain in Pa
        """
        if self.manufacturer_data and len(self.manufacturer_data) > 0:
            # Use interpolation from manufacturer data
            head = self._interpolate_head(flow_rate)
            return head * 9810.0  # Convert m to Pa (assuming water)
        else:
            # Use quadratic curve
            return self.a + self.b * flow_rate + self.c * (flow_rate ** 2)
    
    def _interpolate_head(self, flow_rate: float) -> float:
        """Interpolate head from manufacturer data points"""
        if not self.manufacturer_data or len(self.manufacturer_data) == 0:
            return 0.0
        
        # Sort data by flow rate
        data = sorted(self.manufacturer_data, key=lambda x: x[0])
        
        # Check bounds
        if flow_rate <= data[0][0]:
            return data[0][1]
        if flow_rate >= data[-1][0]:
            return data[-1][1]
        
        # Linear interpolation
        for i in range(len(data) - 1):
            q1, h1 = data[i]
            q2, h2 = data[i + 1]
            
            if q1 <= flow_rate <= q2:
                # Linear interpolation
                t = (flow_rate - q1) / (q2 - q1)
                return h1 + t * (h2 - h1)
        
        return data[-1][1]
    
    def power_consumption(self, flow_rate: float, fluid_density: float = 998.0) -> float:
        """Calculate pump power consumption
        
        Args:
            flow_rate: Volumetric flow rate in m³/s
            fluid_density: Fluid density in kg/m³
            
        Returns:
            Power consumption in W
        """
        head = self.pressure_gain(flow_rate) / (fluid_density * 9.81)
        hydraulic_power = fluid_density * 9.81 * flow_rate * head
        return hydraulic_power / self.efficiency if self.efficiency > 0 else 0.0
    
    @classmethod
    def from_manufacturer_data(cls, data_points: List[Tuple[float, float]], 
                              efficiency: float = 0.75,
                              rated_power: Optional[float] = None):
        """Create pump curve from manufacturer performance data
        
        Args:
            data_points: List of (flow_rate, head) tuples in m³/s and m
            efficiency: Pump efficiency (0-1)
            rated_power: Rated power in W
            
        Returns:
            PumpCurve instance
        """
        # Fit quadratic curve to data (for fallback)
        if len(data_points) >= 3:
            # Simple quadratic fit
            # For now, use first, middle, and last points
            q1, h1 = data_points[0]
            q2, h2 = data_points[len(data_points)//2]
            q3, h3 = data_points[-1]
            
            # Convert heads to pressure
            p1 = h1 * 9810
            p2 = h2 * 9810
            p3 = h3 * 9810
            
            # Solve for a, b, c
            # This is a simplified fit - for production use scipy.optimize.curve_fit
            a = p1
            c = (p3 - p1 - (q3/q2)*(p2 - p1)) / (q3**2 - (q3/q2)*q2**2)
            b = (p2 - p1 - c*q2**2) / q2
        else:
            a, b, c = 0.0, 0.0, 0.0
        
        rated_flow = data_points[-1][0] if data_points else None
        rated_head = data_points[0][1] if data_points else None
        
        return cls(
            a=a,
            b=b,
            c=c,
            manufacturer_data=data_points,
            rated_flow=rated_flow,
            rated_head=rated_head,
            rated_power=rated_power,
            efficiency=efficiency
        )


@dataclass
class Valve:
    """Enhanced valve model with multiple valve types
    
    Supports loss coefficient K and flow coefficient Cv models.
    """
    # Loss coefficient (dimensionless)
    k: float = 0.0
    
    # Flow coefficient Cv (US gallons/min at 1 psi drop)
    cv: Optional[float] = None
    
    # Valve type
    valve_type: str = "gate"  # gate, globe, ball, butterfly, check, control
    
    # Opening percentage (0-100)
    opening: float = 100.0
    
    # Valve characteristics for control valves
    characteristic: str = "linear"  # linear, equal_percentage, quick_opening
    
    def pressure_drop(self, rho: float, velocity: float) -> float:
        """Calculate pressure drop using loss coefficient
        
        Args:
            rho: Fluid density in kg/m³
            velocity: Flow velocity in m/s
            
        Returns:
            Pressure drop in Pa
        """
        k_effective = self._get_effective_k()
        return k_effective * (rho * velocity ** 2 / 2)
    
    def pressure_drop_from_cv(self, flow_rate: float, specific_gravity: float = 1.0) -> float:
        """Calculate pressure drop using Cv coefficient
        
        Args:
            flow_rate: Flow rate in m³/s
            specific_gravity: Specific gravity relative to water
            
        Returns:
            Pressure drop in Pa
        """
        if self.cv is None or self.cv == 0:
            return 0.0
        
        # Convert m³/s to GPM (gallons per minute)
        flow_gpm = flow_rate * 15850.3
        
        # Cv equation: Q = Cv * sqrt(ΔP / SG)
        # Rearranging: ΔP = (Q / Cv)² * SG
        delta_p_psi = (flow_gpm / self.cv) ** 2 * specific_gravity
        
        # Convert psi to Pa
        return delta_p_psi * 6894.76
    
    def _get_effective_k(self) -> float:
        """Calculate effective K based on valve opening and type"""
        if self.opening >= 100:
            return self.k
        
        # Adjust K based on opening percentage and valve type
        opening_fraction = self.opening / 100.0
        
        if self.valve_type == "gate":
            # Gate valve: K increases dramatically when partially closed
            if opening_fraction > 0.9:
                k_factor = 1.0
            elif opening_fraction > 0.75:
                k_factor = 2.0
            elif opening_fraction > 0.5:
                k_factor = 8.0
            elif opening_fraction > 0.25:
                k_factor = 35.0
            else:
                k_factor = 150.0
        elif self.valve_type == "globe":
            # Globe valve: more linear response
            k_factor = 1.0 / (opening_fraction ** 2) if opening_fraction > 0 else 1000.0
        elif self.valve_type == "ball":
            # Ball valve: similar to gate
            k_factor = 1.0 / (opening_fraction ** 3) if opening_fraction > 0 else 1000.0
        elif self.valve_type == "butterfly":
            # Butterfly valve
            k_factor = 1.0 / (opening_fraction ** 1.5) if opening_fraction > 0 else 1000.0
        else:
            k_factor = 1.0 / opening_fraction if opening_fraction > 0 else 1000.0
        
        return self.k * k_factor
    
    @classmethod
    def from_cv(cls, cv: float, valve_type: str = "control", opening: float = 100.0):
        """Create valve from Cv coefficient
        
        Args:
            cv: Flow coefficient in US gallons/min at 1 psi
            valve_type: Type of valve
            opening: Opening percentage (0-100)
            
        Returns:
            Valve instance
        """
        # Estimate K from Cv (rough approximation)
        # K ≈ 890 / Cv² for a typical valve
        k = 890.0 / (cv ** 2) if cv > 0 else 10.0
        
        return cls(
            k=k,
            cv=cv,
            valve_type=valve_type,
            opening=opening
        )


@dataclass
class Tank:
    """Storage tank model with dynamic behavior
    
    Models tanks with varying water level and pressure.
    """
    # Geometry
    diameter: float  # m
    height: float  # m
    elevation: float = 0.0  # m above reference
    
    # Water level
    initial_level: float = 0.0  # m above tank bottom
    min_level: float = 0.0  # m
    max_level: Optional[float] = None  # m (defaults to height)
    
    # Current state
    current_level: Optional[float] = None  # m
    
    def __post_init__(self):
        if self.max_level is None:
            self.max_level = self.height
        if self.current_level is None:
            self.current_level = self.initial_level
    
    def volume(self, level: Optional[float] = None) -> float:
        """Calculate volume at given level
        
        Args:
            level: Water level in m (uses current_level if None)
            
        Returns:
            Volume in m³
        """
        if level is None:
            level = self.current_level
        
        radius = self.diameter / 2
        area = math.pi * radius ** 2
        return area * level
    
    def pressure_at_base(self, level: Optional[float] = None, 
                        fluid_density: float = 998.0) -> float:
        """Calculate pressure at tank base
        
        Args:
            level: Water level in m (uses current_level if None)
            fluid_density: Fluid density in kg/m³
            
        Returns:
            Pressure in Pa
        """
        if level is None:
            level = self.current_level
        
        # Hydrostatic pressure
        return fluid_density * 9.81 * level
    
    def update_level(self, flow_in: float, flow_out: float, timestep: float) -> float:
        """Update tank level based on inflow and outflow
        
        Args:
            flow_in: Inflow rate in m³/s
            flow_out: Outflow rate in m³/s
            timestep: Time step in seconds
            
        Returns:
            New water level in m
        """
        radius = self.diameter / 2
        area = math.pi * radius ** 2
        
        # Volume change
        delta_volume = (flow_in - flow_out) * timestep
        delta_level = delta_volume / area
        
        # Update level with bounds
        new_level = self.current_level + delta_level
        new_level = max(self.min_level, min(self.max_level, new_level))
        
        self.current_level = new_level
        return new_level


@dataclass
class Reservoir:
    """Fixed-head reservoir model
    
    Represents an infinite source/sink with constant pressure.
    """
    # Fixed head
    head: float  # m above reference
    elevation: float = 0.0  # m above reference
    
    def pressure(self, fluid_density: float = 998.0) -> float:
        """Calculate pressure at reservoir connection point
        
        Args:
            fluid_density: Fluid density in kg/m³
            
        Returns:
            Pressure in Pa
        """
        total_head = self.head + self.elevation
        return fluid_density * 9.81 * total_head
