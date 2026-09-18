import asyncio

import pytest

from core.engine.async_queue_manager import (
    ProductionFrameQueue,
)


@pytest.mark.asyncio
async def test_queue_enqueue_is_non_blocking():
    """
    Queue insertion must not require awaiting downstream consumers.
    """

    queue = ProductionFrameQueue(
        maxsize=10
    )

    start = asyncio.get_running_loop().time()

    result = queue.enqueue(
        camera_id="CAM_TEST",
        frame_id=1,
        detections=[],
        trace_id="test-trace-1",
    )

    elapsed = (
        asyncio.get_running_loop().time()
        - start
    )

    assert result is True
    assert queue.size() == 1

    # This is a guard against accidental blocking behavior.
    assert elapsed < 0.1


@pytest.mark.asyncio
async def test_queue_preserves_newest_frame_under_backpressure():
    """
    When the queue is full, the oldest frame must be discarded so that the
    newest frame can enter the real-time pipeline.
    """

    queue = ProductionFrameQueue(
        maxsize=2
    )

    assert queue.enqueue(
        camera_id="CAM_TEST",
        frame_id=1,
        detections=[],
    )

    assert queue.enqueue(
        camera_id="CAM_TEST",
        frame_id=2,
        detections=[],
    )

    assert queue.enqueue(
        camera_id="CAM_TEST",
        frame_id=3,
        detections=[],
    )

    assert queue.dropped_frames == 1
    assert queue.size() == 2

    batch = await queue.dequeue_batch(
        max_batch_size=10,
        timeout=0.01,
    )

    frame_ids = [
        item.frame_id
        for item in batch
    ]

    assert frame_ids == [2, 3]

    for _ in batch:
        queue.task_done()


@pytest.mark.asyncio
async def test_queue_task_accounting_is_balanced():
    """
    Every dequeued item must be completed exactly once.
    """

    queue = ProductionFrameQueue(
        maxsize=10
    )

    for frame_id in range(5):

        assert queue.enqueue(
            camera_id="CAM_TEST",
            frame_id=frame_id,
            detections=[],
        )

    batch = await queue.dequeue_batch(
        max_batch_size=5,
        timeout=0.01,
    )

    assert len(batch) == 5

    for _ in batch:
        queue.task_done()

    await asyncio.wait_for(
        queue.queue.join(),
        timeout=1.0,
    )