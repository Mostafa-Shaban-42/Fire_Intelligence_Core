from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
import streamlit as st


def render_incident_panel(
    incidents: List[Dict[str, Any]],
) -> None:
    """
    Renders recent incidents.
    """

    st.subheader(
        "🚨 Recent Incidents"
    )

    if not incidents:

        st.info(
            "No incidents detected."
        )

        return

    display_rows = []

    for incident in reversed(
        incidents[-20:]
    ):

        display_rows.append(
            {
                "Time": incident.get(
                    "timestamp",
                    "-",
                ),
                "Camera": incident.get(
                    "camera_id",
                    "-",
                ),
                "Type": incident.get(
                    "type",
                    "fire",
                ),
                "Confidence": (
                    f"{incident.get('confidence', 0.0):.1%}"
                ),
                "Status": incident.get(
                    "status",
                    "ACTIVE",
                ),
            }
        )

    dataframe = pd.DataFrame(
        display_rows
    )

    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
    )


def render_incident_card(
    incident: Dict[str, Any],
) -> None:

    confidence = incident.get(
        "confidence",
        0.0,
    )

    st.error(
        f"""
        🔥 **FIRE INCIDENT**

        Camera: {incident.get("camera_id", "-")}

        Confidence: {confidence:.1%}

        Status: {incident.get("status", "ACTIVE")}
        """
    )