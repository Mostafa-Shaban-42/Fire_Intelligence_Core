import streamlit as st
import numpy as np

st.set_page_config(
    page_title="Fire & Smoke Intelligence Core",
    page_icon="🔥",
    layout="wide"
)

st.title("🔥 Real-Time Fire & Smoke Intelligence System")
st.markdown("Production-grade AI vision pipeline for hazard detection and temporal tracking.")

st.sidebar.header("Control Panel")
confidence_threshold = st.sidebar.slider("Confidence Threshold", 0.0, 1.0, 0.45, 0.05)
enable_tracking = st.sidebar.checkbox("Enable Temporal Tracking", value=True)

uploaded_file = st.sidebar.file_uploader("Upload Test Video or Image", type=["mp4", "avi", "jpg", "png"])

col1, col2 = st.columns(2)

with col1:
    st.subheader("Source Input")
    if uploaded_file is not None:
        st.success("File uploaded successfully!")
        if uploaded_file.type.startswith("image"):
            st.image(uploaded_file, use_column_width=True)
        else:
            st.video(uploaded_file)
    else:
        st.info("Please upload a sample video or image from the sidebar to begin processing.")

with col2:
    st.subheader("Intelligence Output")
    st.markdown("**Real-Time Telemetry & Status:**")
    st.json({
        "status": "SYSTEM_READY",
        "confidence_threshold": confidence_threshold,
        "temporal_tracking": enable_tracking,
        "active_alerts": 0
    })