"""Utility helpers for configuration and numeric safety."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


CONFIG_PATH = Path("config.json")


@dataclass(frozen=True)
class AxisLabels:
    x: str = "Reactive Power Q [MVAr]"
    y: str = "Active Power P [MW]"


@dataclass(frozen=True)
class AppConfig:
    S_rated_MVA: float = 50.0
    P_max_MW: float = 50.0
    Q_max_MVAr: float = 35.0
    labels: AxisLabels = AxisLabels()
    pf_target: float = 0.95
    base_frequency_hz: float = 50.0
    droop_percent: float = 4.0


def _env_override(key: str, fallback: float) -> float:
    raw = os.getenv(key)
    if raw is None:
        return fallback
    try:
        return float(raw)
    except ValueError:
        return fallback


def load_config(config_path: Path | None = None) -> Tuple[AppConfig, list[str]]:
    """Load configuration with environment overrides.

    Returns a tuple of the parsed configuration and any warnings raised during loading.
    """

    path = config_path or CONFIG_PATH
    warnings: list[str] = []

    data: dict[str, object] | None = None
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError) as err:
            warnings.append(
                f"Failed to read {path.name} ({err}); falling back to defaults."
            )

    labels_dict = {}
    pf_target = AppConfig().pf_target
    droop_percent = AppConfig().droop_percent
    base_frequency_hz = AppConfig().base_frequency_hz
    if data and isinstance(data, dict):
        labels_dict = {
            "x": str(data.get("labels", {}).get("x", AxisLabels().x)),
            "y": str(data.get("labels", {}).get("y", AxisLabels().y)),
        }
        pf_target = float(data.get("pf_target", pf_target))
        droop_percent = float(data.get("droop_percent", droop_percent))
        base_frequency_hz = float(data.get("base_frequency_hz", base_frequency_hz))
    labels = AxisLabels(**labels_dict)

    defaults = AppConfig(labels=labels)

    if data and isinstance(data, dict):
        defaults = AppConfig(
            S_rated_MVA=float(data.get("S_rated_MVA", defaults.S_rated_MVA)),
            P_max_MW=float(data.get("P_max_MW", defaults.P_max_MW)),
            Q_max_MVAr=float(data.get("Q_max_MVAr", defaults.Q_max_MVAr)),
            labels=labels,
            pf_target=pf_target,
            droop_percent=droop_percent,
            base_frequency_hz=base_frequency_hz,
        )

    s_rated = _env_override("PQT_S_RATED", defaults.S_rated_MVA)
    if s_rated <= 0:
        warnings.append("S_rated_MVA must be positive; using default value.")
        s_rated = defaults.S_rated_MVA

    p_max = _env_override("PQT_P_MAX", defaults.P_max_MW)
    if p_max <= 0:
        warnings.append("P_max_MW must be positive; using default value.")
        p_max = defaults.P_max_MW

    q_max = _env_override("PQT_Q_MAX", defaults.Q_max_MVAr)
    if q_max <= 0:
        warnings.append("Q_max_MVAr must be positive; using default value.")
        q_max = defaults.Q_max_MVAr

    pf_target = _env_override("PQT_PF_TARGET", defaults.pf_target)
    droop_percent = _env_override("PQT_DROOP_PERCENT", defaults.droop_percent)
    base_frequency = _env_override("PQT_F_BASE", defaults.base_frequency_hz)

    config = AppConfig(
        S_rated_MVA=s_rated,
        P_max_MW=p_max,
        Q_max_MVAr=q_max,
        labels=defaults.labels,
        pf_target=pf_target,
        droop_percent=droop_percent,
        base_frequency_hz=base_frequency,
    )

    return config, warnings


def clamp_percent(value: float) -> float:
    """Clamp a percentage value to [0, 100]."""

    return max(0.0, min(100.0, value))

