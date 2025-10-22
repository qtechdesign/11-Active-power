"""Controller mappings between UI sliders and physical quantities."""

from __future__ import annotations

from dataclasses import dataclass

import math

from models import MachineLimits, OperatingPoint
from utils import clamp_percent


@dataclass(frozen=True)
class ControllerRange:
    min_value: float
    max_value: float

    def scale(self, percent: float) -> float:
        pct = clamp_percent(percent) / 100.0
        return self.min_value + pct * (self.max_value - self.min_value)


def governor_percent_to_p(percent: float, limits: MachineLimits) -> float:
    """Map governor percentage [0, 100] to active power (MW)."""

    return ControllerRange(0.0, limits.P_max_MW).scale(percent)


def excitation_percent_to_q(percent: float, limits: MachineLimits) -> float:
    """Map excitation percentage to reactive power (MVAr).

    Convention: 0% -> -Q_max, 50% -> 0, 100% -> +Q_max.
    """

    centered_percent = clamp_percent(percent)
    span = 2 * limits.Q_max_MVAr
    return (centered_percent / 100.0 - 0.5) * span


def p_to_governor_percent(p: float, limits: MachineLimits) -> float:
    if limits.P_max_MW <= 0:
        return 0.0
    raw = (p / limits.P_max_MW) * 100.0
    return clamp_percent(raw)


def q_to_excitation_percent(q: float, limits: MachineLimits) -> float:
    if limits.Q_max_MVAr <= 0:
        return 50.0
    raw = (q / limits.Q_max_MVAr) * 50.0 + 50.0
    return clamp_percent(raw)


def q_for_power_factor(p: float, pf: float, limits: MachineLimits) -> float:
    """Return the reactive power that yields ``pf`` for a given ``p``.

    The result is limited to the machine's Q capability and rating circle.
    """

    pf_clamped = max(-0.999, min(0.999, pf))
    if math.isclose(pf_clamped, 0.0, abs_tol=1e-6):
        return 0.0

    s_target = abs(p) / abs(pf_clamped)
    s_target = min(s_target, limits.S_rated_MVA)
    q_mag_sq = max(s_target**2 - p**2, 0.0)
    q_mag = math.sqrt(q_mag_sq)
    q = q_mag if pf_clamped >= 0 else -q_mag
    q, _ = limits.clamp_q(q)
    _, _, clamped = limits.clamp_s(p, q)
    if clamped:
        _, q, _ = limits.clamp_s(p, q)
    return q


def derive_operating_point(
    governor_percent: float,
    excitation_percent: float,
    limits: MachineLimits,
) -> tuple[OperatingPoint, list[str]]:
    """Return the clamped operating point and messages.

    The raw point is created from the slider mappings, then clamped according to
    the machine capabilities.
    """

    raw_p = governor_percent_to_p(governor_percent, limits)
    raw_q = excitation_percent_to_q(excitation_percent, limits)
    op = OperatingPoint(p_mw=raw_p, q_mvar=raw_q)
    return op.clamp_to_limits(limits)

