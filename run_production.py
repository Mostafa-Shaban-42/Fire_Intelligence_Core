import multiprocessing
import os
import uvicorn

if __name__ == "__main__":
    # Optimal workers for high-concurrency ingestion
    cpu_count = multiprocessing.cpu_count()
    workers = 2 if os.name == "nt" else min(cpu_count, 4)
    
    print("=========================================================")
    print(" STARTING FIRE INTELLIGENCE CORE (PERMANENT PRODUCTION HARDENED)")
    print(f" Workers: {workers} | CPU Cores: {cpu_count}")
    print(" Engine: Uvicorn + Asyncio/uvloop + ThreadPool CPU Isolation")
    print(" Architecture: Zero-Lock Shared Memory Queue + Async ACK Ingestion")
    print("=========================================================")
    
    # Check if uvloop is supported on host OS (Linux/MacOS) or fallback cleanly on Windows
    loop_choice = "uvloop" if os.name != "nt" else "asyncio"

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        workers=workers,
        log_level="warning",
        access_log=False,  # Disable access logging for ultra latency under 50+ camera streams
        loop=loop_choice,
        http="httptools",
        backlog=16384,             # Extended OS-level socket backlog for 50+ camera bursts
        limit_concurrency=20000,   # Zero socket rejection
        timeout_keep_alive=65,
    )