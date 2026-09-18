from __future__ import annotations

import streamlit as st


def render_normal_alert(
    message: str,
) -> None:

    st.success(
        f"🟢 {message}"
    )


def render_warning_alert(
    message: str,
) -> None:

    st.warning(
        f"🟡 {message}"
    )


def render_critical_alert(
    message: str,
) -> None:

    st.error(
        f"🚨 {message}"
    )


def render_offline_alert(
    message: str,
) -> None:

    st.error(
        f"⚫ {message}"
    )


def render_detection_alert(
    detection_type: str,
    confidence: float,
) -> None:

    detection_type_lower = (
        detection_type.lower()
    )

    if detection_type_lower == "fire":

        if confidence >= 0.80:

            render_critical_alert(
                f"FIRE DETECTED — "
                f"Confidence: "
                f"{confidence:.1%}"
            )

        else:

            render_warning_alert(
                f"Possible fire detected — "
                f"Confidence: "
                f"{confidence:.1%}"
            )