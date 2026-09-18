from __future__ import annotations

import streamlit as st


def render_metric(
    title: str,
    value: str | int | float,
    delta: str | None = None,
) -> None:
    """
    Renders one standard dashboard metric.
    """

    st.metric(
        label=title,
        value=value,
        delta=delta,
    )


def render_system_metrics(
    system_state: dict,
) -> None:
    """
    Renders the main system metrics row.
    """

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        render_metric(
            "Active Cameras",
            system_state.get(
                "active_cameras",
                0,
            ),
        )

    with col2:

        render_metric(
            "Total Frames",
            system_state.get(
                "total_frames",
                0,
            ),
        )

    with col3:

        render_metric(
            "Fire Detections",
            system_state.get(
                "fire_detections",
                0,
            ),
        )

    with col4:

        render_metric(
            "Incidents",
            system_state.get(
                "incidents",
                0,
            ),
        )


def render_performance_metrics(
    latency_ms: float,
    fps: float,
    success_rate: float,
) -> None:

    col1, col2, col3 = st.columns(3)

    with col1:

        render_metric(
            "API Latency",
            f"{latency_ms:.1f} ms",
        )

    with col2:

        render_metric(
            "Processing Rate",
            f"{fps:.1f} FPS",
        )

    with col3:

        render_metric(
            "Success Rate",
            f"{success_rate:.1f}%",
        )