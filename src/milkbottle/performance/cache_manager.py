"""Intelligent caching system for MilkBottle."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("milkbottle.cache")


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    value: Any
    timestamp: float
    access_count: int = 0
    size: int = 0
    tags: list[str] = field(default_factory=list)


class CacheManager:
    """Intelligent caching system with TTL and LRU eviction."""

    def __init__(
        self,
        max_size: int = 1000,
        ttl: int = 3600,
        persistent_cache: bool = False,
        cache_dir: Optional[Path] = None,
    ):
        """Initialize cache manager.

        Args:
            max_size: Maximum number of cache entries
            ttl: Time to live in seconds
            persistent_cache: Whether to persist cache to disk
            cache_dir: Directory for persistent cache
        """
        self.max_size = max_size
        self.ttl = ttl
        self.persistent_cache = persistent_cache
        self.cache_dir = cache_dir or Path.home() / ".milkbottle" / "cache"

        # In-memory cache using OrderedDict for LRU
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0,
            "created": time.time(),
        }

        # Load persistent cache if enabled
        if self.persistent_cache:
            self._load_persistent_cache()

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from function arguments."""
        # Create a hash of the arguments
        key_data = {"args": args, "kwargs": sorted(kwargs.items())}
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        if key in self.cache:
            entry = self.cache[key]

            # Check if entry has expired
            if time.time() - entry.timestamp > self.ttl:
                self._remove_entry(key)
                self.stats["misses"] += 1
                return default

            # Update access count and move to end (LRU)
            entry.access_count += 1
            self.cache.move_to_end(key)
            self.stats["hits"] += 1
            return entry.value

        self.stats["misses"] += 1
        return default

    def set(self, key: str, value: Any, tags: Optional[list[str]] = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            tags: Optional tags for the entry
        """
        # Remove expired entries first
        self._cleanup_expired()

        # Check if we need to evict entries
        if len(self.cache) >= self.max_size:
            self._evict_lru()

        # Create cache entry
        entry = CacheEntry(
            value=value,
            timestamp=time.time(),
            access_count=1,
            size=self._estimate_size(value),
            tags=tags or [],
        )

        # Add to cache
        self.cache[key] = entry
        self.stats["size"] += entry.size

        # Move to end (most recently used)
        self.cache.move_to_end(key)

    def delete(self, key: str) -> bool:
        """Delete entry from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was found and deleted
        """
        if key in self.cache:
            self._remove_entry(key)
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.stats["size"] = 0
        logger.info("Cache cleared")

    def clear_by_tags(self, tags: list[str]) -> int:
        """Clear cache entries by tags.

        Args:
            tags: Tags to match for deletion

        Returns:
            Number of entries deleted
        """
        deleted_count = 0
        keys_to_delete = []

        keys_to_delete.extend(
            key
            for key, entry in self.cache.items()
            if any(tag in entry.tags for tag in tags)
        )
        for key in keys_to_delete:
            self._remove_entry(key)
            deleted_count += 1

        logger.info(f"Cleared {deleted_count} cache entries by tags: {tags}")
        return deleted_count

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        hit_rate = 0
        if self.stats["hits"] + self.stats["misses"] > 0:
            hit_rate = self.stats["hits"] / (self.stats["hits"] + self.stats["misses"])

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": hit_rate,
            "evictions": self.stats["evictions"],
            "size": self.stats["size"],
            "entries": len(self.cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
            "created": self.stats["created"],
            "uptime": time.time() - self.stats["created"],
        }

    def optimize(self) -> Dict[str, Any]:
        """Optimize cache performance.

        Returns:
            Optimization results
        """
        # Clean up expired entries
        expired_count = self._cleanup_expired()
        optimizations = {"expired_cleaned": expired_count}
        # Analyze cache efficiency
        if len(self.cache) > 0:
            avg_access_count = sum(
                entry.access_count for entry in self.cache.values()
            ) / len(self.cache)
            optimizations["avg_access_count"] = avg_access_count

            # Suggest size optimization
            if avg_access_count < 2:
                optimizations["suggestion"] = (
                    "Consider reducing cache size - low access frequency"
                )

        # Persist cache if enabled
        if self.persistent_cache:
            self._save_persistent_cache()
            optimizations["persisted"] = True

        logger.info(f"Cache optimization completed: {optimizations}")
        return optimizations

    def _remove_entry(self, key: str) -> None:
        """Remove entry from cache."""
        if key in self.cache:
            entry = self.cache[key]
            self.stats["size"] -= entry.size
            del self.cache[key]

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if self.cache:
            # Remove oldest entry (first in OrderedDict)
            oldest_key = next(iter(self.cache))
            self._remove_entry(oldest_key)
            self.stats["evictions"] += 1

    def _cleanup_expired(self) -> int:
        """Remove expired entries from cache.

        Returns:
            Number of expired entries removed
        """
        current_time = time.time()

        expired_keys = [
            key
            for key, entry in self.cache.items()
            if current_time - entry.timestamp > self.ttl
        ]
        for key in expired_keys:
            self._remove_entry(key)

        return len(expired_keys)

    def _estimate_size(self, value: Any) -> int:
        """Estimate size of cached value in bytes."""
        try:
            return len(json.dumps(value, default=str))
        except (TypeError, ValueError):
            return 1024  # Default size estimate

    def _save_persistent_cache(self) -> None:
        """Save cache to persistent storage."""
        if not self.persistent_cache:
            return

        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = self.cache_dir / "cache.json"

            cache_data = {
                key: {
                    "value": entry.value,
                    "timestamp": entry.timestamp,
                    "access_count": entry.access_count,
                    "tags": entry.tags,
                }
                for key, entry in self.cache.items()
            }
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)

        except Exception as e:
            logger.error(f"Failed to save persistent cache: {e}")

    def _load_persistent_cache(self) -> None:
        """Load cache from persistent storage."""
        if not self.persistent_cache:
            return

        try:
            cache_file = self.cache_dir / "cache.json"
            if cache_file.exists():
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)

                # Load entries, filtering expired ones
                current_time = time.time()
                for key, data in cache_data.items():
                    if current_time - data["timestamp"] <= self.ttl:
                        entry = CacheEntry(
                            value=data["value"],
                            timestamp=data["timestamp"],
                            access_count=data["access_count"],
                            tags=data.get("tags", []),
                        )
                        self.cache[key] = entry
                        self.stats["size"] += entry.size

                logger.info(f"Loaded {len(self.cache)} entries from persistent cache")

        except Exception as e:
            logger.error(f"Failed to load persistent cache: {e}")


def cache_result(ttl: int = 3600, key_prefix: str = ""):
    """Decorator to cache function results.

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        cache = CacheManager(ttl=ttl)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{cache._generate_key(*args, **kwargs)}"

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        return wrapper

    return decorator


def cache_result_with_tags(ttl: int = 3600, tags: Optional[list[str]] = None):
    """Decorator to cache function results with tags.

    Args:
        ttl: Time to live in seconds
        tags: Tags for cache entries

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        cache = CacheManager(ttl=ttl)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache._generate_key(*args, **kwargs)

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, tags=tags)
            return result

        return wrapper

    return decorator
