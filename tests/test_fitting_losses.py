"""Tests for fitting loss coefficient helpers."""

import pytest

from app.services.pressure.fitting_losses import (
    FittingK,
    sum_minor_losses,
    elbow_k,
    tee_k,
    valve_k,
)


def test_sum_minor_losses():
    assert sum_minor_losses(0.5, 1.0, 0.2) == pytest.approx(1.7)
    assert sum_minor_losses(0.5, None, 0.2) == pytest.approx(0.7)


def test_elbow_k():
    assert elbow_k(90.0, long_radius=False) == pytest.approx(FittingK.ELBOW_90_STD)
    assert elbow_k(90.0, long_radius=True) == pytest.approx(FittingK.ELBOW_90_LONG_RADIUS)
    assert elbow_k(45.0) == pytest.approx(FittingK.ELBOW_45_STD)


def test_tee_k():
    assert tee_k(branch=True) == pytest.approx(FittingK.TEE_BRANCH)
    assert tee_k(branch=False) == pytest.approx(FittingK.TEE_THROUGH)


def test_valve_k():
    assert valve_k("gate") == pytest.approx(FittingK.GATE_VALVE)
    assert valve_k("globe") == pytest.approx(FittingK.GLOBE_VALVE)
    assert valve_k("ball") == pytest.approx(FittingK.BALL_VALVE)
    assert valve_k("butterfly") == pytest.approx(FittingK.BUTTERFLY_VALVE)

    with pytest.raises(ValueError):
        valve_k("unknown")
