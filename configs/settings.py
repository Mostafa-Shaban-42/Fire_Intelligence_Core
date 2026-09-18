import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    إدارة إعدادات النظام الموحدة مع القراءة المباشرة من المتغيرات البيئية أو ملف .env
    """

    # Base Application Settings
    APP_NAME: str = "FireIntelligence-Core"
    ENV: str = Field(
        default="development",
        description="Environment: development, staging, production",
    )
    DEBUG: bool = False
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )

    # Camera & RTSP Edge Settings
    RTSP_URL: str = Field(
        default="0",
        description="RTSP Stream URL or local camera index (e.g. '0')",
    )
    CAMERA_ID: str = "CAM_01"
    RTSP_CONNECT_TIMEOUT_SEC: float = 10.0
    RTSP_RECONNECT_INTERVAL_SEC: float = 3.0
    MAX_FRAME_BUFFER_SIZE: int = 2
    TARGET_FPS: float = 30.0

    # Perception Model Configs
    MODEL_PATH: str = "models/fire_smoke_v1.onnx"
    CONFIDENCE_THRESHOLD: float = 0.50
    INFERENCE_DEVICE: str = "CPU"  # Options: 'CPU', 'CUDA', 'TENSORRT'

    # Temporal Analysis & Risk Thresholds
    TEMPORAL_WINDOW_SIZE: int = 5
    INCIDENT_COOLDOWN_SEC: int = 30
    RISK_CONFIRMED_THRESHOLD: float = 70.0

    # Alert Channels Credentials
    TELEGRAM_BOT_TOKEN: str = Field(
        default="", description="Telegram Bot Token for alerts"
    )
    TELEGRAM_CHAT_ID: str = Field(
        default="", description="Telegram Chat ID for alerts"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()