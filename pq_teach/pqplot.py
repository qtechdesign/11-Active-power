"""Plotting utilities for the P-Q teaching app."""

from __future__ import annotations

import math
from typing import Iterable

import matplotlib.pyplot as plt
import mpld3


FIG_SIZE = (10.0, 6.5)
DARK_BG = "#0b1120"
PANEL_BG = "#111c33"
TEXT_COLOR = "#f8fafc"
TICK_COLOR = "#cbd5f5"
GRID_COLOR = "#243b64"
HALF_CIRCLE_COLOR = "#38bdf8"
PF_RAY_COLOR = "#f97316"
PF_TEXT_COLOR = "#bae6fd"
OPERATING_POINT_COLOR = "#fb7185"
ORIGIN_COLOR = "#94a3b8"
LAG_REGION_COLOR = "#166534"
LEAD_REGION_COLOR = "#1d4ed8"


def _configure_axes(ax: plt.Axes, s_rating: float, labels: tuple[str, str]) -> None:
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-s_rating, s_rating)
    ax.set_ylim(0, s_rating)
    ax.set_xlabel(labels[0], color=TEXT_COLOR, fontsize=14)
    ax.set_ylabel(labels[1], color=TEXT_COLOR, fontsize=14)
    ax.tick_params(colors=TICK_COLOR, labelsize=12)
    for spine in ax.spines.values():
        spine.set_color(TICK_COLOR)
        spine.set_linewidth(1.2)
    ax.grid(True, linestyle="--", linewidth=0.7, color=GRID_COLOR, alpha=0.85)
    ax.set_facecolor(PANEL_BG)
    ax.figure.set_facecolor(DARK_BG)


def draw_half_circle(ax: plt.Axes, s_rating: float) -> None:
    theta = [i * math.pi / 180 for i in range(0, 181)]
    q_values = [s_rating * math.cos(t) for t in theta]
    p_values = [s_rating * math.sin(t) for t in theta]
    ax.plot(q_values, p_values, label="Rating", linewidth=2.4, color=HALF_CIRCLE_COLOR)


def draw_pf_annotations(ax: plt.Axes, s_rating: float, pf_values: Iterable[float]) -> None:
    for pf in pf_values:
        pf_clamped = max(-0.999, min(0.999, pf))
        angle = math.acos(abs(pf_clamped))
        q = s_rating * math.sin(angle) * (1 if pf_clamped >= 0 else -1)
        p = s_rating * abs(pf_clamped)
        ax.plot([0, q], [0, p], linestyle=":", linewidth=0.9, alpha=0.55, color=PF_TEXT_COLOR)
        ax.text(
            q * 0.92,
            p * 0.92,
            f"PF {pf:+.2f}",
            ha="center",
            va="bottom",
            fontsize=11,
            color=PF_TEXT_COLOR,
            bbox=dict(boxstyle="round,pad=0.2", facecolor=PANEL_BG, edgecolor="none", alpha=0.75),
        )


def draw_operating_point(ax: plt.Axes, p: float, q: float):
    ax.plot(0, 0, marker="o", color=ORIGIN_COLOR, markersize=5)
    ax.plot([0, q], [0, p], color=PF_RAY_COLOR, linewidth=2.2, label="Power factor")
    point = ax.scatter([q], [p], color=OPERATING_POINT_COLOR, s=130, label="Operating point", zorder=6)
    return point


def render_plot(
    operating_point: tuple[float, float],
    s_rating: float,
    axis_labels: tuple[str, str],
    pf_annotations: Iterable[float] = (0.8, -0.8, 1.0),
) -> str:
    fig, ax = plt.subplots(figsize=FIG_SIZE)
    _configure_axes(ax, s_rating, axis_labels)
    draw_half_circle(ax, s_rating)
    draw_pf_annotations(ax, s_rating, pf_annotations)
    point_collection = draw_operating_point(ax, operating_point[0], operating_point[1])

    ax.axvspan(0, s_rating, alpha=0.1, color=LAG_REGION_COLOR, label="Lagging (+Q)")
    ax.axvspan(-s_rating, 0, alpha=0.1, color=LEAD_REGION_COLOR, label="Leading (-Q)")
    legend = ax.legend(
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        borderaxespad=0.0,
        frameon=True,
        facecolor=PANEL_BG,
        edgecolor="#3b4f74",
        fontsize=12,
    )
    for text in legend.get_texts():
        text.set_color(TEXT_COLOR)
    fig.subplots_adjust(left=0.08, right=0.82, bottom=0.12, top=0.92)

    p_val, q_val = operating_point
    s_val = math.hypot(p_val, q_val)
    pf_val = p_val / s_val if s_val else float("nan")
    phi_val = math.degrees(math.atan2(q_val, p_val)) if s_val else float("nan")

    label_lines = [
        f"P = {p_val:.2f} MW",
        f"Q = {q_val:.2f} MVAr",
        f"S = {s_val:.2f} MVA" if not math.isnan(s_val) else "S = —",
        f"PF = {pf_val:+.3f}" if not math.isnan(pf_val) else "PF = —",
        f"ϕ = {phi_val:+.1f}°" if not math.isnan(phi_val) else "ϕ = —",
    ]

    tooltip = mpld3.plugins.PointLabelTooltip(
        point_collection,
        labels=["\n".join(label_lines)],
    )
    mpld3.plugins.connect(fig, tooltip)

    html = mpld3.fig_to_html(fig, template_type="simple")
    css = (
        "<style>"
        ".pq-plot .mpld3-figure{width:100% !important;height:auto !important;}"
        ".pq-plot .mpld3-figure svg{width:100% !important;height:auto !important;}"
        ".pq-plot .mpld3-tooltip{font-size:14px;padding:6px 8px;background:#111c33;color:#f8fafc;"
        " border-radius:6px;box-shadow:0 4px 12px rgba(12,20,33,0.45);}"
        "</style>"
    )

    responsive_html = (
        "<div class='pq-plot' style='width:100%;max-width:760px;margin:0 auto;'>"
        f"{css}{html}"
        "</div>"
    )

    return responsive_html

