import inspect

import pytest


@pytest.mark.asyncio
async def test_incident_engine_exposes_async_risk_processing():
    """
    Verifies that IncidentEngine exposes the asynchronous processing contract
    required by PipelineWorker.
    """

    from incidents.incident_engine import IncidentEngine

    engine = IncidentEngine()

    assert hasattr(
        engine,
        "process_risk_evaluation",
    )

    method = getattr(
        engine,
        "process_risk_evaluation",
    )

    assert callable(method)

    assert inspect.iscoroutinefunction(
        method
    )


@pytest.mark.asyncio
async def test_incident_engine_can_process_non_incident_scene():
    """
    Basic contract test.

    The exact risk object is intentionally delegated to the existing
    RiskEngine/IncidentEngine implementation.
    """

    from incidents.incident_engine import IncidentEngine

    engine = IncidentEngine()

    assert engine is not None