import time, threading, os
from typing import Dict
from fastapi import HTTPException

RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "120"))
_lock = threading.Lock()
_state: Dict[str, Dict] = {}

def _refill(key):
    now = time.time()
    s = _state.setdefault(key, {"tokens": RATE_LIMIT_PER_MIN, "last": now})
    elapsed = now - s["last"]
    refill_amount = (elapsed / 60.0) * RATE_LIMIT_PER_MIN
    if refill_amount > 0:
        s["tokens"] = min(RATE_LIMIT_PER_MIN, s["tokens"] + refill_amount)
        s["last"] = now
    return s

def check_rate_limit(api_key: str):
    with _lock:
        s = _refill(api_key)
        if s["tokens"] >= 1:
            s["tokens"] -= 1
            return
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
