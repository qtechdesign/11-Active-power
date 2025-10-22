"""Streamlit entrypoint for the P/Q teaching interface."""

from __future__ import annotations

import streamlit as st

from controllers import (
    derive_operating_point,
    p_to_governor_percent,
    q_to_excitation_percent,
)
from models import MachineLimits
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

    # Layout uses three columns: controls, plot, numerics stacked below plot on wide screens
    col_controls, col_plot = st.columns(
        [0.8, 1.2],
        gap="medium",
    )

    with col_controls:
        st.header("Controls")
        s_rated = st.slider(
            "Machine rating S (MVA)",
            min_value=10.0,
            max_value=100.0,
            value=float(config.S_rated_MVA),
            step=1.0,
            help="Adjust machine apparent power rating to compare different generators.",
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
            help="Apply a guided scenario as a starting point.",
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
            help="Governor controls mechanical power input → vertical move (P).",
        )
        excitation_pct = st.slider(
            "Excitation %",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.excitation_pct),
            key="excitation_pct",
            help="Excitation controls field current → horizontal move (Q).",
        )

        requested_messages: list[str] = []
        if scenario_description:
            st.info(scenario_description)

        op, messages = derive_operating_point(governor_pct, excitation_pct, limits)
        requested_messages.extend(messages)

    with col_plot:
        st.header("Operating Space")
        figure_html = render_plot(
            (op.p_mw, op.q_mvar),
            s_rating=limits.S_rated_MVA,
            axis_labels=(config.labels.x, config.labels.y),
        )
        st.components.v1.html(
            f"<div class='pq-plot'>{figure_html}</div>",
            height=620,
            scrolling=False,
        )
        st.caption(
            "Sign convention: +Q = lagging/inductive • −Q = leading/capacitive"
            " — hover the red marker for (P, Q, S, PF, ϕ) details"
        )

    st.markdown("---")
    hints_col, metrics_col = st.columns([1, 2], gap="large")

    with hints_col:
        st.subheader("Education hints")
        st.markdown(
            "- Governor ↑ → P ↑ (vertical move)\n"
            "- Excitation ↑ → Q ↑ (horizontal move)\n"
            "- PF ray angle ϕ = atan2(Q, P) (non-standard axes)"
        )
        if requested_messages:
            for msg in requested_messages:
                st.warning(msg)
        if warnings:
            for warning in warnings:
                st.error(warning)

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

