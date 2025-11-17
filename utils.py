import uuid
import time
from datetime import datetime

def make_run_id(prefix="run"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def now_ts():
    return int(time.time())

def now_iso():
    return datetime.utcnow().isoformat() + "Z"
