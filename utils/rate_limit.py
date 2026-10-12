import time
from threading import Lock


class RateLimiter:
    """In-memory window limiter keyed by an arbitrary string."""

    def __init__(self):
        self._hits = {}
        self._lock = Lock()

    def allow(self, key, limit, window_seconds):
        """Record an attempt and return False once the window is full."""
        now = time.monotonic()
        with self._lock:
            recent = [stamp for stamp in self._hits.get(key, ()) if now - stamp < window_seconds]
            if len(recent) >= limit:
                self._hits[key] = recent
                return False
            recent.append(now)
            self._hits[key] = recent
            if len(self._hits) > 10000:
                self._hits = {
                    stored_key: stamps for stored_key, stamps in self._hits.items() if stamps
                }
            return True

    def reset(self):
        with self._lock:
            self._hits.clear()


rate_limiter = RateLimiter()
