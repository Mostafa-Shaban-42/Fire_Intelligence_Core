from __future__ import annotations

import os
import tempfile
import time
import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000/cameras"


@st.cache_data(ttl=1.0, show_spinner=False)
def fetch_registered_cameras() -> list[dict]:
    try:
        response = requests.get(API_BASE_URL, timeout=1.0)
        if response.status_code == 200:
            cameras = response.json()
            if cameras:
                return cameras
    except Exception:
        pass

    return [
        {
            "camera_id": "webcam_0",
            "location": "Laptop Webcam (Default)",
            "rtsp_url": "0",
            "latitude": 30.0444,
            "longitude": 31.2357,
            "is_active": True,
        }
    ]


def render_live_monitoring() -> None:
    st.title("📹 Live Fire Analytics")
    st.caption("Real-Time Ultra Smooth Engine with Sub-Millisecond AI Overlay")

    if "is_monitoring" not in st.session_state:
        st.session_state["is_monitoring"] = False

    status_col1, status_col2 = st.columns([3, 1])
    with status_col2:
        if st.session_state.get("is_monitoring", False):
            st.success("🟢 AI Stream: ACTIVE")
        else:
            st.error("🔴 AI Stream: STOPPED")

    cameras = fetch_registered_cameras()

    st.subheader("⚙️ Stream Source Selection")
    source_type = st.radio(
        "Select Source Method:",
        ["Registered Stream Node", "Direct File Upload"],
        horizontal=True,
    )

    selected_stream_id = None

    if source_type == "Registered Stream Node":
        if cameras:
            camera_ids = [c["camera_id"] for c in cameras]
            selected_stream_id = st.selectbox(
                "Select Active Camera Node:",
                options=camera_ids,
                format_func=lambda cid: next(
                    (f"{c['location']} ({cid})" for c in cameras if c["camera_id"] == cid),
                    cid,
                ),
            )
            st.session_state["active_stream_id"] = selected_stream_id

    elif source_type == "Direct File Upload":
        uploaded_file = st.file_uploader(
            "Upload Fire Test Video:", type=["mp4", "avi", "mov"]
        )
        if uploaded_file is not None:
            if st.button(
                "Register & Prepare Direct Stream",
                type="primary",
                use_container_width=True,
            ):
                temp_dir = tempfile.gettempdir()
                file_path = os.path.join(
                    temp_dir, f"direct_stream_{int(time.time())}.mp4"
                )
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                new_cam_id = f"upload_{int(time.time())}"
                payload = {
                    "camera_id": new_cam_id,
                    "location": "Direct Local Stream",
                    "rtsp_url": file_path,
                    "latitude": 30.0444,
                    "longitude": 31.2357,
                    "is_active": True,
                }
                
                try:
                    res = requests.post(API_BASE_URL, json=payload, timeout=2.0)
                    st.session_state["active_stream_id"] = new_cam_id
                    st.session_state["is_monitoring"] = True
                    st.success(f"Registered Direct Stream Node: `{new_cam_id}`")
                    st.rerun()
                except Exception as e:
                    st.error(f"Cannot connect to FastAPI Backend: {e}")

    st.divider()

    left_col, right_col = st.columns([3, 1])
    with left_col:
        if st.button("▶ Start Live Monitoring", type="primary", use_container_width=True):
            if source_type == "Registered Stream Node" and not selected_stream_id:
                if cameras:
                    selected_stream_id = cameras[0]["camera_id"]
                    st.session_state["active_stream_id"] = selected_stream_id

            if selected_stream_id or st.session_state.get("active_stream_id"):
                st.session_state["is_monitoring"] = True
                st.rerun()

    with right_col:
        if st.button("⏹ Stop Stream", use_container_width=True):
            st.session_state["is_monitoring"] = False
            st.rerun()

    st.divider()

    # Active Viewer
    if st.session_state.get("is_monitoring", False):
        active_id = st.session_state.get("active_stream_id", "webcam_0")
        st.subheader("📺 Real-Time AI Inference View")
        
        stream_url = f"{API_BASE_URL}/stream/{active_id}"
        
        # Updated parameter to prevent deprecation warning
        st.image(
            stream_url,
            caption=f"AI Processed Stream Node: {active_id}",
            use_container_width=True,
        )