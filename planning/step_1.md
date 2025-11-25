Prompt pour Antigravity
Context : We are pivoting the infrastructure of the email_finder_2 project. Previously, we tried to use rotating proxies (IPRoyal) to verify emails, but they blocked Port 25 (SMTP), making verification impossible. We have now acquired a dedicated VPS (RackNerd) specifically for this task. Current Infrastructure :

OS: Linux (Ubuntu/Debian)

Public IP: 192.3.81.106

Hostname (rDNS configured): vps.auraia.ch

Port 25: Open and accessible directly from this machine.

Goal for Step 1: Refactor the backend to remove all Proxy logic and implement direct SMTP verification using the local network interface.

Detailed Task List:

Cleanup:

Delete backend/core/proxy.py and remove ProxyManager references.

Clean up requirements.txt (remove proxy-related libs like pysocks if not needed).

Configuration:

Update backend/.env (and models.py / config loader) to include:

SMTP_HOSTNAME="vps.auraia.ch" (Crucial for the HELO/EHLO handshake).

SMTP_FROM_EMAIL="verify@vps.auraia.ch"

Core Logic Refactor (backend/core/email_finder.py):

Rewrite the EmailFinder class to use python's native smtplib and dnspython.

Critical logic:

Resolve MX records for the target domain.

Connect directly to the MX server on Port 25.

Send EHLO vps.auraia.ch (Must match our rDNS).

Send MAIL FROM: <verify@vps.auraia.ch>.

Send RCPT TO: <target_email>.

Catch 250 OK (Valid), 550 (Invalid), and handle Catch-All detection (wildcard test).

Safety: Implement a basic timeout (5s) to avoid hanging processes.

Endpoint Update:

Ensure backend/main.py calls this new direct verification logic properly.

Constraint: Do not use any external API or Proxy. The code must run locally on the VPS and talk directly to the target mail servers.