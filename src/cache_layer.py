"""Simple in-memory cache layer."""

# Module-level dictionary to act as cache
_cache: dict[str, str] = {}


def get_from_cache(key: str) -> str | None:
    """
    Retrieve a value from the cache.
    
    Args:
        key: The cache key to look up
        
    Returns:
        The cached value if found, None otherwise
    """
    value = _cache.get(key)
    if value is not None:
        print(f"[CACHE] Cache hit for key: {key}")
    else:
        print(f"[CACHE] Cache miss for key: {key}")
    return value


def set_in_cache(key: str, value: str) -> None:
    """
    Store a value in the cache.
    
    Args:
        key: The cache key
        value: The value to store
    """
    _cache[key] = value
    print(f"[CACHE] Stored value in cache for key: {key}")

