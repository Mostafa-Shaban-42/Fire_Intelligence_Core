from __future__ import annotations

from typing import Any, Dict, List

import cv2
import numpy as np
import streamlit as st


def draw_detection(
    frame: np.ndarray,
    detection: Dict[str, Any],
) -> np.ndarray:
    """Draws one detection bounding box on a static frame array."""
    bbox = detection.get("bbox", {})
    xmin = int(bbox.get("xmin", bbox.get("x1", 0)))
    ymin = int(bbox.get("ymin", bbox.get("y1", 0)))
    xmax = int(bbox.get("xmax", bbox.get("x2", 0)))
    ymax = int(bbox.get("ymax", bbox.get("y2", 0)))

    confidence = detection.get(
        "confidence",
        detection.get("smoothed_confidence", 0.0),
    )

    label = detection.get(
        "detection_type",
        detection.get("class_name", "object"),
    )

    cv2.rectangle(
        frame,
        (xmin, ymin),
        (xmax, ymax),
        (0, 0, 255),
        3,
    )

    text = f"{label.upper()} {confidence:.1%}"

    cv2.putText(
        frame,
        text,
        (xmin, max(ymin - 10, 20)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 255),
        2,
        cv2.LINE_AA,
    )

    return frame


def render_camera_frame(
    placeholder,
    frame: np.ndarray,
    detections: List[Dict[str, Any]] | None = None,
) -> None:
    """Draws and displays one static frame (Legacy Support)."""
    display_frame = frame.copy()

    for detection in detections or []:
        display_frame = draw_detection(
            display_frame,
            detection,
        )

    rgb_frame = cv2.cvtColor(
        display_frame,
        cv2.COLOR_BGR2RGB,
    )

    placeholder.image(
        rgb_frame,
        channels="RGB",
        width="stretch",
    )


def create_camera_placeholder():
    return st.empty()


def render_camera_stream(stream_url: str) -> None:
    """
    Renders MJPEG stream directly using Streamlit native image component.
    Fixes CORS / Mixed Content issues and prevents blank dark screen.
    """
    st.image(
        stream_url,
        caption="🔥 Live AI Fire & Smoke Detection Stream",
        width="stretch",
    )