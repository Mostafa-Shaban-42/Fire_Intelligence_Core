import asyncio
import pytest
from core.engine.pipeline_worker import PipelineWorker

@pytest.mark.asyncio
async def test_pipeline_worker_can_start_and_stop():
    """Verifies the lifecycle contract of the production pipeline worker."""
    worker = PipelineWorker(
        batch_size=4,
        flush_interval_sec=0.001,
    )

    await worker.start()
    try:
        assert worker.is_running is True
    finally:
        await worker.stop()

    assert worker.is_running is False


@pytest.mark.asyncio
async def test_pipeline_worker_start_is_idempotent():
    """Calling start twice must not crash or degrade state."""
    worker = PipelineWorker(
        batch_size=4,
        flush_interval_sec=0.001,
    )

    await worker.start()
    try:
        # Re-calling start should be handled gracefully
        await worker.start()
        assert worker.is_running is True
    finally:
        await worker.stop()


@pytest.mark.asyncio
async def test_pipeline_worker_stop_is_idempotent():
    """Calling stop multiple times must remain safe."""
    worker = PipelineWorker(
        batch_size=4,
        flush_interval_sec=0.001,
    )

    await worker.start()
    await worker.stop()
    await worker.stop()

    assert worker.is_running is False