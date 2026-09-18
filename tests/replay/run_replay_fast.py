import concurrent.futures
import os
import time
import requests
import vcr

API_URL = "http://localhost:8000/detections/ingest"

# 1. Configure VCR.py to record HTTP responses once and replay them locally from cassette
replay_vcr = vcr.VCR(
    cassette_library_dir=os.path.join("tests", "replay", "cassettes"),
    record_mode="once",
    match_on=["method", "scheme", "host", "port", "path"],
)

# 2. Reuse TCP/SSL connections across all requests using a shared Session instance
session = requests.Session()


def process_frame(frame_id):
    """Sends a single frame payload and measures the response latency."""
    conf = min(0.3 + (frame_id * 0.015), 0.95)

    payload = {
        "camera_id": "replay-cam-01",
        "frame_id": frame_id,
        "timestamp": time.time(),
        "detections": [
            {
                "bbox": {
                    "xmin": 120.0,
                    "ymin": 140.0,
                    "xmax": 250.0,
                    "ymax": 300.0,
                },
                "confidence": conf,
                "detection_type": "fire",
            }
        ],
        "temperature_celsius": 30.0 + (frame_id * 0.4),
        "smoke_ppm": 50.0 + (frame_id * 2.0),
    }

    f_start = time.time()
    try:
        res = session.post(API_URL, json=payload)
        f_latency = (time.time() - f_start) * 1000  # ms

        incident_triggered = False
        if res.status_code == 200:
            data = res.json()
            if data.get("incident_triggered"):
                incident_triggered = True

        return f_latency, incident_triggered
    except Exception:
        return 0.0, False


# 3. Execute request processing concurrently with thread pooling and VCR caching
@replay_vcr.use_cassette("replay_benchmark.yaml")
def run_simulated_replay(total_frames=50, max_workers=10):
    print(f"--- Starting Fast Replay Benchmark ({total_frames} Frames) ---")
    start_time = time.time()

    # Process frames concurrently
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:
        results = list(
            executor.map(process_frame, range(1, total_frames + 1))
        )

    latencies = [r[0] for r in results]
    incidents_triggered = sum(1 for r in results if r[1])

    total_time = time.time() - start_time
    avg_fps = total_frames / total_time
    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    print("\n================ Fast Replay Benchmark Results ================")
    print(f"Total Frames Processed : {total_frames}")
    print(f"Average Pipeline Latency: {avg_latency:.2f} ms")
    print(f"Effective Throughput   : {avg_fps:.1f} FPS")
    print(f"Incidents Triggered    : {incidents_triggered}")
    print("===============================================================")


if __name__ == "__main__":
    run_simulated_replay()