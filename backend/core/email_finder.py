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
from models import EmailFinderResponse

load_dotenv()

class EmailFinder:
    def __init__(self):
        self.smtp_hostname = os.getenv("SMTP_HOSTNAME", "vps.auraia.ch")
        self.smtp_from_email = os.getenv("SMTP_FROM_EMAIL", "verify@vps.auraia.ch")

    def normalize_domain(self, domain: str) -> str:
        domain = domain.lower().strip()
        if "://" in domain:
            domain = domain.split("://")[1].split("/")[0]
        return domain

    def normalize_name(self, full_name: str) -> Tuple[str, str]:
        parts = full_name.strip().split()
        first = parts[0]
        last = parts[-1] if len(parts) > 1 else ""
        
        # Simple normalization
        first = re.sub(r'[^a-zA-Z]', '', first).lower()
        last = re.sub(r'[^a-zA-Z]', '', last).lower()
        
        return first, last

    def generate_patterns(self, first: str, last: str, domain: str) -> List[str]:
        """Generate email patterns in priority order as specified."""
        patterns = []
        if first and last:
            # Exact order as requested: [first.last, firstlast, f.last, first.l, first, last]
            patterns.append(f"{first}.{last}@{domain}")      # first.last
            patterns.append(f"{first}{last}@{domain}")       # firstlast
            patterns.append(f"{first[0]}.{last}@{domain}")   # f.last
            patterns.append(f"{first}.{last[0]}@{domain}")   # first.l
            patterns.append(f"{first}@{domain}")             # first
            patterns.append(f"{last}@{domain}")              # last
        elif first:
            patterns.append(f"{first}@{domain}")
        
        return patterns

    def get_mx_records(self, domain: str) -> List[str]:
        try:
            records = dns.resolver.resolve(domain, 'MX')
            sorted_records = sorted(records, key=lambda r: r.preference)
            return [str(r.exchange).rstrip('.') for r in sorted_records]
        except Exception as e:
            print(f"DNS Error: {e}")
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

    def generate_random_email(self, domain: str) -> str:
        """Generate a random email for catch-all detection."""
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
        return f"chk_{random_string}@{domain}"

    def find_email(self, domain: str, full_name: str) -> EmailFinderResponse:
        domain = self.normalize_domain(domain)
        first, last = self.normalize_name(full_name)
        patterns = self.generate_patterns(first, last, domain)
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

        mx_host = mx_records[0]
        
        # STEP 1: Catch-All Check (CRUCIAL - Must be first)
        catch_all_email = self.generate_random_email(domain)
        is_valid, log, code = self.verify_email(catch_all_email, mx_host)
        response.smtpLogs.append(f"Catch-all check ({catch_all_email}): {log}")
        
        if is_valid:
            # Server accepts all emails (Catch-All)
            response.catchAll = True
            response.status = "catch_all"
            response.debugInfo = f"MX: {mx_host} | Catch-all detected (low confidence)"
            # Return best guess (first.last)
            if patterns:
                response.email = patterns[0]
            return response

        # STEP 2: Pattern Testing (Only if server is "Honest" - rejected catch-all)
        for i, pattern in enumerate(patterns):
            # Politeness: 1s delay between checks
            if i > 0:
                time.sleep(1)
                
            is_valid, log, code = self.verify_email(pattern, mx_host)
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
