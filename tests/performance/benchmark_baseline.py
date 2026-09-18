import os
import sys
import time
import numpy as np
import requests

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

API_URL = "http://localhost:8000/detections/ingest"


def run_performance_baseline(total_frames=50):
    print(
        f"--- Running Real System Performance Baseline ({total_frames} Sequential Frames) ---"
    )

    session = requests.Session()

    # --- Warm-up Request (Ignored from metrics) ---
    warmup_payload = {
        "camera_id": "warmup-cam",
        "frame_id": 0,
        "timestamp": time.time(),
        "detections": [],
        "temperature_celsius": 25.0,
        "smoke_ppm": 10.0,
    }
    try:
        session.post(API_URL, json=warmup_payload, timeout=5)
        print("Warm-up request sent to establish TCP session...\n")
    except Exception as e:
        print(f"Warm-up failed: {e}\n")

    # --- Main Benchmark Loop ---
    latencies = []
    errors = 0
    incidents_triggered = 0

    benchmark_start = time.time()

    for frame_id in range(1, total_frames + 1):
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

        f_start = time.perf_counter()
        try:
            res = session.post(API_URL, json=payload, timeout=10)
            f_latency = (time.perf_counter() - f_start) * 1000  # ms

            # دعم كل من 200 OK و 202 Accepted (الأنظمة المعتمدة على Queues)
            if res.status_code in (200, 202):
                latencies.append(f_latency)
                try:
                    data = res.json()
                    if isinstance(data, dict) and data.get("incident_triggered"):
                        incidents_triggered += 1
                except Exception:
                    pass

                spike_flag = " ⚠️ [SPIKE]" if f_latency > 100 else ""
                print(
                    f"Frame {frame_id:02d} | Client Latency: {f_latency:7.2f} ms | Status: {res.status_code}{spike_flag}"
                )
            else:
                errors += 1
                print(f"Frame {frame_id:02d} | ERROR: Status {res.status_code}")
        except Exception as e:
            errors += 1
            print(f"Frame {frame_id:02d} | EXCEPTION: {e}")

    total_time = time.time() - benchmark_start

    if latencies:
        p50 = np.percentile(latencies, 50)
        p95 = np.percentile(latencies, 95)
        p99 = np.percentile(latencies, 99)
        avg_latency = np.mean(latencies)
        min_latency = np.min(latencies)
        max_latency = np.max(latencies)
        throughput = len(latencies) / total_time
    else:
        p50 = p95 = p99 = avg_latency = min_latency = max_latency = (
            throughput
        ) = 0.0

    print("\n================ OFFICIAL PERFORMANCE BASELINE ================")
    print(f"Total Frames Attempted : {total_frames}")
    print(f"Successful Requests    : {len(latencies)}")
    print(f"Failed / Error Requests: {errors}")
    print(f"Incidents Triggered    : {incidents_triggered}")
    print("---------------------------------------------------------------")
    print(f"Throughput (FPS)       : {throughput:.2f} req/sec")
    print(f"Average Latency        : {avg_latency:.2f} ms")
    print(f"Min Latency            : {min_latency:.2f} ms")
    print(f"Max Latency            : {max_latency:.2f} ms")
    print("---------------------------------------------------------------")
    print(f"P50 Latency (Median)   : {p50:.2f} ms")
    print(f"P95 Latency            : {p95:.2f} ms")
    print(f"P99 Latency            : {p99:.2f} ms")
    print("===============================================================")


if __name__ == "__main__":
    run_performance_baseline()