from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.components.incident_panel import (
    render_incident_panel,
)


def render_incidents() -> None:

    st.title(
        "🚨 Incident Management"
    )

    st.caption(
        "Historical and active fire incidents."
    )

    incidents = (
        st.session_state.incidents
    )

    if not incidents:

        st.info(
            "No incidents recorded."
        )

        return

    render_incident_panel(
        incidents
    )

    st.divider()

    dataframe = pd.DataFrame(
        incidents
    )

    csv_data = dataframe.to_csv(
        index=False
    )

    st.download_button(
        label="⬇ Export Incident Report",
        data=csv_data,
        file_name=(
            "fire_incidents.csv"
        ),
        mime="text/csv",
    )

    if st.button(
        "🗑 Clear Incident History"
    ):

        st.session_state.incidents.clear()

        st.session_state.system_state[
            "incidents"
        ] = 0

        st.rerun()