from __future__ import annotations

import streamlit as st

from dashboard.services.api_client import (
    get_api_client,
)


def render_system_health() -> None:

    st.title(
        "🩺 System Health"
    )

    st.caption(
        "Fire Intelligence Core infrastructure "
        "and runtime health."
    )

    api_client = (
        get_api_client()
    )

    health_result = (
        api_client.check_health()
    )

    col1, col2, col3 = (
        st.columns(3)
    )

    with col1:

        if health_result[
            "online"
        ]:

            st.metric(
                "Backend",
                "ONLINE",
            )

        else:

            st.metric(
                "Backend",
                "OFFLINE",
            )

    with col2:

        latency = (
            health_result.get(
                "latency_ms",
                0.0,
            )
        )

        st.metric(
            "Health Latency",
            f"{latency:.2f} ms",
        )

    with col3:

        status_code = (
            health_result.get(
                "status_code"
            )
        )

        st.metric(
            "HTTP Status",
            status_code
            if status_code
            else "-",
        )

    st.divider()

    st.subheader(
        "Backend Response"
    )

    if health_result[
        "online"
    ]:

        st.json(
            health_result.get(
                "data",
                {},
            )
        )

    else:

        st.error(
            health_result.get(
                "error",
                "Unknown backend error.",
            )
        )

    st.divider()

    st.subheader(
        "Tracking Runtime"
    )

    system_state = (
        st.session_state.system_state
    )

    st.json(
        {
            "camera_running": (
                system_state.get(
                    "camera_running"
                )
            ),
            "active_cameras": (
                system_state.get(
                    "active_cameras"
                )
            ),
            "total_frames": (
                system_state.get(
                    "total_frames"
                )
            ),
            "fire_detections": (
                system_state.get(
                    "fire_detections"
                )
            ),
            "incidents": (
                system_state.get(
                    "incidents"
                )
            ),
            "api_errors": (
                system_state.get(
                    "api_errors"
                )
            ),
        }
    )