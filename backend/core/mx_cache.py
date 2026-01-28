"""
MX Records caching layer to reduce DNS lookups.
Simple in-memory cache with TTL (Time To Live).
"""
import time
from typing import List, Optional, Dict, Tuple


class MXCache:
    """
    Simple in-memory cache for MX records with TTL.

    Usage:
        cache = MXCache(ttl=3600)  # 1 hour TTL
        records = cache.get("example.com")
        if records is None:
            records = fetch_from_dns("example.com")
            cache.set("example.com", records)
    """

    def __init__(self, ttl: int = 3600):
        """
        Initialize cache.

        Args:
            ttl: Time to live in seconds (default: 1 hour)
        """
        self.ttl = ttl
        self._cache: Dict[str, Tuple[List[str], float]] = {}
        self._hits = 0
        self._misses = 0

    def get(self, domain: str) -> Optional[List[str]]:
        """
        Get MX records from cache if available and not expired.

        Args:
            domain: Domain name

        Returns:
            List of MX records or None if not in cache or expired
        """
        domain = domain.lower().strip()

        if domain not in self._cache:
            self._misses += 1
            return None

        records, timestamp = self._cache[domain]
        age = time.time() - timestamp

        if age > self.ttl:
            # Expired - remove from cache
            del self._cache[domain]
            self._misses += 1
            return None

        self._hits += 1
        return records

    def set(self, domain: str, records: List[str]) -> None:
        """
        Store MX records in cache.

        Args:
            domain: Domain name
            records: List of MX server hostnames
        """
        domain = domain.lower().strip()
        self._cache[domain] = (records, time.time())

    def clear(self) -> None:
        """Clear all cached records."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dict with hits, misses, hit_rate, and size
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "cached_domains": len(self._cache),
            "ttl_seconds": self.ttl
        }

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        now = time.time()
        expired = [
            domain
            for domain, (_, timestamp) in self._cache.items()
            if now - timestamp > self.ttl
        ]

        for domain in expired:
            del self._cache[domain]

        return len(expired)
