"""
Edge Layer Comprehensive Integration Test
Tests all submodules, protocols, capture mechanisms, buffering, processing, and runtime.
"""

import asyncio
import logging
import sys
import numpy as np

# Configure minimal standard logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("edge_test")


def test_imports():
    logger.info("1️⃣ Testing all Module Imports...")
    try:
        from shared.schemas import FramePacket
        from shared.enums import CameraHealthState
        from configs.settings import settings

        from edge.protocols import (
            FrameCapturedEvent,
            DetectionEvent,
            CameraCommand,
            CommandType,
            HeartbeatMessage,
            CameraHealthReport,
        )
        from edge.capture import (
            BaseFrameCapture,
            USBCapture,
            RTSPCapture,
            FileCapture,
            ExponentialBackoffReconnect,
        )
        from edge.buffering import (
            NonBlockingFrameBuffer,
            MediaBoundedQueue,
            FrameDropStrategy,
            DropPolicy,
        )
        from edge.processing import (
            FramePreprocessor,
            FramePostprocessor,
            FrameProcessor,
        )
        from edge.camera_agent import (
            CameraHealthMonitor,
            WorkerRegistry,
            CameraLifecycleManager,
            CameraSupervisor,
            CameraWorker,
        )
        from edge.runtime import (
            EdgeRuntimeEngine,
            StreamScheduler,
            GracefulShutdownHandler,
        )

        logger.info("✅ All module imports successful with zero conflicts!")
        assert True
    except Exception as e:
        logger.error(f"❌ Import failed: {str(e)}", exc_info=True)
        assert False, f"Import failed: {str(e)}"


async def test_buffering_and_processing():
    logger.info("2️⃣ Testing Frame Buffering & Processing Pipeline...")
    from shared.schemas import FramePacket
    from edge.buffering import NonBlockingFrameBuffer
    from edge.processing import FrameProcessor

    buffer = NonBlockingFrameBuffer(maxsize=2)
    processor = FrameProcessor(pipeline_id="Test-Pipe-1")

    # Create dummy numpy frame (simulation)
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    packet = FramePacket(
        frame_id=1,
        camera_id="cam-01",
        raw_frame_ref=dummy_frame,
    )

    await buffer.put(packet)
    retrieved_packet = await buffer.get()

    assert retrieved_packet is not None, "Failed to retrieve frame packet from buffer"
    processed_packet = await processor.process_frame(retrieved_packet)

    assert processed_packet is not None, "Failed to process frame packet"
    logger.info(f"✅ Processing test passed: {processor.get_metrics()}")


async def test_runtime_engine():
    logger.info("3️⃣ Testing EdgeRuntimeEngine Initialization & Telemetry...")
    from edge.runtime import EdgeRuntimeEngine

    engine = EdgeRuntimeEngine()
    telemetry = engine.get_telemetry()

    assert "health" in telemetry
    assert "buffer" in telemetry
    assert "pipeline" in telemetry
    logger.info(f"✅ Runtime Telemetry Check passed: {telemetry}")


async def main():
    print("\n" + "=" * 50)
    print("🚀 STARTING EDGE LAYER INTEGRATION TEST")
    print("=" * 50 + "\n")

    test_imports()
    await test_buffering_and_processing()
    await test_runtime_engine()

    print("\n" + "=" * 50)
    print("🎉 ALL EDGE LAYER TESTS PASSED SUCCESSFULLY!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())