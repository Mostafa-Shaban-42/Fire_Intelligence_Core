"""
Alert Engine Layer: Manages alert queueing, multi-channel dispatch, retries, rate limiting, and delivery idempotency.
"""
from alerts.alert_engine import AlertEngine

__all__ = ["AlertEngine"]