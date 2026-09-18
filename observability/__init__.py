"""
Observability Layer: Standardized JSON logging, Prometheus metrics collection,
and OpenTelemetry distributed tracing.
"""
from observability.logging import setup_logging
from observability.metrics import MetricsCollector
from observability.tracing import setup_tracing

__all__ = ["setup_logging", "MetricsCollector", "setup_tracing"]