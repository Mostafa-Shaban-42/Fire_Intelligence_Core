import argparse
import asyncio
import statistics
import time
import psutil
import httpx

API_URL = "http://127.0.0.1:8000/detections/ingest"

def generate_payload(camera_id: str, frame_id: int) -> dict:
    """Generates payload exactly matching the production API schema."""
    return {
        "camera_id": camera_id,
        "frame_id": frame_id,
        "timestamp": time.time(),
        "detections": [
            {
                "bbox": {
                    "xmin": 100.0,
                    "ymin": 150.0,
                    "xmax": 200.0,
                    "ymax": 250.0,
                },
                "confidence": 0.88,
                "label": "fire",
                "detection_type": "fire",
                "class_id": 1,
                "class_name": "fire",
            }
        ],
    }

async def send_frame(client: httpx.AsyncClient, camera_id: str, frame_id: int):
    payload = generate_payload(camera_id, frame_id)
    start = time.perf_counter()
    try:
        resp = await client.post(API_URL, json=payload, timeout=10.0)
        elapsed = (time.perf_counter() - start) * 1000.0
        is_success = resp.status_code in (200, 201, 202)
        return is_success, elapsed, resp.status_code
    except Exception:
        elapsed = (time.perf_counter() - start) * 1000.0
        return False, elapsed, 500

async def camera_worker(camera_id: int, duration: int, stats_collector: list, stop_event: asyncio.Event):
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=30)
    async with httpx.AsyncClient(limits=limits) as client:
        frame_id = 0
        end_time = time.time() + duration
        while time.time() < end_time and not stop_event.is_set():
            frame_id += 1
            success, latency, status = await send_frame(client, f"cam_{camera_id:02d}", frame_id)
            stats_collector.append((success, latency, status))
            await asyncio.sleep(0.01)

async def monitor_resources(duration: int, stop_event: asyncio.Event):
    print("\n--- RESOURCE MONITORING STARTED ---")
    print(f"{'Time (s)':<10} | {'CPU %':<8} | {'RAM (MB)':<10} | {'RAM %':<8}")
    print("-" * 45)
    
    start_time = time.time()
    process = psutil.Process()
    ram_samples = []
    
    while time.time() - start_time < duration and not stop_event.is_set():
        elapsed = int(time.time() - start_time)
        cpu = psutil.cpu_percent(interval=1.0)
        ram_info = process.memory_info()
        ram_mb = ram_info.rss / (1024 * 1024)
        ram_pct = psutil.virtual_memory().percent
        ram_samples.append(ram_mb)
        
        print(f"{elapsed:<10} | {cpu:<8.1f} | {ram_mb:<10.1f} | {ram_pct:<8.1f}")
        await asyncio.sleep(4.0)
        
    return ram_samples

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cameras", type=int, default=20)
    parser.add_argument("--duration", type=int, default=120)
    args = parser.parse_args()

    print("=" * 80)
    print(f" FIRE INTELLIGENCE CORE - SOAK TEST")
    print(f" Cameras: {args.cameras} | Duration: {args.duration}s ({args.duration / 60:.1f} mins)")
    print("=" * 80)

    stats = []
    stop_event = asyncio.Event()

    monitor_task = asyncio.create_task(monitor_resources(args.duration, stop_event))
    workers = [
        asyncio.create_task(camera_worker(i, args.duration, stats, stop_event))
        for i in range(1, args.cameras + 1)
    ]

    try:
        await asyncio.gather(*workers)
    finally:
        stop_event.set()
        ram_samples = await monitor_task

    total = len(stats)
    successes = sum(1 for s, _, _ in stats if s)
    latencies = [l for _, l, _ in stats]
    status_codes = {}
    for _, _, code in stats:
        status_codes[code] = status_codes.get(code, 0) + 1

    print("\n" + "=" * 80)
    print(" SOAK TEST FINAL RESULTS")
    print("=" * 80)
    print(f"Total Processed Requests : {total}")
    print(f"Successful Requests     : {successes}")
    print(f"Failed Requests         : {total - successes}")
    print(f"Success Rate            : {(successes / total) * 100:.2f}%" if total else "N/A")
    print(f"HTTP Status Codes Breakdown : {status_codes}")
    
    if latencies:
        latencies.sort()
        p50_idx = int(len(latencies) * 0.50)
        p95_idx = int(len(latencies) * 0.95)
        p99_idx = int(len(latencies) * 0.99)
        print(f"Average Latency         : {statistics.mean(latencies):.2f} ms")
        print(f"P50 Latency             : {latencies[p50_idx]:.2f} ms")
        print(f"P95 Latency             : {latencies[p95_idx]:.2f} ms")
        print(f"P99 Latency             : {latencies[p99_idx]:.2f} ms")

    if ram_samples:
        ram_diff = ram_samples[-1] - ram_samples[0]
        print(f"\nRAM Initial: {ram_samples[0]:.1f} MB | RAM Final: {ram_samples[-1]:.1f} MB | Delta: {ram_diff:+.1f} MB")
        if total > 0 and successes == total and ram_diff <= 150:
            print("🟢 PASS: 100% Success Rate and stable memory usage!")
        else:
            print("🔴 FAIL: Requests failed or memory growth detected.")

if __name__ == "__main__":
    asyncio.run(main())