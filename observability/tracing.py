import logging
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)


def setup_tracing(service_name: str = "fire-intelligence-service") -> trace.Tracer:
    """
    Initializes OpenTelemetry TracerProvider and global tracer instance.
    """
    resource = Resource.create(attributes={"service.name": service_name})
    provider = TracerProvider(resource=resource)
    
    # Export spans to stdout console (Can be swapped with OTLPSpanExporter for Jaeger/Tempo)
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    logger.info(f"OpenTelemetry tracing initialized for service: {service_name}")
    return trace.get_tracer(service_name)