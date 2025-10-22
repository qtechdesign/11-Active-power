"""Geometry-related tests for operating point projections."""

from __future__ import annotations

import math

from models import MachineLimits, OperatingPoint


LIMITS = MachineLimits(S_rated_MVA=50.0, P_max_MW=50.0, Q_max_MVAr=35.0)


def test_point_on_circle_is_not_clamped() -> None:
    op = OperatingPoint(p_mw=40.0, q_mvar=30.0)
    clamped, messages = op.clamp_to_limits(LIMITS)
    assert not messages
    assert math.isclose(clamped.apparent_power(), LIMITS.S_rated_MVA, rel_tol=1e-6)


def test_point_outside_circle_is_projected() -> None:
    op = OperatingPoint(p_mw=60.0, q_mvar=10.0)
    clamped, messages = op.clamp_to_limits(LIMITS)
    assert "MVA rating" in messages[-1]
    assert clamped.apparent_power() <= LIMITS.S_rated_MVA + 1e-6

