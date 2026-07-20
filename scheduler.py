import subprocess
import time
import sys
from datetime import datetime

POLL_INTERVAL_SECONDS = 3 * 60  # 3 min

def run_step(script_path, label):
    print(f"[{datetime.now().isoformat()}] Running {label}...")
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[{datetime.now().isoformat()}] {label} FAILED:")
        print(result.stderr)
        return False
    print(result.stdout.strip())
    return True

if __name__ == "__main__":
    print(f"Scheduler started. Polling every {POLL_INTERVAL_SECONDS // 60} min. Ctrl+C to stop.")
    while True:
        fetch_ok = run_step("ingestion/fetch_gtfs_realtime.py", "fetch")
        if fetch_ok:
            run_step("etl/load_facts.py", "load")
        else:
            print("Skipping load — fetch failed.")

        print(f"Sleeping {POLL_INTERVAL_SECONDS}s...\n")
        time.sleep(POLL_INTERVAL_SECONDS)