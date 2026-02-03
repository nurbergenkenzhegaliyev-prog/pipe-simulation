from __future__ import annotations

import math
from dataclasses import dataclass

from app.map.pipe import Pipe
from app.models.fluid import Fluid
from app.services.pressure_drop_service import PressureDropService


@dataclass
class PipePointData:
    """Data at a specific point along a pipe"""
    distance: float  # Distance from start in meters
    pressure: float  # Pressure in Pa
    velocity: float  # Velocity in m/s
    pressure_drop: float  # Pressure drop from start to this point in Pa


class PipePointAnalyzer:
    """Analyzes pressure, velocity, and pressure drop at multiple points along a pipe"""

    def __init__(self, service: PressureDropService):
        self.service = service

    def analyze_pipe(self, pipe: Pipe, start_pressure: float, num_points: int = 4) -> list[PipePointData]:
        """
        Analyze pipe at multiple points along its length.
        
        Args:
            pipe: The pipe to analyze
            start_pressure: Pressure at the start node in Pa
            num_points: Number of analysis points (minimum 2 for start and end)
        
        Returns:
            List of PipePointData for each analysis point
        """
        if pipe.flow_rate is None:
            return []

        num_points = max(num_points, 2)  # At least start and end
        
        # Calculate distances along pipe
        distances = [i * pipe.length / (num_points - 1) for i in range(num_points)]
        
        results = []
        for distance in distances:
            # Create a virtual pipe segment from start to this point
            fraction = distance / pipe.length if pipe.length > 0 else 0
            
            # Calculate pressure drop for the segment
            segment_dp = self._calculate_segment_dp(pipe, fraction, self.service.fluid)
            
            # Calculate velocity at this point (velocity is constant in incompressible flow)
            velocity = self._calculate_velocity(pipe, self.service.fluid)
            
            # Cumulative pressure drop from start
            pressure_at_point = start_pressure - segment_dp
            
            results.append(PipePointData(
                distance=distance,
                pressure=pressure_at_point,
                velocity=velocity,
                pressure_drop=segment_dp
            ))
        
        return results

    def _calculate_segment_dp(self, pipe: Pipe, fraction: float, fluid: Fluid) -> float:
        """Calculate pressure drop for a segment of the pipe"""
        if pipe.flow_rate is None or fraction == 0:
            return 0.0
        
        rho = fluid.density
        q = pipe.flow_rate
        area = pipe.area()
        v = q / area
        
        # Calculate friction factor
        f = self.service.flow.friction_factor(
            velocity=v,
            diameter=pipe.diameter,
            roughness=pipe.roughness,
            rho=rho,
            mu=fluid.viscosity,
        )
        
        # Calculate pressure drop for the segment (Darcy-Weisbach)
        segment_length = pipe.length * fraction
        dp = f * (segment_length / pipe.diameter) * (rho * v**2 / 2)
        
        # Add component losses only at the end
        if fraction == 1.0:
            if pipe.valve is not None:
                dp += pipe.valve.pressure_drop(rho, v)
            
            if pipe.pump_curve is not None:
                dp -= pipe.pump_curve.pressure_gain(q)
        
        return dp

    def _calculate_velocity(self, pipe: Pipe, fluid: Fluid) -> float:
        """Calculate velocity in the pipe"""
        if pipe.flow_rate is None:
            return 0.0
        
        area = pipe.area()
        return pipe.flow_rate / area
