import smtplib
import dns.resolver
import socket
import logging

# Configuration spécifique à ton infra RackNerd
MY_HOSTNAME = "vps.auraia.ch"  # Ton rDNS
MY_IP = "192.3.81.106"         # Ton IP RackNerd
SENDER_EMAIL = "verify@vps.auraia.ch"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_mx_record(domain):
    try:
        records = dns.resolver.resolve(domain, 'MX')
        mx_record = str(records[0].exchange).rstrip('.')
        logger.info(f"Serveur MX trouvé pour {domain}: {mx_record}")
        return mx_record
    except Exception as e:
        logger.error(f"Erreur DNS pour {domain}: {e}")
        return None

def verify_email_direct(target_email):
    domain = target_email.split('@')[1]
    mx_host = get_mx_record(domain)
    
    if not mx_host:
        return "DNS_ERROR"

    logger.info(f"Connexion au serveur SMTP {mx_host} sur le port 25...")
    
    try:
        # On force l'utilisation de l'interface locale si besoin, 
        # mais sur un VPS simple, l'OS gère ça tout seul.
        server = smtplib.SMTP(timeout=10)
        server.set_debuglevel(1)  # On veut voir TOUT ce qu'il se passe
        
        # Connexion
        server.connect(mx_host, 25)
        
        # 1. HELO/EHLO (Crucial : doit matcher ton rDNS)
        server.ehlo(MY_HOSTNAME)
        
        # 2. MAIL FROM
        server.mail(SENDER_EMAIL)
        
        # 3. RCPT TO (Le test)
        code, message = server.rcpt(target_email)
        server.quit()
        
        if code == 250:
            return "VALID (Email existe)"
        elif code == 550:
            return "INVALID (N'existe pas)"
        else:
            return f"UNKNOWN (Code: {code}, Msg: {message})"

    except TimeoutError:
        return "TIMEOUT (Port 25 probablement bloqué par RackNerd)"
    except ConnectionRefusedError:
        return "BLOCKED (Refus de connexion par le serveur distant)"
    except Exception as e:
        return f"ERROR ({str(e)})"

if __name__ == "__main__":
    print(f"--- TEST INFRASTRUCTURE VPS ({MY_HOSTNAME}) ---")
    
    # Test 1 : Ton propre email pro (Doit être VALIDE)
    email_test_1 = "adrian.turion@auraia.ch"
    print(f"\nTest 1 : {email_test_1}")
    result1 = verify_email_direct(email_test_1)
    print(f"RÉSULTAT 1 : {result1}")
    
    # Test 2 : Email bidon sur le même domaine (Doit être INVALID ou CATCH-ALL)
    email_test_2 = "banane.flambee@auraia.ch"
    print(f"\nTest 2 : {email_test_2}")
    result2 = verify_email_direct(email_test_2)
    print(f"RÉSULTAT 2 : {result2}")
