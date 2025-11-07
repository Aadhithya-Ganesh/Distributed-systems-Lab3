import os
import pybreaker
import requests
import logging
from flask import jsonify, Blueprint, request

BACKEND_BASE = "http://backend:5000"
circuitBreaker_bp = Blueprint("circuit", __name__)

os.makedirs('/app/logs', exist_ok=True)
cb_logger = logging.getLogger("client.circuit")
cb_logger.setLevel(logging.INFO)
if not cb_logger.handlers:
    fh = logging.FileHandler('/app/logs/circuit_breaker.log', mode='a')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    cb_logger.addHandler(fh)
cb_logger.propagate = True

class SimpleCircuitBreakerListener(pybreaker.CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        cb_logger.warning(f"CIRCUIT STATE CHANGE: {old_state.name} -> {new_state.name} | CB_STATE={new_state.name}")
    def failure(self, cb, exc):
        cb_logger.error(f"CIRCUIT FAILURE: {type(exc).__name__}: {exc}")
    def success(self, cb):
        cb_logger.info("CIRCUIT SUCCESS")

breaker = pybreaker.CircuitBreaker(
    fail_max=2,
    reset_timeout=10,
    success_threshold=2,
    listeners=[SimpleCircuitBreakerListener()]
)

# ---- helper that MAKES 5xx COUNT AS FAILURE ----
def _get_checked(url: str, timeout: float):
    resp = requests.get(url, timeout=timeout)
    if resp.status_code >= 500:
        cb_logger.error(f"Backend returned {resp.status_code} (treated as failure)")
        raise requests.exceptions.HTTPError(f"HTTP {resp.status_code}", response=resp)
    return resp

@circuitBreaker_bp.route("/circuit", methods=["GET"])
def circuit_endpoint():
    mode = (request.args.get("mode") or "").lower()
    path = "/chaos" if mode == "chaos" else "/circuit"
    url = f"{BACKEND_BASE}{path}"

    cb_logger.info(f"CIRCUIT ENDPOINT CALLED | state={breaker.current_state} | mode={mode or 'default'} | url={url}")

    try:
        # Call THROUGH the breaker, using the wrapper that raises on 5xx
        resp = breaker.call(_get_checked, url, 2)  # (url, timeout)
        cb_logger.info(f"CIRCUIT CALL SUCCESS | state={breaker.current_state} | status={resp.status_code}")
        return jsonify({
            "status": "success",
            "breaker_state": str(breaker.current_state),
            "backend_path": path,
            "response": resp.json()
        }), 200

    except pybreaker.CircuitBreakerError:
        cb_logger.error(f"CIRCUIT BREAKER OPEN - FAST FAIL | CB_FAST_FAIL=1 | state={breaker.current_state}")
        return jsonify({
            "error": "Circuit breaker open",
            "breaker_state": str(breaker.current_state),
            "backend_path": path
        }), 503

    except Exception as e:
        # Any network error or raised HTTPError reaches here and is counted as a failure
        cb_logger.error(f"CIRCUIT CALL FAILED | state={breaker.current_state} | err={type(e).__name__}: {e}")
        return jsonify({
            "error": str(e),
            "breaker_state": str(breaker.current_state),
            "backend_path": path
        }), 500
