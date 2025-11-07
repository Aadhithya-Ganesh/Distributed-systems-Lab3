import argparse
import os
import time
from datetime import datetime
import requests

CLIENT_URL = "http://localhost:80"

def log_write(path, line):
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def circuit_task(log_file, count):
    print(f"[load_tester] CIRCUIT: {count} calls -> {log_file}")
    for i in range(count):
        start = time.time()
        status = None
        try:
            resp = requests.get(f"{CLIENT_URL}/circuit?mode=chaos", timeout=5)
            status = resp.status_code
            dur = round(time.time() - start, 2)

            if status == 200:
                log_write(log_file, f"{status} OK in {dur}s")
                time.sleep(0.3)
            elif status == 503:
                log_write(log_file, f"{status} CIRCUIT OPEN in {dur}s")
                time.sleep(0.5)
            else:
                log_write(log_file, f"{status} FAILURE in {dur}s")
                time.sleep(0.8)

        except Exception:
            dur = round(time.time() - start, 2)
            log_write(log_file, f"NO RESPONSE / TIMEOUT in {dur}s")
            time.sleep(1.0)

def retries_task(log_file):
    print(f"[load_tester] RETRIES: single call -> {log_file}")
    start = time.time()
    try:
        # Enough room for 5 attempts + waits + HTTP timeouts
        resp = requests.get(f"{CLIENT_URL}/retries?mode=chaos", timeout=60)
        dur = round(time.time() - start, 2)

        delays_txt = ""
        try:
            data = resp.json()
            if isinstance(data, dict) and "delays" in data and data["delays"]:
                delays_txt = f" (delays={data['delays']})"
        except Exception:
            pass

        if resp.status_code == 200:
            log_write(log_file, f"200 OK in {dur}s{delays_txt}")
        else:
            log_write(log_file, f"{resp.status_code} FAILURE in {dur}s{delays_txt}")

    except Exception:
        dur = round(time.time() - start, 2)
        log_write(log_file, f"NO RESPONSE / TIMEOUT in {dur}s")

def main():
    parser = argparse.ArgumentParser(description="Targeted load for CB and Retries (mode=chaos)")
    parser.add_argument("phase", help="Phase label, e.g., initial | during-chaos | final")
    parser.add_argument("--task", choices=["circuit", "retries"], required=True, help="What to run")
    parser.add_argument("--count", type=int, default=10, help="Number of calls for circuit task (default 10)")
    args = parser.parse_args()

    base_dir = os.path.abspath(os.getcwd())
    out_dir = os.path.join(base_dir, "load-logs")
    os.makedirs(out_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file = os.path.join(out_dir, f"{args.phase}_{args.task}_{ts}.log")

    print(f"[load_tester] CWD: {base_dir}")
    print(f"[load_tester] Phase: {args.phase} | Task: {args.task}")
    print(f"[load_tester] Writing: {log_file}")

    if args.task == "circuit":
        circuit_task(log_file, args.count)
    else:
        retries_task(log_file)

    print("[load_tester] Done.")

if __name__ == "__main__":
    main()
