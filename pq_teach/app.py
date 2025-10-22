"""Streamlit entrypoint for the P/Q teaching interface."""

from __future__ import annotations

import streamlit as st
import matplotlib.pyplot as plt
import io

from streamlit_plotly_events import plotly_events

from controllers import (
    derive_operating_point,
    p_to_governor_percent,
    q_to_excitation_percent,
)
from models import MachineLimits, OperatingPoint
from pqplot import render_plot
from scenarios import scenario_list
from utils import AppConfig, load_config


st.set_page_config(page_title="PQ Teach", layout="wide")


@st.cache_data
def get_config() -> tuple[AppConfig, list[str]]:
    return load_config()


def main() -> None:
    config, warnings = get_config()
    limits = MachineLimits(
        S_rated_MVA=config.S_rated_MVA,
        P_max_MW=config.P_max_MW,
        Q_max_MVAr=config.Q_max_MVAr,
    )

    if "governor_pct" not in st.session_state:
        st.session_state.governor_pct = 50.0
    if "excitation_pct" not in st.session_state:
        st.session_state.excitation_pct = 50.0
    if "last_preset" not in st.session_state:
        st.session_state.last_preset = "None"
    if "pending_governor_pct" in st.session_state:
        st.session_state.governor_pct = st.session_state.pop("pending_governor_pct")
    if "pending_excitation_pct" in st.session_state:
        st.session_state.excitation_pct = st.session_state.pop("pending_excitation_pct")
    pending_toasts: list[str] = st.session_state.pop("pending_toasts", []) if "pending_toasts" in st.session_state else []

    # Layout uses three columns: controls, plot, numerics stacked below plot on wide screens
    col_controls, col_plot = st.columns(
        [0.7, 1.3],
        gap="large",
    )

    with col_controls:
        st.header("Controls")
        s_rated = st.slider(
            "Machine rating S (MVA)",
            min_value=10.0,
            max_value=100.0,
            value=float(config.S_rated_MVA),
            step=1.0,
            help="⬆ Bigger S → larger circle, mimicking a bigger generator rating.",
        )
        limits = MachineLimits(
            S_rated_MVA=s_rated,
            P_max_MW=config.P_max_MW,
            Q_max_MVAr=config.Q_max_MVAr,
        )

        presets = scenario_list(limits)
        preset_by_name = {scenario.name: scenario for scenario in presets}
        preset_names = list(preset_by_name.keys())
        preset_options = ["None"] + preset_names
        previous_preset = st.session_state.last_preset
        default_index = 0
        if previous_preset in preset_names:
            default_index = preset_names.index(previous_preset) + 1
        preset_name = st.selectbox(
            "Presets",
            options=preset_options,
            index=default_index,
            help="🔖 Snap to a learning scenario with curated P & Q targets.",
        )

        scenario_description = ""
        if preset_name != "None":
            scenario = preset_by_name[preset_name]
            scenario_description = scenario.description

        if preset_name != previous_preset:
            st.session_state.last_preset = preset_name
            if preset_name != "None":
                selected_op = preset_by_name[preset_name].operating_point
                st.session_state.governor_pct = p_to_governor_percent(
                    selected_op.p_mw, limits
                )
                st.session_state.excitation_pct = q_to_excitation_percent(
                    selected_op.q_mvar, limits
                )
            else:
                st.session_state.last_preset = "None"

        governor_pct = st.slider(
            "Governor %",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.governor_pct),
            key="governor_pct",
            help="⚙️ Mechanical power input. Drag to move vertically (change P).",
        )
        excitation_pct = st.slider(
            "Excitation %",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.excitation_pct),
            key="excitation_pct",
            help="🌩 Field current. Drag to move horizontally (change Q).",
        )

        requested_messages: list[str] = []
        if scenario_description:
            st.toast(scenario_description, icon="🎯")

        op, messages = derive_operating_point(governor_pct, excitation_pct, limits)
        requested_messages.extend(messages)

    with col_plot:
        st.header("Operating Space")
        figure_plotly = render_plot(
            (op.p_mw, op.q_mvar),
            s_rating=limits.S_rated_MVA,
            axis_labels=(config.labels.x, config.labels.y),
        )
        clicked_points = plotly_events(
            figure_plotly,
            click_event=True,
            hover_event=False,
            select_event=False,
            key="plot_click",
            override_height=450,
        )
        if clicked_points:
            point = clicked_points[0]
            q_new = float(point.get("x", 0.0))
            p_new = float(point.get("y", 0.0))
            raw_op = OperatingPoint(p_mw=p_new, q_mvar=q_new)
            clamped_op, clamp_msgs = raw_op.clamp_to_limits(limits)
            st.session_state.pending_governor_pct = p_to_governor_percent(clamped_op.p_mw, limits)
            st.session_state.pending_excitation_pct = q_to_excitation_percent(clamped_op.q_mvar, limits)
            if clamp_msgs:
                st.session_state.pending_toasts = clamp_msgs
            st.session_state.last_preset = "None"
            st.rerun()

        st.caption(
            "Sign convention: +Q = lagging/inductive • −Q = leading/capacitive"
            " — click the plot to set the target operating point or drag legend entries to filter."
        )

    st.markdown("---")
    hints_col, metrics_col = st.columns([1.4, 1.0], gap="large")

    with hints_col:
        st.subheader("Education hints")
        st.markdown(
            """
            ### 🔍 Power Triangle Refresher
            - ⚡ **Active power (P)** — does real work (MW). Controlled by the **governor**.
            - 🌀 **Reactive power (Q)** — supports voltage & magnetizing energy (MVAr). Driven by **excitation**.
            - 🧲 **Apparent power (S)** — vector sum that reflects stator current. The blue arc is the thermal ceiling.
            - ⭐ **Power factor (PF)** — cosine of angle between ray & P-axis. Lagging (+Q) means supplying vars; leading (−Q) means absorbing.

            ### 🎓 Quick Exercises
            1. **Grid voltage dip?** Increase *Excitation %* ➜ push Q positive ➜ see the point slide right.
            2. **Light-load overvoltage?** Pull *Excitation %* down ➜ Q goes negative ➜ absorb vars.
            3. **Fuel-limited operation?** Reduce *Governor %* ➜ P falls ➜ stay inside the circle while maintaining PF > 0.9.

            ### 📈 Tips
            - Watch PF hover popups: keep within ±0.95 for efficiency.
            - If a warning pops up, you're exceeding thermal or rating limits—back off sliders until the toast clears.
            - Drag legend entries to isolate particular layers (ray, circle, operating point).
            """
        )
        if requested_messages:
            for msg in requested_messages:
                st.warning(msg)
        if warnings:
            for warning in warnings:
                st.error(warning)
        if pending_toasts:
            for toast_msg in pending_toasts:
                st.toast(toast_msg, icon="⚠️")

    with metrics_col:
        st.subheader("Numerics")
        s_value = op.apparent_power()
        pf = op.power_factor()
        angle = op.angle_deg()
        i_stator_pu = s_value / limits.S_rated_MVA if limits.S_rated_MVA else 0.0

        st.write(
            """
            | Quantity | Value |
            | --- | ---: |
            | P (MW) | {p:.2f} |
            | Q (MVAr) | {q:.2f} |
            | S (MVA) | {s:.2f} |
            | PF | {pf_val} |
            | ϕ (deg) | {phi} |
            | I_stator (pu) | {i_stat:.3f} |
            """.format(
                p=op.p_mw,
                q=op.q_mvar,
                s=s_value,
                pf_val="—" if pf is None else f"{pf:+.3f}",
                phi="—" if angle is None else f"{angle:+.1f}",
                i_stat=i_stator_pu,
            )
        )


if __name__ == "__main__":
    main()

