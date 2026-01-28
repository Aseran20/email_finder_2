import smtplib
import dns.resolver
import re
import time
import os
import random
import string
import socket
from typing import List, Tuple
from dotenv import load_dotenv
from unidecode import unidecode
from models import EmailFinderResponse
from core.mx_cache import MXCache
from core.logger import StructuredLogger
from config import config

load_dotenv()
logger = StructuredLogger("email_finder", json_format=False)

class EmailFinder:
    def __init__(self, mx_cache_ttl: int = None):
        """
        Initialize EmailFinder with optional MX cache.

        Args:
            mx_cache_ttl: MX cache TTL in seconds (default: from config)
        """
        self.smtp_hostname = config.SMTP_HOSTNAME
        self.smtp_from_email = config.SMTP_FROM_EMAIL
        self.mx_cache = MXCache(ttl=mx_cache_ttl or config.MX_CACHE_TTL)

    def normalize_domain(self, domain: str) -> str:
        domain = domain.lower().strip()
        if "://" in domain:
            domain = domain.split("://")[1].split("/")[0]
        return domain

    def normalize_name(self, full_name: str) -> Tuple[List[str], List[str]]:
        """
        Normalize name and return variants to handle edge cases.
        Returns: (first_name_variants, last_name_variants)
        
        Examples:
        - "Mads-Håkon Mørck" -> (['mads-hakon', 'madshakon'], ['morck'])
        - "André Müller" -> (['andre'], ['muller'])
        """
        parts = full_name.strip().split()
        first = parts[0] if parts else ""
        last = parts[-1] if len(parts) > 1 else ""
        
        # Normalize accents using unidecode (Mørck -> Morck)
        first_normalized = unidecode(first).lower()
        last_normalized = unidecode(last).lower()
        
        # Remove non-alphanumeric except hyphens
        first_cleaned = re.sub(r'[^a-z-]', '', first_normalized)
        last_cleaned = re.sub(r'[^a-z-]', '', last_normalized)
        
        # Generate variants for hyphenated names
        first_variants = [first_cleaned]
        if '-' in first_cleaned:
            # Add version without hyphens
            first_variants.append(first_cleaned.replace('-', ''))
        
        last_variants = [last_cleaned]
        if '-' in last_cleaned:
            last_variants.append(last_cleaned.replace('-', ''))
        
        return first_variants, last_variants

    def generate_patterns(self, first_variants: List[str], last_variants: List[str], domain: str) -> List[str]:
        """
        Generate email patterns with enhanced coverage.
        Handles name variants (hyphenated, accented) and missing permutations.
        """
        patterns = []
        
        # Generate patterns for all variant combinations
        for first in first_variants:
            for last in last_variants:
                if first and last:
                    # Original patterns (priority order)
                    patterns.append(f"{first}.{last}@{domain}")        # john.doe@
                    patterns.append(f"{first}{last}@{domain}")          # johndoe@
                    patterns.append(f"{first[0]}.{last}@{domain}")     # j.doe@
                    patterns.append(f"{first}.{last[0]}@{domain}")     # john.d@
                    patterns.append(f"{first}@{domain}")                # john@
                    patterns.append(f"{last}@{domain}")                 # doe@
                    
                    # NEW: Missing permutations (Edge Case #2)
                    patterns.append(f"{first[0]}{last}@{domain}")      # jdoe@
                    patterns.append(f"{last}{first[0]}@{domain}")      # doej@
                    patterns.append(f"{first}{last[0]}@{domain}")      # johnd@
                    
                elif first:
                    patterns.append(f"{first}@{domain}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_patterns = []
        for p in patterns:
            if p not in seen:
                seen.add(p)
                unique_patterns.append(p)
        
        return unique_patterns

    def get_mx_records(self, domain: str) -> List[str]:
        """
        Get MX records for a domain with caching.

        Args:
            domain: Domain name

        Returns:
            List of MX hostnames, sorted by preference
        """
        # Check cache first
        cached = self.mx_cache.get(domain)
        if cached is not None:
            return cached

        # Cache miss - query DNS
        try:
            records = dns.resolver.resolve(domain, 'MX')
            sorted_records = sorted(records, key=lambda r: r.preference)
            mx_list = [str(r.exchange).rstrip('.') for r in sorted_records]

            # Store in cache
            self.mx_cache.set(domain, mx_list)
            return mx_list

        except Exception as e:
            logger.error("DNS query failed", domain=domain, error=str(e))
            return []

    def verify_email(self, email: str, mx_host: str) -> Tuple[bool, str, int]:
        """
        Direct SMTP verification without proxy.
        Returns (is_valid, log_message, code)
        """
        try:
            server = smtplib.SMTP(timeout=10)
            server.set_debuglevel(0)
            
            server.connect(mx_host, 25)
            server.ehlo(self.smtp_hostname)
            server.mail(self.smtp_from_email)
            
            code, message = server.rcpt(email)
            server.quit()
            
            log = f"{mx_host}: {code} {message.decode('ascii', errors='ignore')}"
            
            # 250 = OK, 251 = User not local (will forward)
            if code == 250 or code == 251:
                return True, log, code
            return False, log, code
            
        except socket.timeout:
            return False, f"{mx_host}: Timeout (>10s)", 0
        except ConnectionRefusedError:
            return False, f"{mx_host}: Connection refused", 0
        except Exception as e:
            return False, f"{mx_host}: Error {str(e)}", 0

    def verify_email_with_retry(self, email: str, mx_host: str) -> Tuple[bool, str, int]:
        """
        Verify email with retry logic and exponential backoff.

        Retries on transient errors (timeout, connection issues) but NOT on
        permanent failures like 550 (user not found).

        Retry strategy: 1s → 2s → 4s (max 3 attempts total)

        Args:
            email: Email address to verify
            mx_host: MX server hostname

        Returns:
            Tuple of (is_valid, log_message, smtp_code)
        """
        last_error = None

        for attempt in range(config.SMTP_MAX_RETRIES):
            is_valid, log, code = self.verify_email(email, mx_host)

            # Success - return immediately
            if is_valid:
                if attempt > 0:
                    log += f" (succeeded after {attempt + 1} attempts)"
                return is_valid, log, code

            # Check if error is transient and should be retried
            should_retry = config.should_retry_error(log)

            if not should_retry:
                # Permanent error (like 550 user not found) - don't retry
                logger.debug(f"Permanent error, not retrying: {log}")
                return is_valid, log, code

            # Transient error - retry
            last_error = (is_valid, log, code)

            if attempt < config.SMTP_MAX_RETRIES - 1:
                delay = config.get_retry_delay(attempt)
                logger.info(f"Transient error, retrying in {delay}s (attempt {attempt + 1}/{config.SMTP_MAX_RETRIES}): {log}")
                time.sleep(delay)

        # All retries exhausted
        is_valid, log, code = last_error
        log += f" (failed after {config.SMTP_MAX_RETRIES} attempts)"
        return is_valid, log, code

    def generate_random_email(self, domain: str) -> str:
        """Generate a random email for catch-all detection."""
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
        return f"chk_{random_string}@{domain}"

    def find_email(self, domain: str, full_name: str) -> EmailFinderResponse:
        domain = self.normalize_domain(domain)
        first_variants, last_variants = self.normalize_name(full_name)
        patterns = self.generate_patterns(first_variants, last_variants, domain)
        mx_records = self.get_mx_records(domain)

        response = EmailFinderResponse(
            status="unknown",
            patternsTested=patterns,
            mxRecords=mx_records
        )

        if not mx_records:
            response.status = "error"
            response.errorMessage = "No MX records found"
            return response

        # Try up to MAX_MX_SERVERS MX records with fallback
        mx_hosts_to_try = mx_records[:config.MAX_MX_SERVERS]
        mx_host = None
        connection_errors = []

        # STEP 1: Catch-All Check (CRUCIAL - Must be first)
        catch_all_email = self.generate_random_email(domain)

        for idx, mx in enumerate(mx_hosts_to_try):
            is_valid, log, code = self.verify_email_with_retry(catch_all_email, mx)
            response.smtpLogs.append(f"Catch-all check ({catch_all_email}) on MX{idx + 1} ({mx}): {log}")

            # Check if it's a connection error (should try next MX)
            is_connection_error = any(err in log.lower() for err in [
                "timeout", "connection refused", "connection reset", "connection closed"
            ])

            if is_connection_error:
                connection_errors.append(f"MX{idx + 1} ({mx}): {log}")
                continue  # Try next MX

            # Got a response (valid or invalid) - use this MX
            mx_host = mx

            if is_valid:
                # Server accepts all emails (Catch-All)
                response.catchAll = True
                response.status = "catch_all"
                response.debugInfo = f"MX: {mx_host} | Catch-all detected (low confidence)"
                # Return best guess (first.last)
                if patterns:
                    response.email = patterns[0]
                return response

            # Catch-all rejected - proceed to pattern testing with this MX
            break

        # If all MX servers had connection errors
        if mx_host is None:
            response.status = "error"
            response.errorMessage = f"All MX servers unreachable: {'; '.join(connection_errors)}"
            return response

        # STEP 2: Pattern Testing (Only if server is "Honest" - rejected catch-all)
        for i, pattern in enumerate(patterns):
            # Politeness: 1s delay between checks
            if i > 0:
                time.sleep(1)

            is_valid, log, code = self.verify_email_with_retry(pattern, mx_host)
            response.smtpLogs.append(log)

            if is_valid:
                response.status = "valid"
                response.email = pattern
                response.debugInfo = f"MX: {mx_host} | Match: {pattern} (high confidence)"
                return response

        # No match found
        response.status = "not_found"
        response.debugInfo = f"MX: {mx_host} | {len(patterns)} patterns tested | No match"
        return response

    def check_email(self, email: str, full_name: str = None) -> EmailFinderResponse:
        """
        Check if a specific email address is valid.
        If invalid and fullName is provided, fallback to domain search.

        Args:
            email: Email address to verify
            full_name: Optional full name for fallback search

        Returns:
            EmailFinderResponse with validation result
        """
        # Extract domain from email
        if '@' not in email:
            response = EmailFinderResponse(status="error", errorMessage="Invalid email format")
            return response

        domain = email.split('@')[1]
        domain = self.normalize_domain(domain)

        # Get MX records
        mx_records = self.get_mx_records(domain)
        response = EmailFinderResponse(
            status="unknown",
            patternsTested=[email],
            mxRecords=mx_records
        )

        if not mx_records:
            response.status = "error"
            response.errorMessage = "No MX records found"
            return response

        # Try up to MAX_MX_SERVERS MX records with fallback
        mx_hosts_to_try = mx_records[:config.MAX_MX_SERVERS]
        mx_host = None

        for idx, mx in enumerate(mx_hosts_to_try):
            is_valid, log, code = self.verify_email_with_retry(email, mx)
            response.smtpLogs.append(f"Direct check ({email}) on MX{idx + 1} ({mx}): {log}")

            # Check if it's a connection error (should try next MX)
            is_connection_error = any(err in log.lower() for err in [
                "timeout", "connection refused", "connection reset", "connection closed"
            ])

            if is_connection_error:
                continue  # Try next MX

            # Got a response (valid or invalid) - use this result
            mx_host = mx

            if is_valid:
                response.status = "valid"
                response.email = email
                response.debugInfo = f"MX: {mx_host} | Email verified directly (high confidence)"
                return response

            # Email is invalid - break to proceed to fallback
            break

        # If all MX servers had connection errors
        if mx_host is None:
            response.status = "error"
            response.errorMessage = "All MX servers unreachable"
            return response

        # Email is invalid
        # If fullName provided, try fallback domain search
        if full_name:
            logger.info(f"Email {email} invalid, attempting fallback search with name: {full_name}")
            response.smtpLogs.append(f"Fallback: Trying domain search with name '{full_name}'")

            fallback_response = self.find_email(domain, full_name)

            # Merge logs and info
            response.smtpLogs.extend(fallback_response.smtpLogs)
            response.patternsTested.extend(fallback_response.patternsTested)
            response.catchAll = fallback_response.catchAll

            if fallback_response.status == "valid":
                response.status = "valid"
                response.email = fallback_response.email
                response.debugInfo = f"Fallback success: Found {fallback_response.email}"
            elif fallback_response.status == "catch_all":
                response.status = "catch_all"
                response.email = fallback_response.email
                response.debugInfo = fallback_response.debugInfo + " (via fallback)"
            else:
                response.status = "not_found"
                response.debugInfo = f"Email {email} invalid, fallback search found no alternatives"
        else:
            response.status = "not_found"
            response.debugInfo = f"MX: {mx_host} | Email {email} does not exist"

        return response
