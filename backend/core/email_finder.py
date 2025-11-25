import smtplib
import socket
import dns.resolver
import re
import socks
from typing import List, Optional, Tuple
from .proxy import ProxyManager
from models import EmailFinderResponse

class EmailFinder:
    def __init__(self):
        self.proxy_manager = ProxyManager()

    def _configure_proxy(self):
        proxy_config = self.proxy_manager.get_next_proxy()
        if proxy_config and proxy_config['protocol'] == 'socks5':
            print(f"Configuring SOCKS5 proxy: {proxy_config['host']}:{proxy_config['port']}")
            socks.setdefaultproxy(
                socks.SOCKS5,
                proxy_config['host'],
                proxy_config['port'],
                True, # rdns
                proxy_config['user'],
                proxy_config['password']
            )
            socks.wrapmodule(smtplib)

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
        patterns = []
        if first and last:
            patterns.append(f"{first}.{last}@{domain}")
            patterns.append(f"{first}@{domain}")
            patterns.append(f"{last}@{domain}")
            patterns.append(f"{first[0]}.{last}@{domain}")
            patterns.append(f"{first}.{last[0]}@{domain}")
            patterns.append(f"{first}{last}@{domain}")
            patterns.append(f"{first}_{last}@{domain}")
            patterns.append(f"{first}-{last}@{domain}")
            patterns.append(f"{last}.{first}@{domain}")
        elif first:
            patterns.append(f"{first}@{domain}")
        
        return patterns[:15] # Limit to 15

    def get_mx_records(self, domain: str) -> List[str]:
        try:
            records = dns.resolver.resolve(domain, 'MX')
            # Sort by preference
            sorted_records = sorted(records, key=lambda r: r.preference)
            return [str(r.exchange).rstrip('.') for r in sorted_records]
        except Exception as e:
            print(f"DNS Error: {e}")
            return []

    def verify_email(self, email: str, mx_host: str) -> Tuple[bool, str]:
        """
        Returns (is_valid, log_message)
        """
        self._configure_proxy()
        try:
            # SOCKS5 proxy is already configured globally via socks.wrapmodule(smtplib)
            server = smtplib.SMTP(mx_host, 25, timeout=10)
            server.ehlo()
            
            # MAIL FROM
            server.mail("test@example.com")
            
            # RCPT TO
            code, message = server.rcpt(email)
            server.quit()
            
            log = f"{mx_host}: {code} {message.decode('ascii', errors='ignore')}"
            
            if code == 250 or code == 251:
                return True, log
            return False, log
            
        except Exception as e:
            return False, f"{mx_host}: Error {str(e)}"

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

        mx_host = mx_records[0] # Use primary MX
        
        # Check for catch-all
        catch_all_email = f"zzq123invalid@{domain}"
        is_valid, log = self.verify_email(catch_all_email, mx_host)
        response.smtpLogs.append(f"Catch-all check: {log}")
        
        if is_valid:
            response.catchAll = True
            response.status = "unknown"
            response.debugInfo = f"MX: {mx_host} | Catch-all detected"
            # Best guess
            if patterns:
                response.email = patterns[0]
            return response

        # Test patterns
        for pattern in patterns:
            is_valid, log = self.verify_email(pattern, mx_host)
            response.smtpLogs.append(log)
            
            if is_valid:
                response.status = "valid"
                response.email = pattern
                response.debugInfo = f"MX: {mx_host} | Match: {pattern}"
                return response

        response.status = "not_found"
        response.debugInfo = f"MX: {mx_host} | {len(patterns)} patterns tested | No match"
        return response
