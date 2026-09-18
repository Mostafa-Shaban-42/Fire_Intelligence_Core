from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import requests
import streamlit as st

from dashboard.config import APP_ICON, APP_TITLE, LAYOUT
from dashboard.pages.command_center import render_command_center
from dashboard.pages.incidents import render_incidents
from dashboard.pages.live_monitoring import render_live_monitoring
from dashboard.pages.system_health import render_system_health

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none !important; }
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_session_state() -> None:
    """Safely initialize all required session states before rendering pages."""
    if "system_state" not in st.session_state:
        st.session_state.system_state = {
            "backend_online": False,
            "total_cameras": 4,
            "active_alerts": 0,
            "avg_latency_ms": 0.0,
            "engine_fps": 0.0,
        }
    if "incidents" not in st.session_state:
        st.session_state.incidents = []


def render_sidebar() -> str:
    with st.sidebar:
        st.title("🔥 Fire Intelligence")
        st.caption("fire intelligence core")
        st.divider()
        page = st.radio(
            "Navigation",
            ["Command Center", "Live Monitoring", "Incidents", "System Health"],
            key="main_navigation",
        )
        return page


def main() -> None:
    init_session_state()

    page = render_sidebar()
    if page == "Command Center":
        render_command_center()
    elif page == "Live Monitoring":
        render_live_monitoring()
    elif page == "Incidents":
        render_incidents()
    elif page == "System Health":
        render_system_health()


if __name__ == "__main__":
    main()