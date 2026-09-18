from __future__ import annotations

import os
from pathlib import Path


# ==============================================================================
# PATHS
# ==============================================================================

DASHBOARD_DIR = Path(__file__).resolve().parent

ASSETS_DIR = (
    DASHBOARD_DIR
    / "assets"
)

SOUNDS_DIR = (
    ASSETS_DIR
    / "sounds"
)

ALARM_SOUND_PATH = (
    SOUNDS_DIR
    / "alarm.wav"
)


# ==============================================================================
# API CONFIGURATION
# ==============================================================================

API_BASE_URL = os.getenv(
    "FIRE_CORE_API_URL",
    "http://127.0.0.1:8000",
)

DETECTION_INGEST_ENDPOINT = (
    "/detections/ingest"
)

HEALTH_ENDPOINT = os.getenv(
    "FIRE_CORE_HEALTH_ENDPOINT",
    "/health",
)

API_TIMEOUT_SECONDS = float(
    os.getenv(
        "FIRE_CORE_API_TIMEOUT",
        "10.0",
    )
)


# ==============================================================================
# CAMERA CONFIGURATION
# ==============================================================================

DEFAULT_CAMERA_INDEX = int(
    os.getenv(
        "FIRE_CAMERA_INDEX",
        "0",
    )
)

DEFAULT_CAMERA_ID = os.getenv(
    "FIRE_CAMERA_ID",
    "laptop-camera-01",
)

DEFAULT_FRAME_WIDTH = int(
    os.getenv(
        "FIRE_CAMERA_WIDTH",
        "1280",
    )
)

DEFAULT_FRAME_HEIGHT = int(
    os.getenv(
        "FIRE_CAMERA_HEIGHT",
        "720",
    )
)

DEFAULT_TARGET_FPS = int(
    os.getenv(
        "FIRE_CAMERA_FPS",
        "15",
    )
)


# ==============================================================================
# FRAME PROCESSING & STREAMING
# ==============================================================================

FRAME_SEND_INTERVAL_SECONDS = float(
    os.getenv(
        "FRAME_SEND_INTERVAL_SECONDS",
        "0.20",
    )
)


# ==============================================================================
# DASHBOARD CONFIGURATION
# ==============================================================================

APP_TITLE = (
    "Fire Intelligence Core"
)

APP_ICON = "🔥"

LAYOUT = "wide"


# ==============================================================================
# ALARM CONFIGURATION
# ==============================================================================

ALARM_ENABLED_BY_DEFAULT = True

ALARM_COOLDOWN_SECONDS = float(
    os.getenv(
        "ALARM_COOLDOWN_SECONDS",
        "5.0",
    )
)


# ==============================================================================
# UI STATUS
# ==============================================================================

STATUS_NORMAL = (
    "🟢 NORMAL"
)

STATUS_WARNING = (
    "🟡 WARNING"
)

STATUS_CRITICAL = (
    "🔴 CRITICAL"
)

STATUS_OFFLINE = (
    "⚫ OFFLINE"
)