Context: We are pivoting the infrastructure. We are removing the Rotating Proxy system (IPRoyal) because it blocked Port 25. We are switching to a Direct VPS strategy using a dedicated RackNerd server.

Infrastructure Info:

Hostname (rDNS): vps.auraia.ch

IP: 192.3.81.106 (Local interface)

Port 25: Open.

Task: Refactor backend/core/email_finder.py to become a full standalone Email Discovery Engine using direct SMTP connections.

Detailed Implementation Steps:

Cleanup:

Remove backend/core/proxy.py and ProxyManager. Remove dependencies like pysocks.

Update backend/.env to include SMTP_HOSTNAME="vps.auraia.ch" and SMTP_FROM="verify@vps.auraia.ch".

Core Logic (Rewrite EmailFinder class): Use smtplib and dnspython directly. Implement the following workflow in the find method:

Phase A: Preparation

Accept first_name, last_name, domain.

Fetch MX records for domain (sorted by priority). If no MX, return INVALID.

Phase B: Catch-All Check (Crucial)

Generate a random non-existent email (e.g., chk_82910@domain.com).

Perform an SMTP Handshake (HELO -> MAIL FROM -> RCPT TO).

Logic:

If Server responds 250 OK: The domain is CATCH-ALL. -> STOP. Do not test permutations. Return the most probable email (first.last@domain.com) but mark status as catch_all / risky.

If Server responds 550: The domain is HONEST. -> PROCEED to Phase C.

Phase C: Permutations Discovery (Only if HONEST)

Generate common patterns:

first.last@domain

firstlast@domain

f.last@domain

first.l@domain

first@domain

last@domain

Iterate through them one by one.

Politeness: Add a time.sleep(1) between each SMTP check to avoid rate-limiting.

If 250 OK is received: STOP. Return this email as valid.

If 550 is received: Continue to next pattern.

Technical Constraints:

HELO/EHLO: You MUST use server.helo("vps.auraia.ch"). Do not use localhost.

Timeouts: Set SMTP timeout to 5-10 seconds. Catch socket.timeout and return a specific "Time out / Blocked" error.

Safety: Ensure the connection is closed (server.quit()) even if errors occur.

Integration:

Update main.py to use this new synchronous logic (or wrap it properly in the async endpoint).

Goal: The output should be a clean, direct-connection email finder that follows the "Catch-all first, then permutations" strategy.