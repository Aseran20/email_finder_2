from core.email_finder import EmailFinder

def test_proxy():
    finder = EmailFinder()
    print("Testing proxy connection...")
    
    # Use a known domain with MX records (e.g., gmail.com)
    domain = "gmail.com"
    mx_records = finder.get_mx_records(domain)
    
    if not mx_records:
        print("Failed to get MX records")
        return

    mx_host = mx_records[0]
    print(f"MX Host: {mx_host}")
    
    # Test connection
    is_valid, log = finder.verify_email("test@gmail.com", mx_host)
    print(f"Result: {is_valid}")
    print(f"Log: {log}")

if __name__ == "__main__":
    test_proxy()
