"""Fitting loss coefficient library (minor losses).

Provides standard K-values and helper functions to compute
minor loss coefficients for common fittings.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FittingK:
    """Common fitting loss coefficients (typical values)."""

    # Elbows
    ELBOW_90_STD: float = 0.9
    ELBOW_90_LONG_RADIUS: float = 0.6
    ELBOW_45_STD: float = 0.4

    # Tees
    TEE_THROUGH: float = 0.6
    TEE_BRANCH: float = 1.8

    # Valves (fully open)
    GATE_VALVE: float = 0.15
    GLOBE_VALVE: float = 10.0
    BALL_VALVE: float = 0.05
    BUTTERFLY_VALVE: float = 0.9

    # Sudden expansions/contractions (approx)
    EXPANSION_SUDDEN: float = 1.0
    CONTRACTION_SUDDEN: float = 0.5


def sum_minor_losses(*k_values: float) -> float:
    """Sum multiple minor loss coefficients."""
    return sum(k for k in k_values if k is not None)


def elbow_k(angle_deg: float = 90.0, long_radius: bool = False) -> float:
    """Return K for an elbow based on angle and radius type."""
    if angle_deg <= 50:
        return FittingK.ELBOW_45_STD
    if long_radius:
        return FittingK.ELBOW_90_LONG_RADIUS
    return FittingK.ELBOW_90_STD


def tee_k(branch: bool = True) -> float:
    """Return K for a tee fitting (branch or through)."""
    return FittingK.TEE_BRANCH if branch else FittingK.TEE_THROUGH


def valve_k(valve_type: str) -> float:
    """Return K for a valve type (fully open)."""
    v = valve_type.strip().lower()
    if v == "gate":
        return FittingK.GATE_VALVE
    if v == "globe":
        return FittingK.GLOBE_VALVE
    if v == "ball":
        return FittingK.BALL_VALVE
    if v == "butterfly":
        return FittingK.BUTTERFLY_VALVE
    raise ValueError(f"Unknown valve type: {valve_type}")