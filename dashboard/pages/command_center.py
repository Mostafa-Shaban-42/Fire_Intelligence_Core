from __future__ import annotations

import os
import tempfile
import time
import folium
import requests
import streamlit as st
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

from dashboard.components.incident_panel import render_incident_panel
from dashboard.components.metrics import render_system_metrics

API_BASE_URL = "http://localhost:8000/cameras"


def fetch_registered_cameras() -> list[dict]:
    try:
        response = requests.get(API_BASE_URL, timeout=2.0)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []


def check_backend_health() -> bool:
    """Checks if FastAPI server is responsive."""
    try:
        res = requests.get("http://localhost:8000/docs", timeout=1.5)
        return res.status_code == 200
    except Exception:
        return False


def fetch_real_live_ip_location() -> tuple[float, float, str]:
    """Dynamically fetches real user location coordinates via IP Geolocation API."""
    try:
        response = requests.get("http://ip-api.com/json/", timeout=2.5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                lat = float(data.get("lat"))
                lon = float(data.get("lon"))
                city = data.get("city", "Live Location")
                country = data.get("country", "")
                return lat, lon, f"{city}, {country}"
    except Exception:
        pass
    return 30.0444, 31.2357, "Detected System Node"


def render_command_center() -> None:
    st.title("🔥 Fire Intelligence Command Center")
    st.caption(
        "Real-time fire detection with dynamic auto-located spatial GIS camera mapping."
    )

    # Sync system state with real backend status
    system_state = st.session_state.system_state
    system_state["backend_online"] = check_backend_health()
    render_system_metrics(system_state)

    st.divider()

    # Detect dynamic real location on device startup
    if "user_lat" not in st.session_state:
        loc = get_geolocation()
        if loc and "coords" in loc and loc["coords"].get("latitude"):
            st.session_state["user_lat"] = float(loc["coords"]["latitude"])
            st.session_state["user_lng"] = float(loc["coords"]["longitude"])
            st.session_state["user_loc_name"] = "GPS Exact Device Location"
        else:
            auto_lat, auto_lng, loc_name = fetch_real_live_ip_location()
            st.session_state["user_lat"] = auto_lat
            st.session_state["user_lng"] = auto_lng
            st.session_state["user_loc_name"] = loc_name

    auto_lat = st.session_state["user_lat"]
    auto_lng = st.session_state["user_lng"]
    loc_name = st.session_state["user_loc_name"]

    left_column, right_column = st.columns([2, 1])
    cameras = fetch_registered_cameras()

    with left_column:
        st.subheader("🌐 Dynamic GIS Camera Map")
        st.caption(f"📍 **Detected Real Node Center:** {loc_name}")

        gis_map = folium.Map(
            location=[auto_lat, auto_lng],
            zoom_start=12,
            tiles="OpenStreetMap",
        )

        # Highlight device real location
        folium.CircleMarker(
            location=[auto_lat, auto_lng],
            radius=9,
            popup=f"📍 Current Station Device ({loc_name})",
            color="#00FFFF",
            fill=True,
            fill_color="#00FFFF",
            fill_opacity=0.6,
        ).add_to(gis_map)

        for cam in cameras:
            has_fire = cam.get("has_fire", False)
            is_active = cam.get("is_active", True)

            color = "red" if has_fire else ("green" if is_active else "gray")
            icon_symbol = "fire" if has_fire else ("video-camera" if is_active else "stop")
            status_text = "🔥 FIRE DETECTED!" if has_fire else ("🟢 Active & Monitoring" if is_active else "⚪ Inactive")

            popup_html = f"""
            <div style="font-family: Arial, sans-serif; width: 170px;">
                <h4 style="margin-bottom: 5px;"><b>{cam['location']}</b></h4>
                <p style="margin: 0; font-size: 12px;"><b>ID:</b> {cam['camera_id']}</p>
                <p style="margin: 5px 0; font-size: 12px;"><b>Status:</b> {status_text}</p>
                <p style="margin: 0; font-size: 11px; color: gray;">Lat: {cam['latitude']:.4f}, Lng: {cam['longitude']:.4f}</p>
            </div>
            """

            folium.Marker(
                location=[cam["latitude"], cam["longitude"]],
                popup=folium.Popup(popup_html, max_width=220),
                tooltip=f"{cam['location']} ({cam['camera_id']})",
                icon=folium.Icon(color=color, icon=icon_symbol, prefix="fa"),
            ).add_to(gis_map)

        st_folium(gis_map, width="100%", height=480, key="gis_camera_map")

    with right_column:
        st.subheader("⚙️ Camera Management")

        action_tab = st.radio(
            "Select Action:",
            ["➕ Register Camera", "🗑️ Remove Camera", "📹 Upload Fire Test Video"],
            horizontal=False,
        )

        st.divider()

        if action_tab == "➕ Register Camera":
            with st.form("register_camera_form", clear_on_submit=True):
                cam_id = st.text_input("Camera ID", placeholder="cam_warehouse_01")
                location = st.text_input("Location Name", value=f"Station Near {loc_name}")
                rtsp_url = st.text_input("RTSP / Stream Source", value="0")

                col_lat, col_lng = st.columns(2)
                with col_lat:
                    latitude = st.number_input("Latitude", value=auto_lat, format="%.4f")
                with col_lng:
                    longitude = st.number_input("Longitude", value=auto_lng, format="%.4f")

                submit_button = st.form_submit_button("Register Camera", type="primary", use_container_width=True)

                if submit_button and cam_id and location:
                    payload = {
                        "camera_id": cam_id,
                        "location": location,
                        "rtsp_url": rtsp_url,
                        "latitude": latitude,
                        "longitude": longitude,
                        "is_active": True,
                    }
                    try:
                        res = requests.post(API_BASE_URL, json=payload, timeout=2.0)
                        if res.status_code == 201:
                            st.success("Camera registered successfully!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"API Connection error: {e}")

        elif action_tab == "🗑️ Remove Camera":
            if cameras:
                cam_to_delete = st.selectbox(
                    "Select Camera to Delete:",
                    options=[c["camera_id"] for c in cameras],
                )
                if st.button("Confirm Delete", type="primary", use_container_width=True):
                    try:
                        res = requests.delete(f"{API_BASE_URL}/{cam_to_delete}", timeout=2.0)
                        if res.status_code == 200:
                            st.success(f"Camera '{cam_to_delete}' removed.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"API Error: {e}")

        elif action_tab == "📹 Upload Fire Test Video":
            uploaded_file = st.file_uploader(
                "Upload test video (.mp4, .avi) for AI Evaluation",
                type=["mp4", "avi", "mov"],
            )

            if uploaded_file is not None and st.button("Process & Register Test Video", type="primary", use_container_width=True):
                temp_dir = tempfile.gettempdir()
                file_path = os.path.join(temp_dir, f"fire_test_{int(time.time())}.mp4")
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                new_cam_id = f"test_vid_{int(time.time())}"
                payload = {
                    "camera_id": new_cam_id,
                    "location": f"Test Video ({loc_name})",
                    "rtsp_url": file_path,
                    "latitude": auto_lat + 0.002,
                    "longitude": auto_lng + 0.002,
                    "is_active": True,
                }
                try:
                    res = requests.post(API_BASE_URL, json=payload, timeout=2.0)
                    if res.status_code == 201:
                        st.success(f"Video registered as `{new_cam_id}`! Go to Live Monitoring tab to see AI Stream.")
                except Exception as e:
                    st.error(f"API Error: {e}")

    st.divider()
    render_incident_panel(st.session_state.incidents)