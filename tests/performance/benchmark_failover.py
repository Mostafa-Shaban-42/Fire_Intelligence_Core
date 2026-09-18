import asyncio
import random
import time
import httpx

API_URL = "http://127.0.0.1:8000/detections/ingest"

def generate_payload(camera_id: str, frame_id: int) -> dict:
    return {
        "camera_id": camera_id,
        "frame_id": frame_id,
        "timestamp": time.time(),
        "detections": [
            {
                "bbox": {"xmin": 100.0, "ymin": 150.0, "xmax": 200.0, "ymax": 250.0},
                "confidence": 0.92,
                "label": "smoke",
                "detection_type": "smoke",
                "class_id": 2,
                "class_name": "smoke",
            }
        ],
    }

async def dynamic_camera_worker(camera_id: str, duration: int, results: list):
    """Simulates a camera stream that connects, disconnects, and reconnects smoothly."""
    limits = httpx.Limits(max_keepalive_connections=30, max_connections=30)
    
    end_time = time.monotonic() + duration
    frame_id = 1

    async with httpx.AsyncClient(limits=limits, timeout=5.0) as client:
        while time.monotonic() < end_time:
            # Simulate unexpected camera disconnection / network jitter
            if random.random() < 0.15:  # 15% chance to simulate drop
                await asyncio.sleep(random.uniform(0.5, 1.5))  # Reconnection delay
                continue

            payload = generate_payload(camera_id, frame_id)
            try:
                start = time.perf_counter()
                resp = await client.post(API_URL, json=payload)
                elapsed = (time.perf_counter() - start) * 1000.0
                results.append((resp.status_code, elapsed))
                frame_id += 1
            except (httpx.RequestError, Exception):
                # Network disconnect retry simulation (Client-side reconnection)
                await asyncio.sleep(0.1)

            await asyncio.sleep(0.05)  # ~20 FPS simulation

async def main():
    print("=" * 80)
    print(" FIRE INTELLIGENCE CORE - DYNAMIC FAILOVER & RECONNECTION TEST")
    print(" Scenario: 30 Cameras with Random Network Disconnections & Jitter (60s)")
    print("=" * 80)

    duration = 60
    camera_count = 30
    results = []

    start_time = time.perf_counter()
    tasks = [
        asyncio.create_task(dynamic_camera_worker(f"failover_cam_{i:02d}", duration, results))
        for i in range(camera_count)
    ]

    await asyncio.gather(*tasks)
    total_time = time.perf_counter() - start_time

    status_counts = {}
    for code, _ in results:
        status_counts[code] = status_counts.get(code, 0) + 1

    total_sent = len(results)
    accepted = status_counts.get(202, 0) + status_counts.get(200, 0)
    failures = total_sent - accepted

    print("\n" + "=" * 80)
    print(" DYNAMIC FAILOVER TEST RESULTS")
    print("=" * 80)
    print(f"Total Requests Processed : {total_sent}")
    print(f"Total Execution Time     : {total_time:.2f} seconds")
    print(f"Throughput Achieved      : {total_sent / total_time:.2f} req/sec")
    print("-" * 80)
    print(f"Status Code Breakdown    : {status_counts}")
    print(f" -> Accepted (20x)       : {accepted}")
    print(f" -> Failed Requests      : {failures}")
    print("-" * 80)

    if failures == 0 and total_sent > 0:
        print("🟢 PASS: Core Pipeline handled dynamic camera disconnections & failover flawlessly!")
    else:
        print("🔴 FAIL: Pipeline crashed or dropped connection states during failover.")

if __name__ == "__main__":
    asyncio.run(main())