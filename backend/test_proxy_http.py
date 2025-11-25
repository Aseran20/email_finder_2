import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_http_proxy():
    proxy_url = os.getenv("IPROYAL_PROXY_URL")
    print(f"Testing proxy: {proxy_url}")
    
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    
    try:
        print("Sending request to http://httpbin.org/ip...")
        response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_http_proxy()
