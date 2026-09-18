# tests/performance/benchmark_concurrent.py
from __future__ import annotations

import asyncio
import json
import statistics
import time
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

# ==============================================================================
# FIRE INTELLIGENCE CORE
# PRODUCTION CONCURRENCY BENCHMARK SUITE
# ==============================================================================

BASE_URL = "http://127.0.0.1:8000"
ENDPOINT = "/detections/ingest"
METRICS_ENDPOINT = "/detections/metrics/summary"

REQUEST_TIMEOUT_SECONDS = 10.0

WARMUP_REQUESTS = 3
INTER_FRAME_DELAY_SECONDS = 0.001
SCENARIO_COOLDOWN_SECONDS = 3.0

SUCCESS_STATUS_CODES = {200, 201, 202}

SCENARIOS = [
    ("Scenario A - Baseline Single Camera", 1, 50),
    ("Scenario B - 5 Concurrent Cameras", 5, 20),
    ("Scenario C - 10 Concurrent Cameras", 10, 20),
    ("Scenario D - 20 Stress Cameras", 20, 20),
]


# ==============================================================================
# DATA MODELS
# ==============================================================================


@dataclass
class RequestResult:
    """Represents the result of one HTTP request."""

    success: bool
    latency_ms: float
    status_code: Optional[int]
    error_type: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ScenarioResult:
    """Represents aggregated metrics for one benchmark scenario."""

    name: str
    cameras: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    wall_clock_duration: float
    throughput: float
    average_latency: float
    min_latency: float
    max_latency: float
    p50: float
    p95: float
    p99: float
    errors: Counter


# ==============================================================================
# PAYLOAD GENERATION
# ==============================================================================


def generate_payload(camera_id: str, frame_id: int) -> Dict[str, Any]:
    """Generates a payload matching the API schema."""
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


# ==============================================================================
# PERCENTILE CALCULATION
# ==============================================================================


def calculate_percentile(
    sorted_values: List[float],
    percentile: float,
) -> float:
    """Calculates a percentile using linear interpolation."""
    if not sorted_values:
        return 0.0

    if len(sorted_values) == 1:
        return sorted_values[0]

    position = (len(sorted_values) - 1) * percentile
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    weight = position - lower_index

    return (
        sorted_values[lower_index]
        + (sorted_values[upper_index] - sorted_values[lower_index]) * weight
    )


# ==============================================================================
# ERROR CLASSIFICATION
# ==============================================================================


def classify_exception(exception: Exception) -> str:
    """Converts HTTPX exceptions into stable benchmark error categories."""
    if isinstance(exception, httpx.ConnectError):
        return "CONNECT_ERROR"
    if isinstance(exception, httpx.ConnectTimeout):
        return "CONNECT_TIMEOUT"
    if isinstance(exception, httpx.ReadTimeout):
        return "READ_TIMEOUT"
    if isinstance(exception, httpx.WriteTimeout):
        return "WRITE_TIMEOUT"
    if isinstance(exception, httpx.PoolTimeout):
        return "POOL_TIMEOUT"
    if isinstance(exception, httpx.TimeoutException):
        return "TIMEOUT"
    if isinstance(exception, httpx.RequestError):
        return "REQUEST_ERROR"

    return type(exception).__name__.upper()


# ==============================================================================
# SINGLE REQUEST
# ==============================================================================


async def send_frame_request(
    client: httpx.AsyncClient,
    camera_id: str,
    frame_id: int,
) -> RequestResult:
    """Sends one detection frame to the Fire Intelligence Core API."""
    payload = generate_payload(camera_id, frame_id)
    start_time = time.perf_counter()

    try:
        response = await client.post(ENDPOINT, json=payload)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        if response.status_code in SUCCESS_STATUS_CODES:
            return RequestResult(
                success=True,
                latency_ms=latency_ms,
                status_code=response.status_code,
            )

        error_type = f"HTTP_{response.status_code}"
        if camera_id == "cam_01" and frame_id == 1:
            print(
                f"\n[HTTP ERROR]\nStatus : {response.status_code}\nBody   : {response.text[:1000]}\n"
            )

        return RequestResult(
            success=False,
            latency_ms=latency_ms,
            status_code=response.status_code,
            error_type=error_type,
            error_message=response.text[:1000],
        )

    except Exception as exception:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        error_type = classify_exception(exception)

        if camera_id == "cam_01" and frame_id == 1:
            print(
                f"\n[REQUEST EXCEPTION]\nType    : {type(exception).__name__}\nCategory: {error_type}\nMessage : {exception}\n"
            )

        return RequestResult(
            success=False,
            latency_ms=latency_ms,
            status_code=None,
            error_type=error_type,
            error_message=str(exception),
        )


# ==============================================================================
# CAMERA STREAM SIMULATION
# ==============================================================================


async def simulate_camera_stream(
    client: httpx.AsyncClient,
    camera_id: str,
    frame_count: int,
) -> List[RequestResult]:
    """Simulates one camera sending frames sequentially."""
    results: List[RequestResult] = []

    for frame_id in range(1, frame_count + 1):
        result = await send_frame_request(
            client=client,
            camera_id=camera_id,
            frame_id=frame_id,
        )
        results.append(result)

        if INTER_FRAME_DELAY_SECONDS > 0:
            await asyncio.sleep(INTER_FRAME_DELAY_SECONDS)

    return results


# ==============================================================================
# WARM-UP
# ==============================================================================


async def run_warmup(client: httpx.AsyncClient) -> None:
    """Sends warm-up requests before measurements begin."""
    print(f"Warm-up phase: sending {WARMUP_REQUESTS} request(s)...")

    for warmup_index in range(1, WARMUP_REQUESTS + 1):
        result = await send_frame_request(
            client=client,
            camera_id="warmup_cam",
            frame_id=warmup_index,
        )
        if not result.success:
            print(
                f"WARNING: Warm-up request {warmup_index} failed ({result.error_type})"
            )


# ==============================================================================
# SCENARIO EXECUTION
# ==============================================================================


async def run_scenario(
    name: str,
    num_cameras: int,
    frames_per_camera: int,
) -> ScenarioResult:
    """Executes one concurrency benchmark scenario."""
    total_expected_requests = num_cameras * frames_per_camera

    print("\n" + "=" * 79)
    print(f" Running: {name}")
    print(
        f" Cameras: {num_cameras} concurrent | Frames per camera: {frames_per_camera}"
    )
    print(f" Total expected requests: {total_expected_requests}")
    print("=" * 79)

    limits = httpx.Limits(
        max_keepalive_connections=num_cameras + 10,
        max_connections=num_cameras + 20,
    )
    timeout = httpx.Timeout(REQUEST_TIMEOUT_SECONDS)

    async with httpx.AsyncClient(
        base_url=BASE_URL,
        limits=limits,
        timeout=timeout,
    ) as client:
        await run_warmup(client)

        start_wall_time = time.perf_counter()

        tasks = [
            simulate_camera_stream(
                client=client,
                camera_id=f"cam_{camera_index:02d}",
                frame_count=frames_per_camera,
            )
            for camera_index in range(1, num_cameras + 1)
        ]

        camera_results = await asyncio.gather(*tasks)
        end_wall_time = time.perf_counter()

    all_results = [res for stream in camera_results for res in stream]
    successful_results = [r for r in all_results if r.success]
    failed_results = [r for r in all_results if not r.success]
    successful_latencies = sorted(r.latency_ms for r in successful_results)

    error_counter = Counter(
        r.error_type or "UNKNOWN_ERROR" for r in failed_results
    )

    total_duration = end_wall_time - start_wall_time
    total_requests = len(all_results)
    successful_requests = len(successful_results)
    failed_requests = len(failed_results)

    success_rate = (
        (successful_requests / total_requests) * 100.0
        if total_requests > 0
        else 0.0
    )
    throughput = (
        successful_requests / total_duration if total_duration > 0 else 0.0
    )

    if successful_latencies:
        average_latency = statistics.mean(successful_latencies)
        min_latency = min(successful_latencies)
        max_latency = max(successful_latencies)
        p50 = calculate_percentile(successful_latencies, 0.50)
        p95 = calculate_percentile(successful_latencies, 0.95)
        p99 = calculate_percentile(successful_latencies, 0.99)
    else:
        average_latency = min_latency = max_latency = p50 = p95 = p99 = 0.0

    scenario_result = ScenarioResult(
        name=name,
        cameras=num_cameras,
        total_requests=total_requests,
        successful_requests=successful_requests,
        failed_requests=failed_requests,
        success_rate=success_rate,
        wall_clock_duration=total_duration,
        throughput=throughput,
        average_latency=average_latency,
        min_latency=min_latency,
        max_latency=max_latency,
        p50=p50,
        p95=p95,
        p99=p99,
        errors=error_counter,
    )

    print_scenario_result(scenario_result)
    return scenario_result


# ==============================================================================
# REPORTING
# ==============================================================================


def print_scenario_result(result: ScenarioResult) -> None:
    """Prints a complete scenario benchmark report."""
    print("\n" + "-" * 79)
    print(f"Total Requests Processed : {result.total_requests}")
    print(f"Successful Requests      : {result.successful_requests}")
    print(f"Failed Requests          : {result.failed_requests}")
    print(f"Success Rate             : {result.success_rate:.2f}%")
    print(
        f"Wall Clock Duration      : {result.wall_clock_duration:.3f} seconds"
    )
    print("-" * 79)
    print(f"System Throughput        : {result.throughput:.2f} req/sec")
    print(f"Average Client Latency   : {result.average_latency:.2f} ms")
    print(f"Min Latency              : {result.min_latency:.2f} ms")
    print(f"Max Latency              : {result.max_latency:.2f} ms")
    print("-" * 79)
    print(f"P50 Latency              : {result.p50:.2f} ms")
    print(f"P95 Latency              : {result.p95:.2f} ms")
    print(f"P99 Latency              : {result.p99:.2f} ms")

    if result.errors:
        print("-" * 79)
        print("ERROR SUMMARY")
        for error_name, count in result.errors.most_common():
            print(f"{error_name:<30} : {count}")
    print("=" * 79)


def print_final_summary(results: List[ScenarioResult]) -> None:
    """Prints the final comparison table for all scenarios."""
    print("\n\n" + "#" * 100)
    print("                    FINAL CONCURRENCY BENCHMARK SUMMARY")
    print("#" * 100)
    print(
        f"{'Scenario':<38}{'Cameras':>9}{'Requests':>10}{'Success':>10}{'Rate':>10}{'FPS':>12}{'Avg(ms)':>12}{'P95(ms)':>12}{'P99(ms)':>12}"
    )
    print("-" * 125)

    for result in results:
        print(
            f"{result.name:<38}{result.cameras:>9}{result.total_requests:>10}{result.successful_requests:>10}{result.success_rate:>9.1f}%{result.throughput:>12.2f}{result.average_latency:>12.2f}{result.p95:>12.2f}{result.p99:>12.2f}"
        )

    print("#" * 100)


async def fetch_and_print_pipeline_telemetry():
    """Queries the metrics summary endpoint and displays the bottleneck breakdown."""
    print("\n\n" + "=" * 90)
    print("         PIPELINE STAGE BOTTLENECK ANALYSIS (IN-MEMORY TELEMETRY)")
    print("=" * 90)

    try:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            resp = await client.get(METRICS_ENDPOINT)
            if resp.status_code == 200:
                summary = resp.json()
                if not summary:
                    print("No camera telemetry metrics recorded in profiler yet.")
                    return

                print(
                    f"{'Camera ID':<12} | {'Q Wait':<8} | {'Sensor':<8} | {'Tracking':<9} | {'Fusion':<8} | {'Risk':<8} | {'Incident':<9} | {'Proc MS':<9} | {'E2E MS':<8}"
                )
                print("-" * 90)
                for cam_id, stats in summary.items():
                    print(
                        f"{cam_id:<12} | "
                        f"{stats.get('avg_queue_wait_ms', 0.0):>6.2f}ms | "
                        f"{stats.get('avg_sensor_ms', 0.0):>6.2f}ms | "
                        f"{stats.get('avg_tracking_ms', 0.0):>7.2f}ms | "
                        f"{stats.get('avg_fusion_ms', 0.0):>6.2f}ms | "
                        f"{stats.get('avg_risk_ms', 0.0):>6.2f}ms | "
                        f"{stats.get('avg_incident_ms', 0.0):>7.2f}ms | "
                        f"{stats.get('avg_processing_total_ms', 0.0):>7.2f}ms | "
                        f"{stats.get('avg_e2e_total_ms', 0.0):>6.2f}ms"
                    )
            else:
                print(f"Could not retrieve metrics: HTTP {resp.status_code}")
    except Exception as ex:
        print(f"Failed to fetch internal pipeline metrics: {ex}")
    print("=" * 90)


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================


async def main() -> None:
    print("\n" + "=" * 79)
    print(" FIRE INTELLIGENCE CORE")
    print(" PRODUCTION CONCURRENCY BENCHMARK SUITE")
    print("=" * 79)
    print(f"Target API: {BASE_URL}{ENDPOINT}")

    all_scenario_results: List[ScenarioResult] = []

    for scenario_index, (
        name,
        num_cameras,
        frames_per_camera,
    ) in enumerate(SCENARIOS):
        scenario_result = await run_scenario(
            name=name,
            num_cameras=num_cameras,
            frames_per_camera=frames_per_camera,
        )
        all_scenario_results.append(scenario_result)

        if scenario_index < len(SCENARIOS) - 1:
            print(f"\nCooling down for {SCENARIO_COOLDOWN_SECONDS:.1f} seconds...")
            await asyncio.sleep(SCENARIO_COOLDOWN_SECONDS)

    print_final_summary(all_scenario_results)
    await fetch_and_print_pipeline_telemetry()


if __name__ == "__main__":
    asyncio.run(main())