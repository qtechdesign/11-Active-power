"""Tests for controller mappings and limit clamping."""

from __future__ import annotations

import math

from controllers import (
    derive_operating_point,
    excitation_percent_to_q,
    governor_percent_to_p,
    q_for_power_factor,
)
from models import MachineLimits


LIMITS = MachineLimits(S_rated_MVA=50.0, P_max_MW=50.0, Q_max_MVAr=35.0)


def test_governor_maps_linearly() -> None:
    assert math.isclose(governor_percent_to_p(0.0, LIMITS), 0.0)
    assert math.isclose(governor_percent_to_p(50.0, LIMITS), 25.0)
    assert math.isclose(governor_percent_to_p(100.0, LIMITS), LIMITS.P_max_MW)


def test_excitation_maps_symmetrically() -> None:
    assert math.isclose(excitation_percent_to_q(0.0, LIMITS), -LIMITS.Q_max_MVAr)
    assert math.isclose(excitation_percent_to_q(50.0, LIMITS), 0.0)
    assert math.isclose(excitation_percent_to_q(100.0, LIMITS), LIMITS.Q_max_MVAr)


def test_operating_point_clamping() -> None:
    op, messages = derive_operating_point(120.0, 120.0, LIMITS)
    assert messages
    assert op.p_mw <= LIMITS.P_max_MW
    assert op.q_mvar <= LIMITS.Q_max_MVAr


def test_q_for_power_factor() -> None:
    q = q_for_power_factor(p=40.0, pf=0.8, limits=LIMITS)
    assert abs(q - 30.0) < 1e-6

