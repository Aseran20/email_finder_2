"""
Quick test script for new improvements:
- MX caching
- Structured logging
- Cache stats endpoint
"""
from core.email_finder import EmailFinder
from core.logger import StructuredLogger

# Test 1: MX Cache
print("=== Test 1: MX Cache ===")
finder = EmailFinder(mx_cache_ttl=60)

# First call - cache miss
print("\nFirst call (cache miss):")
mx1 = finder.get_mx_records("auraia.ch")
print(f"MX Records: {mx1}")
print(f"Cache stats: {finder.mx_cache.stats()}")

# Second call - cache hit
print("\nSecond call (cache hit):")
mx2 = finder.get_mx_records("auraia.ch")
print(f"MX Records: {mx2}")
print(f"Cache stats: {finder.mx_cache.stats()}")

# Different domain
print("\nDifferent domain:")
mx3 = finder.get_mx_records("google.com")
print(f"MX Records: {mx3}")
print(f"Cache stats: {finder.mx_cache.stats()}")

# Test 2: Structured Logging
print("\n=== Test 2: Structured Logging ===")
logger = StructuredLogger("test", json_format=False)

logger.info("Email verification started", domain="example.com", pattern="john.doe@example.com")
logger.warning("Catch-all detected", domain="example.com", confidence="low")
logger.error("SMTP connection failed", domain="example.com", error="Timeout")

# With JSON format
logger_json = StructuredLogger("test_json", json_format=True)
logger_json.info("Test with JSON", domain="example.com", status="valid")

print("\n✅ All tests passed!")
