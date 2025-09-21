from collections import deque
from typing import Dict, Deque
from datetime import datetime, timezone

def utcnow():
    return datetime.now(tz=timezone.utc)

class RollingStats:
    def __init__(self, maxlen: int, min_samples: int = 10):
        self.buf: Dict[str, Deque[float]] = {}
        self.maxlen = maxlen
        self.min_samples = min_samples
    def add_key(self, k: str):
        from collections import deque
        if k not in self.buf:
            self.buf[k] = deque(maxlen=self.maxlen)
    def push(self, k: str, v: float):
        self.add_key(k); self.buf[k].append(float(v))
    def stats(self, k: str):
        import numpy as np
        arr = self.buf.get(k)
        if not arr or len(arr) < self.min_samples:
            return None
        a = np.array(arr, dtype=float)
        mu = float(a.mean()); sd = float(a.std() + 1e-6)
        last = float(a[-1])
        return {"mean": mu, "std": sd, "last": last, "z": abs((last-mu)/sd)}
