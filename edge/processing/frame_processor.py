import logging
import time
from typing import Any, Dict, Optional
from edge.processing.postprocessing import FramePostprocessor
from edge.processing.preprocessing import FramePreprocessor
from shared.schemas import FramePacket

logger = logging.getLogger(__name__)


class FrameProcessor:
    """Orchestrates preprocessing and pipeline latency benchmarking."""

    def __init__(self, pipeline_id: str):
        self.pipeline_id = pipeline_id
        self.preprocessor = FramePreprocessor()
        self.postprocessor = FramePostprocessor()
        self.processed_count = 0
        self.total_pipeline_latency_ms = 0.0

    async def process_frame(self, frame_packet: FramePacket) -> Optional[FramePacket]:
        t0 = time.time()

        if frame_packet.raw_frame_ref is None:
            logger.warning(
                f"[{self.pipeline_id}] Null frame reference received at frame_id={frame_packet.frame_id}"
            )
            return None

        # Process frame
        _ = self.preprocessor.preprocess(frame_packet.raw_frame_ref)

        stage_latency = (time.time() - t0) * 1000.0
        self.total_pipeline_latency_ms += stage_latency
        self.processed_count += 1

        return frame_packet

    def get_metrics(self) -> Dict[str, Any]:
        avg_latency = (
            self.total_pipeline_latency_ms / self.processed_count
            if self.processed_count > 0
            else 0.0
        )
        return {
            "pipeline_id": self.pipeline_id,
            "frames_processed": self.processed_count,
            "avg_pipeline_stage_latency_ms": round(avg_latency, 2),
        }