import time
import requests

API_URL = "http://localhost:8000/detections/ingest"

def run_simulated_replay(total_frames=50):
    print(f"--- Starting Replay Benchmark ({total_frames} Frames) ---")
    start_time = time.time()
    latencies = []
    incidents_triggered = 0

    for frame_id in range(1, total_frames + 1):
        # محاكاة تصاعد المخاطر تدريجياً
        conf = min(0.3 + (frame_id * 0.015), 0.95)
        
        payload = {
            "camera_id": "replay-cam-01",
            "frame_id": frame_id,
            "timestamp": time.time(),
            "detections": [
                {
                    "bbox": {"xmin": 120.0, "ymin": 140.0, "xmax": 250.0, "ymax": 300.0},
                    "confidence": conf,
                    "detection_type": "fire"
                }
            ],
            "temperature_celsius": 30.0 + (frame_id * 0.4),
            "smoke_ppm": 50.0 + (frame_id * 2.0)
        }

        f_start = time.time()
        res = requests.post(API_URL, json=payload)
        f_latency = (time.time() - f_start) * 1000  # ms
        latencies.append(f_latency)

        if res.status_code == 200:
            data = res.json()
            if data.get("incident_triggered"):
                incidents_triggered += 1

        time.sleep(0.03)  # محاكاة بث 30 FPS

    total_time = time.time() - start_time
    avg_fps = total_frames / total_time
    avg_latency = sum(latencies) / len(latencies)

    print("\n================ Replay Benchmark Results ================")
    print(f"Total Frames Processed : {total_frames}")
    print(f"Average Pipeline Latency: {avg_latency:.2f} ms")
    print(f"Effective Throughput   : {avg_fps:.1f} FPS")
    print(f"Incidents Triggered    : {incidents_triggered}")
    print("==========================================================")

if __name__ == "__main__":
    run_simulated_replay()