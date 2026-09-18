# ============================================================
# Fire Intelligence Core
# Production Container (GPU Enabled)
# ============================================================

FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime


# ------------------------------------------------------------
# Runtime Environment
# ------------------------------------------------------------

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1


# ------------------------------------------------------------
# Working Directory
# ------------------------------------------------------------

WORKDIR /app


# ------------------------------------------------------------
# System Dependencies
# ------------------------------------------------------------

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        libgl1-mesa-glx \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*


# ------------------------------------------------------------
# Python Dependencies
# ------------------------------------------------------------

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt


# ------------------------------------------------------------
# Application
# ------------------------------------------------------------

COPY . .


# ------------------------------------------------------------
# Non-root Runtime User
# ------------------------------------------------------------

RUN useradd \
        --create-home \
        --shell /usr/sbin/nologin \
        appuser \
    && chown -R appuser:appuser /app

USER appuser


# ------------------------------------------------------------
# Network
# ------------------------------------------------------------

EXPOSE 8000


# ------------------------------------------------------------
# Container Health Check
# ------------------------------------------------------------

HEALTHCHECK \
    --interval=30s \
    --timeout=5s \
    --start-period=10s \
    --retries=3 \
    CMD curl --fail http://127.0.0.1:8000/health || exit 1


# ------------------------------------------------------------
# Startup
# ------------------------------------------------------------

CMD [
    "uvicorn",
    "api.main:app",
    "---host",
    "0.0.0.0",
    "--port",
    "8000"
]