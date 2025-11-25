import os
import random
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

class ProxyManager:
    def __init__(self):
        self.proxies = self._load_proxies()
        self.current_index = 0

    def _load_proxies(self) -> List[str]:
        proxy_url = os.getenv("IPROYAL_PROXY_SOCKS5")
        if not proxy_url:
            return []
        # In the future, this could parse a comma-separated list
        return [proxy_url]

    def get_next_proxy(self) -> Optional[dict]:
        """
        Returns a proxy dictionary compatible with requests/smtplib (if supported)
        or just the proxy URL details for manual connection handling.
        For this MVP, we return the parsed details.
        """
        if not self.proxies:
            return None

        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        
        # Parse the proxy URL: http://user:pass@host:port
        try:
            # Parse the proxy URL: http://user:pass@host:port
            # Remove protocol if present
            if "://" in proxy:
                protocol, rest = proxy.split("://")
            else:
                protocol = "http"
                rest = proxy
            
            # Split auth and host
            if "@" in rest:
                auth_part, host_part = rest.split("@")
                user, password = auth_part.split(":")
            else:
                # Handle case without auth if necessary, though MVP assumes auth
                user = None
                password = None
                host_part = rest
            
            host, port = host_part.split(":")
            
            return {
                "host": host,
                "port": int(port),
                "user": user,
                "password": password,
                "protocol": protocol
            }
        except Exception:
            return None
