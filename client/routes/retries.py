# routes/retries.py
import os
import requests
import time
import logging
from flask import jsonify, Blueprint, request
from tenacity import retry, stop_after_attempt, wait_exponential, wait_random

retries_bp = Blueprint("retries", __name__)

# Ensure logs dir and a dedicated logger
os.makedirs('/app/logs', exist_ok=True)
r_logger = logging.getLogger("client.retries")
r_logger.setLevel(logging.INFO)
if not r_logger.handlers:
    fh = logging.FileHandler('/app/logs/retries.log', mode='a', encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    r_logger.addHandler(fh)
r_logger.propagate = True  # also goes to app.log / stdout

BACKEND_BASE = "http://backend:5000"

def call_with_retry(url, delays_out):
    """
    5 attempts total. Exponential backoff with jitter:
    waits ~= 1s, 2s, 4s, 8s (capped at 10s), each + random [0, 2]s jitter.
    We capture the computed 'next sleep' before each retry and append to delays_out.
    """
    def _before_sleep(retry_state):
        nxt = getattr(getattr(retry_state, "next_action", None), "sleep", None)
        if nxt is not None:
            # record the next wait (seconds, float)
            delays_out.append(round(float(nxt), 2))
            r_logger.warning(f"RETRY WAIT (next): {float(nxt):.2f}s")

    # Tenacity trick: exponential backoff PLUS jitter by adding waits
    wait_policy = wait_exponential(multiplier=1, min=1, max=10) + wait_random(0, 2)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_policy,
        before_sleep=_before_sleep
    )
    def _call():
        r_logger.info("RETRY: Attempting backend call")
        resp = requests.get(url, timeout=2)
        r_logger.info(f"RETRY: Backend responded with {resp.status_code}")
        resp.raise_for_status()
        return resp

    return _call()

@retries_bp.route("/retries", methods=["GET"])
def retries_endpoint():
    mode = (request.args.get("mode") or "").lower()
    path = "/chaos" if mode == "chaos" else "/retries"
    url = f"{BACKEND_BASE}{path}"
    r_logger.info(f"RETRIES ENDPOINT CALLED | mode={mode or 'default'} | url={url}")

    delays = []
    start = time.time()
    try:
        resp = call_with_retry(url, delays)
        elapsed = time.time() - start
        r_logger.info(f"RETRY SUCCESS: Took {elapsed:.2f}s | delays={delays}")
        return jsonify({
            "status": "success",
            "time_taken": round(elapsed, 2),
            "delays": delays,   # show the jittered waits that were scheduled
            "response": resp.json()
        }), 200

    except Exception as e:
        elapsed = time.time() - start
        r_logger.error(f"RETRY FAILED: Took {elapsed:.2f}s - {e} | delays={delays}")
        return jsonify({
            "status": "failed",
            "error": str(e),
            "time_taken": round(elapsed, 2),
            "delays": delays    # show the jittered waits that were scheduled
        }), 500
