"""Preset scenarios for common operating conditions."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List

from models import MachineLimits, OperatingPoint


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    operating_point: OperatingPoint


def _pf_point(limits: MachineLimits, pf: float) -> OperatingPoint:
    pf_abs = max(1e-6, min(0.999, abs(pf)))
    target_p = min(limits.P_max_MW, limits.S_rated_MVA * pf_abs)
    s = target_p / pf_abs
    q_abs = math.sqrt(max(s * s - target_p * target_p, 0.0))
    q = q_abs if pf >= 0 else -q_abs
    return OperatingPoint(p_mw=target_p, q_mvar=q)


def nominal_pf_085_lag(limits: MachineLimits) -> Scenario:
    op = _pf_point(limits, pf=0.85)
    op, _ = op.clamp_to_limits(limits)
    return Scenario(
        name="Nominal PF 0.85 lag",
        description="Operate at power factor ~0.85 lagging for rated loading.",
        operating_point=op,
    )


def voltage_support(limits: MachineLimits) -> Scenario:
    base = _pf_point(limits, pf=0.95)
    target_q = min(limits.Q_max_MVAr, base.q_mvar + 0.4 * limits.Q_max_MVAr)
    op = OperatingPoint(p_mw=base.p_mw, q_mvar=target_q)
    op, _ = op.clamp_to_limits(limits)
    return Scenario(
        name="Voltage support (+Q)",
        description="Increase excitation to supply reactive power while keeping P constant.",
        operating_point=op,
    )


def capacitive_support(limits: MachineLimits) -> Scenario:
    base = _pf_point(limits, pf=0.95)
    target_q = max(-limits.Q_max_MVAr, base.q_mvar - 0.6 * limits.Q_max_MVAr)
    op = OperatingPoint(p_mw=base.p_mw, q_mvar=target_q)
    op, _ = op.clamp_to_limits(limits)
    return Scenario(
        name="Capacitive compensation (-Q)",
        description="Reduce excitation to absorb reactive power with constant P.",
        operating_point=op,
    )


def scenario_list(limits: MachineLimits) -> List[Scenario]:
    return [
        nominal_pf_085_lag(limits),
        voltage_support(limits),
        capacitive_support(limits),
    ]

