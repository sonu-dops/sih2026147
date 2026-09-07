"""Caching subsystem for expensive DSP artifacts."""

import hashlib
from pathlib import Path
from typing import Any, Dict, Optional


class DSPCache:
    """In-memory and file-backed cache keyed by signal content hash and parameters."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._memory_cache: Dict[str, Any] = {}

    @staticmethod
    def compute_key(samples_bytes: bytes, params_str: str) -> str:
        h = hashlib.sha256()
        # Hash first 64KB of samples for rapid fingerprinting + length
        h.update(samples_bytes[:65536])
        h.update(str(len(samples_bytes)).encode("utf-8"))
        h.update(params_str.encode("utf-8"))
        return h.hexdigest()

    def get(self, key: str) -> Optional[Any]:
        return self._memory_cache.get(key)

    def put(self, key: str, value: Any) -> None:
        self._memory_cache[key] = value

    def clear(self) -> None:
        self._memory_cache.clear()


# Global cache instance
cache = DSPCache()
