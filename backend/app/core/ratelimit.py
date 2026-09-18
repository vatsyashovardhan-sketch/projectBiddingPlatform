# """Simple in-memory rate limiter for auth endpoints."""
# import time
# from fastapi import HTTPException

# _BUCKETS: dict[str, list[float]] = {}


# def rate_limit(key: str, max_hits: int = 20, window_s: int = 60):
#     if len(_BUCKETS) > 5000:  # bound memory under key flood
#         _BUCKETS.clear()
#     now = time.time()
#     hits = [t for t in _BUCKETS.get(key, []) if now - t < window_s]
#     if len(hits) >= max_hits:
#         raise HTTPException(429, "Too many requests, slow down")
#     hits.append(now)
#     _BUCKETS[key] = hits

"""Simple in-memory rate limiter for auth endpoints."""
import time
from fastapi import HTTPException

_BUCKETS: dict[str, list[float]] = {}


def rate_limit(key: str, max_hits: int = 20, window_s: int = 60):
    if len(_BUCKETS) > 5000:  # bound memory under key flood
        _BUCKETS.clear()
    now = time.time()
    hits = [t for t in _BUCKETS.get(key, []) if now - t < window_s]
    if len(hits) >= max_hits:
        raise HTTPException(429, "Too many requests, slow down")
    hits.append(now)
    _BUCKETS[key] = hits
