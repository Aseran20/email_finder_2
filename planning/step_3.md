ACT: Senior Python Backend Developer GOAL: Migrate Email Discovery Engine from "Rotating Proxies" to "Direct VPS SMTP"

Context: We have pivoted our infrastructure. We are no longer using external Proxies (IPRoyal) because they blocked SMTP port 25. We have deployed the app on a dedicated VPS with a clean IP and open Port 25. New Infrastructure Config:

Hostname (rDNS): vps.auraia.ch

Sender Email: verify@vps.auraia.ch

Method: Direct smtplib connection from the local interface.

Execution Plan (Step-by-Step):

1. CLEANUP (Remove Proxy Dependencies)
Delete backend/core/proxy.py.

Delete backend/test_proxy.py and backend/test_proxy_http.py.

Modify backend/requirements.txt: Remove PySocks, aiohttp_socks or any proxy-specific libraries. Keep dnspython.

Clean backend/core/email_finder.py: Remove all imports related to ProxyManager.

2. CORE LOGIC REWRITE (backend/core/email_finder.py)
Rewrite the EmailFinder class from scratch to use native smtplib and dns.resolver. It must implement the following Strict Logic:

A. Initialization

Load SMTP_HOSTNAME ("vps.auraia.ch") from env/config.

B. The find(first_name, last_name, domain) method workflow:

MX Lookup: Fetch MX records for domain. If none, return status NO_MX.

Catch-All Check (Priority #1):

Generate a fake email (e.g., chk_9s8d9@domain.com).

Connect to MX on Port 25.

Send EHLO vps.auraia.ch (CRITICAL: Must match rDNS).

Send MAIL FROM: <verify@vps.auraia.ch>.

Send RCPT TO: <fake_email>.

Decision:

If 250 OK: The server is Catch-All. -> STOP. Return a predicted email (first.last@domain) with status catch_all (Low Confidence).

If 550 User Unknown: The server is Honest. -> PROCEED to Step 3.

Permutation Testing (Priority #2 - Only if Honest):

Generate list: [first.last, firstlast, f.last, first.l, first, last] @ domain.

Loop through them.

Introduce a time.sleep(1) delay between checks to be polite.

Perform the SMTP Handshake for each.

If 250 OK: FOUND. Return email with status valid (High Confidence).

If 550: Continue.

Error Handling:

If connection times out (>5s) or refuses: Return status unreachable (Port 25 blocked or Firewall).

3. API & CONFIG UPDATE
Update backend/models.py / .env:

Add SMTP_HOSTNAME=vps.auraia.ch.

Add SMTP_FROM=verify@vps.auraia.ch.

Update backend/main.py:

Ensure the /search endpoint calls this new synchronous find logic (wrap it in run_in_executor if needed to avoid blocking the event loop, or keep it simple for MVP).

The API response structure must remain compatible with the Frontend (returning email, status, confidence).

Final Output Requirement: I want the code to be production-ready for the VPS. No "mock" data. Real SMTP checks.