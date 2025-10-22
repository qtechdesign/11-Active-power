"""Data models describing the machine and its operating point."""

from __future__ import annotations

import math
from dataclasses import dataclass


EPS = 1e-9


@dataclass(frozen=True)
class MachineLimits:
    S_rated_MVA: float
    P_max_MW: float
    Q_max_MVAr: float

    def clamp_s(self, p: float, q: float) -> tuple[float, float, bool]:
        """Project (Q, P) onto the rating circle if necessary."""

        s_squared = p * p + q * q
        if s_squared <= self.S_rated_MVA * self.S_rated_MVA + EPS:
            return p, q, False

        if s_squared <= EPS:
            return 0.0, 0.0, True

        scale = self.S_rated_MVA / math.sqrt(s_squared)
        return p * scale, q * scale, True

    def clamp_q(self, q: float) -> tuple[float, bool]:
        limited = max(-self.Q_max_MVAr, min(self.Q_max_MVAr, q))
        return limited, not math.isclose(limited, q, rel_tol=1e-6, abs_tol=1e-6)

    def clamp_p(self, p: float) -> tuple[float, bool]:
        limited = max(0.0, min(self.P_max_MW, p))
        return limited, not math.isclose(limited, p, rel_tol=1e-6, abs_tol=1e-6)


@dataclass
class OperatingPoint:
    p_mw: float
    q_mvar: float
    frequency_hz: float | None = None

    def apparent_power(self) -> float:
        return math.hypot(self.p_mw, self.q_mvar)

    def power_factor(self) -> float | None:
        s = self.apparent_power()
        if s <= EPS:
            return None
        return self.p_mw / s

    def angle_rad(self) -> float | None:
        if math.isclose(self.p_mw, 0.0, abs_tol=EPS) and math.isclose(
            self.q_mvar, 0.0, abs_tol=EPS
        ):
            return None
        return math.atan2(self.q_mvar, self.p_mw)

    def angle_deg(self) -> float | None:
        angle = self.angle_rad()
        if angle is None:
            return None
        return math.degrees(angle)

    def as_tuple(self) -> tuple[float, float]:
        return self.p_mw, self.q_mvar

    def clamp_to_limits(self, limits: MachineLimits) -> tuple["OperatingPoint", list[str]]:
        p, q = self.p_mw, self.q_mvar
        messages: list[str] = []

        p, clamped_p = limits.clamp_p(p)
        if clamped_p:
            messages.append("Requested P exceeds machine rating; clamped to limit.")

        q, clamped_q = limits.clamp_q(q)
        if clamped_q:
            messages.append("Requested Q exceeds excitation limits; clamped.")

        p, q, clamped_s = limits.clamp_s(p, q)
        if clamped_s:
            messages.append("Requested point exceeds MVA rating; clamped to boundary.")

        return OperatingPoint(p, q), messages

