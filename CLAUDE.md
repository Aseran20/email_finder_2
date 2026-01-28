# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**VPS Email Finder** - Professional email verification system using direct SMTP validation. Deployed in production at Auraia for internal use (~200 searches/day).

**Stack**: FastAPI (Python 3.12+) backend + React frontend + SQLite database
**Production**: http://192.3.81.106:8000 (API) + https://email.auraia.ch (Frontend)
**VPS**: ssh root@192.3.81.106 (RackNerd, systemd service)

## Essential Commands

### Development Workflow

```bash
# Backend development (from /backend)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Run tests (IMPORTANT: Always run before deployment)
pip install -r requirements-dev.txt
pytest tests/ -v --cov

# Single test file
pytest tests/test_email_finder.py -v

# Check test coverage
pytest tests/ --cov --cov-report=html
# Open: backend/htmlcov/index.html

# Frontend development (from /frontend)
npm install
npm run dev  # http://localhost:5173
```

### Production Deployment

```powershell
# Deploy backend changes to VPS
cd C:\Users\AdrianTurion\devprojects\2-auraia\vps-email-finder

# Copy modified files
scp backend/main.py root@192.3.81.106:/root/vps-email-finder/backend/
scp backend/core/email_finder.py root@192.3.81.106:/root/vps-email-finder/backend/core/

# Restart service
ssh root@192.3.81.106 "systemctl restart email-finder"

# Verify deployment
curl http://192.3.81.106:8000/api/cache/stats
```

### Monitoring & Debugging

```bash
# Check service status
ssh root@192.3.81.106 "systemctl status email-finder"

# View real-time logs
ssh root@192.3.81.106 "tail -f /root/logs/email_finder.log"

# View systemd logs (errors during startup)
ssh root@192.3.81.106 "journalctl -u email-finder -n 100"

# Test API endpoints
curl http://192.3.81.106:8000/api/cache/stats
curl http://192.3.81.106:8000/api/history?limit=5

# Full email search test
curl -X POST "http://192.3.81.106:8000/api/find-email" \
  -H "Content-Type: application/json" \
  -d '{"domain":"auraia.ch","fullName":"Adrian Turion"}'
```

## Architecture & Design Decisions

### Core Email Verification Flow

**File**: `backend/core/email_finder.py`

1. **DNS MX Lookup** (with 1h in-memory cache via `mx_cache.py`) - reduces ~100-150 DNS queries/day
2. **Catch-All Detection** (CRITICAL - must run first):
   - Tests random email (e.g., `chk_xyz123@domain.com`)
   - If accepted → Server is catch-all (Microsoft 365, Google common) → Return `status: "catch_all"` with best-guess pattern
   - If rejected → Server is honest → Proceed to pattern testing
3. **Pattern Testing** (only if not catch-all):
   - Tests 9 patterns in priority order: `first.last@`, `firstlast@`, `f.last@`, etc.
   - 1-second delay between tests (ANTI-BAN mechanism - never remove)
   - Returns first valid match with `status: "valid"`

**Key Constraints**:
- **1-second delay between SMTP checks is MANDATORY** (`time.sleep(1)` in email_finder.py:209 and main.py:224)
- Catch-all detection MUST run before pattern testing (prevents false positives)
- MX cache reduces latency by 50-100ms per search (target: >50% hit rate)

### Name Normalization & Pattern Generation

**File**: `backend/core/email_finder.py:38-105`

Handles edge cases:
- **Accents**: "André" → "andre" (using unidecode)
- **Hyphens**: "Mads-Håkon" → generates both "mads-hakon" and "madshakon" variants
- **Missing permutations**: Includes `jdoe@`, `doej@`, `johnd@` (added after finding gaps)

**Pattern priority** (most common first):
1. `first.last@domain.com`
2. `firstlast@domain.com`
3. `f.last@domain.com`
4. `first.l@domain.com`
5. ... (9 total patterns)

### API Structure

**File**: `backend/main.py`

- `/api/find-email` (POST) - Single email search
- `/api/bulk-search` (POST) - CSV/Excel batch processing with rate limiting
- `/api/history` (GET) - Search history from SQLite
- `/api/cache/stats` (GET) - MX cache metrics (hits, misses, hit_rate)

**Database**: SQLite (`/root/data/email_finder.db` on VPS) - sufficient for current volume (~200/day)

### Logging Strategy

**File**: `backend/core/logger.py`

Structured logging with JSON support (currently disabled for development):
- `logger = StructuredLogger("email_finder", json_format=False)`
- Change to `json_format=True` for production JSON logs
- Logs written to `/root/logs/email_finder.log` on VPS

## Testing Philosophy

**Coverage**: 86% (31/37 tests pass)
**Location**: `backend/tests/`

**What to test**:
- ✅ Email pattern generation (including edge cases: accents, hyphens)
- ✅ Name normalization logic
- ✅ Catch-all detection logic
- ✅ MX cache hit/miss behavior
- ✅ API endpoint responses (mocked SMTP)

**Known failures**: 6 database tests fail due to SQLAlchemy mocking issues (non-critical, database works in production)

**Before deployment**: ALWAYS run `pytest tests/ -v` and ensure core tests pass.

## Common Modifications

### Change Email Patterns

**File**: `backend/core/email_finder.py` → `generate_patterns()` (line ~70)

Add new pattern to the list:
```python
patterns.append(f"{first}_{last}@{domain}")  # first_last@
```

### Adjust Cache TTL

**File**: `backend/core/email_finder.py` (line ~20)
```python
self.mx_cache = MXCache(ttl=7200)  # Change from 3600 (1h) to 7200 (2h)
```

### Add New API Endpoint

**File**: `backend/main.py`

```python
@app.get("/api/new-endpoint")
async def new_endpoint():
    return {"status": "ok"}
```

### Modify Rate Limiting in Bulk Search

**File**: `backend/main.py` (line ~224)
```python
time.sleep(2)  # Change from 1s to 2s (more conservative)
```

**WARNING**: Never remove the sleep entirely - this will cause IP bans from mail servers.

## VPS Production Environment

**Service**: `/etc/systemd/system/email-finder.service`
**Process**: uvicorn running on port 8000
**Database**: `/root/data/email_finder.db` (SQLite)
**Logs**: `/root/logs/email_finder.log`
**Repo**: `/root/vps-email-finder/` (Git)

**Key files on VPS**:
- `/root/vps-email-finder/backend/.env` - SMTP configuration (not in Git)
- `/etc/nginx/.htpasswd` - Basic Auth for frontend
- `~/.ssh/authorized_keys` - SSH key access

**Environment variables** (in `.env`):
```bash
SMTP_HOSTNAME=vps.auraia.ch
SMTP_FROM_EMAIL=verify@vps.auraia.ch
```

## Troubleshooting Guide

### Service Not Responding

```bash
# Quick restart
ssh root@192.3.81.106 "systemctl restart email-finder"

# Check for port conflicts
ssh root@192.3.81.106 "lsof -i :8000"

# Check startup errors
ssh root@192.3.81.106 "journalctl -u email-finder -n 50"
```

### Cache Not Working (hit_rate = 0%)

```bash
# Verify mx_cache.py exists on VPS
ssh root@192.3.81.106 "ls -la /root/vps-email-finder/backend/core/mx_cache.py"

# Redeploy if missing
scp backend/core/mx_cache.py root@192.3.81.106:/root/vps-email-finder/backend/core/
ssh root@192.3.81.106 "systemctl restart email-finder"
```

### All Searches Return "error"

**Likely causes**:
1. Port 25 blocked by hosting provider
2. IP banned by target mail servers (too many requests)
3. Reverse DNS misconfigured

**Debug**:
```bash
# Test SMTP manually
ssh root@192.3.81.106
telnet gmail-smtp-in.l.google.com 25
> HELO vps.auraia.ch
> MAIL FROM:<verify@vps.auraia.ch>
> RCPT TO:<test@gmail.com>
> QUIT

# Verify reverse DNS
host 192.3.81.106
# Should return: vps.auraia.ch
```

### Tests Failing Locally

```bash
# Ensure dev dependencies installed
pip install -r backend/requirements-dev.txt

# Run with verbose output
pytest tests/ -v -s

# Known issue: 6 database tests fail (SQLAlchemy mocking) - this is expected
# Core functionality tests (email_finder, patterns, cache) MUST pass
```

## Security Notes

- **API has NO authentication** (acceptable for internal use, but consider adding if exposed)
- **Frontend has Basic Auth** via nginx (credentials in `/etc/nginx/.htpasswd`)
- **SSH access** via key only (password auth disabled)
- **Port 25 required** for SMTP verification (ensure not blocked)

## Performance Targets

- **Cache hit rate**: >50% (check via `/api/cache/stats`)
- **API response time**: <5s per email (including SMTP)
- **Bulk search**: 1 email/second (enforced delay)
- **Database size**: <50 MB for 10,000+ searches

## Documentation References

- **README.md** - Complete project overview
- **QUICKSTART.md** - 30-second getting started guide
- **PROJECT_FILES.md** - File index and structure
- **docs/API_USAGE.md** - API usage examples
- **docs/SESSION_NOTES.md** - Project history and decisions
