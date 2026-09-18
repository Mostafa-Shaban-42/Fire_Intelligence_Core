import asyncio
import time
import statistics
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
                "confidence": 0.95,
                "label": "fire",
                "detection_type": "fire",
                "class_id": 1,
                "class_name": "fire",
            }
        ],
    }

async def flood_worker(worker_id: int, total_requests: int, results: list):
    """Flood client to intentionally saturate the server queue."""
    limits = httpx.Limits(max_keepalive_connections=100, max_connections=100)
    async with httpx.AsyncClient(limits=limits, timeout=5.0) as client:
        for i in range(total_requests):
            payload = generate_payload(f"flood_cam_{worker_id:02d}", i + 1)
            try:
                start = time.perf_counter()
                resp = await client.post(API_URL, json=payload)
                elapsed = (time.perf_counter() - start) * 1000.0
                results.append((resp.status_code, elapsed))
            except Exception:
                results.append((500, 0.0))

async def main():
    print("=" * 80)
    print(" FIRE INTELLIGENCE CORE - BACKPRESSURE & QUEUE SATURATION TEST")
    print(" Aggressive Flooding Scenario: 50 Concurrent Workers / 2,500 Instant Requests")
    print("=" * 80)

    workers_count = 50
    requests_per_worker = 50
    results = []

    start_time = time.perf_counter()
    tasks = [
        asyncio.create_task(flood_worker(w, requests_per_worker, results))
        for w in range(workers_count)
    ]

    await asyncio.gather(*tasks)
    total_time = time.perf_counter() - start_time

    status_counts = {}
    successful_latencies = []
    
    for code, latency in results:
        status_counts[code] = status_counts.get(code, 0) + 1
        # قبول الأكواد 200 و 201 و 202 كطلبات ناجحة
        if code in (200, 201, 202):
            successful_latencies.append(latency)

    total_sent = len(results)
    accepted = len(successful_latencies)
    rate_limited = status_counts.get(429, 0)
    service_unavailable = status_counts.get(503, 0)
    failures = status_counts.get(500, 0)

    print("\n" + "=" * 80)
    print(" BACKPRESSURE TEST RESULTS")
    print("=" * 80)
    print(f"Total Requests Flooded : {total_sent}")
    print(f"Total Execution Time   : {total_time:.2f} seconds")
    print(f"Throughput Offered     : {total_sent / total_time:.2f} req/sec")
    print("-" * 80)
    print(f"Status Code Breakdown  : {status_counts}")
    print(f" -> Accepted (20x)    : {accepted}")
    print(f" -> Rate-Limited (429): {rate_limited}")
    print(f" -> Overloaded (503)  : {service_unavailable}")
    print(f" -> Server Errors(500): {failures}")
    print("-" * 80)

    if successful_latencies:
        sorted_latencies = sorted(successful_latencies)
        p50 = statistics.median(sorted_latencies)
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
        avg_lat = statistics.mean(sorted_latencies)
        
        print(f"Successful Requests Latency Metrics:")
        print(f" -> Avg Latency       : {avg_lat:.2f} ms")
        print(f" -> P50 Latency       : {p50:.2f} ms")
        print(f" -> P95 Latency       : {p95:.2f} ms")
        print(f" -> P99 Latency       : {p99:.2f} ms")
        print("-" * 80)

    # Criteria for Graceful Backpressure
    if failures == 0:
        print("🟢 PASS: Server handled extreme saturation gracefully without crashing (0 Server Errors)!")
    else:
        print("🔴 FAIL: Unhandled server errors encountered during backpressure test.")

if __name__ == "__main__":
    asyncio.run(main())