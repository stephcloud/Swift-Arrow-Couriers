from collections import OrderedDict

CACHE_MAX_SIZE = 10
_cache = OrderedDict()


def get(key):
    """Return the cached value for a key, or None if it's not cached"""
    if key not in _cache:
        return None
    _cache.move_to_end(key)
    return _cache[key]


def set(key, value):
    """Store a value under a key. Evicts the oldest entry if the cache is full"""
    _cache[key] = value
    _cache.move_to_end(key)
    if len(_cache) > CACHE_MAX_SIZE:
        _cache.popitem(last=False)


def clear():
    """Wipe the entire cache. Called whenever data changes, so nothing stale is served"""
    _cache.clear()
