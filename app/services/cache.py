
import time
from collections import OrderedDict
from typing import Any, Tuple
from app.core.settings import settings

class LRUCacheTTL:
    def __init__(self, max_entries: int = settings.CACHE_MAX_ENTRIES, ttl: int = settings.CACHE_TTL_SECONDS):
        self.max_entries = max_entries
        self.ttl = ttl
        self.store: "OrderedDict[str, Tuple[float, Any]]" = OrderedDict()

    def _is_expired(self, ts: float) -> bool:
        return (time.time() - ts) > self.ttl

    def get(self, key: str):
        if key in self.store:
            ts, value = self.store.pop(key)
            if not self._is_expired(ts):
                # re-insert as most-recent
                self.store[key] = (ts, value)
                return value, "cache_fresh"
            else:
                # keep stale value around for SWR
                return value, "cache_stale"
        return None, "cache_miss"

    def set(self, key: str, value: Any):
        if key in self.store:
            self.store.pop(key)
        elif len(self.store) >= self.max_entries:
            self.store.popitem(last=False)  # evict LRU
        self.store[key] = (time.time(), value)

cache = LRUCacheTTL()
