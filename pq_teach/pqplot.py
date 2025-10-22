"""Plotting utilities for the P-Q teaching app."""

from __future__ import annotations

import math
from typing import Iterable, Tuple

import numpy as np
import plotly.graph_objects as go

DARK_BG = "#0b1120"
PANEL_BG = "#12203a"
TEXT_COLOR = "#e2e8f0"
GRID_COLOR = "#1f3256"
HALF_CIRCLE_COLOR = "#38bdf8"
PF_RAY_COLOR = "#f97316"
PF_TEXT_COLOR = "#bae6fd"
OPERATING_POINT_COLOR = "#fb7185"
LAG_REGION_COLOR = "rgba(22, 101, 52, 0.12)"
LEAD_REGION_COLOR = "rgba(29, 78, 216, 0.12)"


def _pf_point(s_rating: float, pf: float) -> Tuple[float, float]:
    pf_clamped = max(-0.999, min(0.999, pf))
    angle = math.acos(abs(pf_clamped))
    q = s_rating * math.sin(angle) * (1 if pf_clamped >= 0 else -1)
    p = s_rating * abs(pf_clamped)
    return q, p


def render_plot(
    operating_point: tuple[float, float],
    s_rating: float,
    axis_labels: tuple[str, str],
    pf_annotations: Iterable[float] = (0.8, -0.8, 1.0),
) -> go.Figure:
    q_values = np.linspace(-s_rating, s_rating, 361)
    p_values = np.sqrt(np.clip(s_rating**2 - q_values**2, 0.0, None))

    fig = go.Figure()

    # Rating boundary
    fig.add_trace(
        go.Scatter(
            x=q_values,
            y=p_values,
            mode="lines",
            line=dict(color=HALF_CIRCLE_COLOR, width=3),
            name="Rating",
            hoverinfo="skip",
        )
    )

    # Lagging / leading regions
    fig.add_shape(
        type="rect",
        x0=0,
        x1=s_rating,
        y0=0,
        y1=s_rating,
        fillcolor=LAG_REGION_COLOR,
        line_width=0,
        layer="below",
    )
    fig.add_shape(
        type="rect",
        x0=-s_rating,
        x1=0,
        y0=0,
        y1=s_rating,
        fillcolor=LEAD_REGION_COLOR,
        line_width=0,
        layer="below",
    )

    # PF annotations
    for pf in pf_annotations:
        q_pf, p_pf = _pf_point(s_rating, pf)
        fig.add_trace(
            go.Scatter(
                x=[0, q_pf],
                y=[0, p_pf],
                mode="lines",
                line=dict(color=PF_TEXT_COLOR, width=1.5, dash="dot"),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig.add_annotation(
            x=q_pf * 0.9,
            y=p_pf * 0.9,
            text=f"PF {pf:+.2f}",
            showarrow=False,
            font=dict(color=PF_TEXT_COLOR, size=12),
            bgcolor="rgba(18, 32, 58, 0.6)",
            bordercolor="rgba(18, 32, 58, 0.2)",
            borderpad=4,
        )

    # Power factor ray
    p_op, q_op = operating_point
    fig.add_trace(
        go.Scatter(
            x=[0, q_op],
            y=[0, p_op],
            mode="lines",
            line=dict(color=PF_RAY_COLOR, width=3),
            name="Power factor",
            hoverinfo="skip",
        )
    )

    # Operating point marker
    s_val = math.hypot(p_op, q_op)
    pf_val = p_op / s_val if s_val else 0.0
    phi = math.degrees(math.atan2(q_op, p_op)) if s_val else 0.0
    fig.add_trace(
        go.Scatter(
            x=[q_op],
            y=[p_op],
            mode="markers",
            marker=dict(size=16, color=OPERATING_POINT_COLOR, line=dict(color="#ffffff", width=1.5)),
            name="Operating point",
            customdata=[[s_val, pf_val, phi]],
            hovertemplate=(
                "<b>Operating point</b><br>"
                + f"{axis_labels[1]}: %{{y:.2f}}<br>"
                + f"{axis_labels[0]}: %{{x:.2f}}<br>"
                + "S: %{{customdata[0]:.2f}} MVA<br>"
                + "PF: %{{customdata[1]:+.3f}}<br>"
                + "ϕ: %{{customdata[2]:+.1f}}°<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        paper_bgcolor=DARK_BG,
        plot_bgcolor=PANEL_BG,
        margin=dict(l=50, r=160, t=50, b=60),
        hovermode="closest",
        dragmode=False,
        legend=dict(
            title="",
            orientation="v",
            x=1.02,
            xanchor="left",
            y=0.5,
            yanchor="middle",
            bgcolor="rgba(18, 32, 58, 0.85)",
            bordercolor="#355070",
            borderwidth=1,
            font=dict(color=TEXT_COLOR, size=12),
        ),
    )

    fig.update_xaxes(
        title=axis_labels[0],
        range=[-s_rating * 1.05, s_rating * 1.05],
        gridcolor=GRID_COLOR,
        zeroline=False,
        linecolor=TEXT_COLOR,
        color=TEXT_COLOR,
        tickfont=dict(size=12),
        fixedrange=True,
    )
    fig.update_yaxes(
        title=axis_labels[1],
        range=[0, s_rating * 1.05],
        gridcolor=GRID_COLOR,
        zeroline=False,
        linecolor=TEXT_COLOR,
        color=TEXT_COLOR,
        tickfont=dict(size=12),
        fixedrange=True,
    )

    return fig

