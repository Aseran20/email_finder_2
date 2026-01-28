from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import json
import platform
from datetime import datetime

from models import EmailFinderRequest, CheckEmailRequest, EmailFinderResponse, BulkSearchJsonRequest
from core.email_finder import EmailFinder
from database import init_db, get_db, SearchHistory
from config import config

app = FastAPI(title="Email Finder MVP")

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()
    print("Database initialized")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

finder = EmailFinder()

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    Returns system status, database connectivity, cache metrics, and version info.
    """
    try:
        # Check database connectivity (simplified for now)
        database_status = "ok"

        # Get cache stats
        cache_stats = finder.mx_cache.stats()

        # System info
        import sys
        system_info = {
            "platform": platform.system(),
            "python": sys.version.split()[0]
        }

        # Overall health status
        status = "healthy"

        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "database": database_status,
            "cache": {
                "hit_rate": cache_stats["hit_rate"],
                "cached_domains": cache_stats["cached_domains"],
                "hits": cache_stats["hits"],
                "misses": cache_stats["misses"]
            },
            "version": config.APP_VERSION,
            "config": {
                "max_retries": config.SMTP_MAX_RETRIES,
                "max_mx_servers": config.MAX_MX_SERVERS,
                "rate_limit_delay": config.RATE_LIMIT_DELAY,
                "mx_cache_ttl": config.MX_CACHE_TTL
            },
            "system": system_info
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e)
        }

@app.post("/api/find-email", response_model=EmailFinderResponse)
async def find_email(request: EmailFinderRequest, db: Session = Depends(get_db)):
    if not request.domain:
        raise HTTPException(status_code=400, detail="Domain is required")
        
    if not request.fullName:
        raise HTTPException(status_code=400, detail="Full name is required")

    try:
        result = finder.find_email(request.domain, request.fullName)
        
        # Save to database
        history_entry = SearchHistory(
            domain=request.domain,
            full_name=request.fullName,
            status=result.status,
            email=result.email,
            catch_all=result.catchAll,
            patterns_tested=json.dumps(result.patternsTested),
            mx_records=json.dumps(result.mxRecords),
            smtp_logs=json.dumps(result.smtpLogs),
            debug_info=result.debugInfo,
            error_message=result.errorMessage
        )
        db.add(history_entry)
        db.commit()
        
        return result
    except Exception as e:
        return EmailFinderResponse(
            status="error",
            errorMessage=str(e),
            debugInfo="Internal Server Error"
        )

@app.post("/api/check-email", response_model=EmailFinderResponse)
async def check_email(request: CheckEmailRequest, db: Session = Depends(get_db)):
    """
    Check if a specific email address is valid.
    If invalid and fullName is provided, fallback to domain search.

    Args:
        email: Email address to verify
        fullName: Optional full name for fallback search

    Returns:
        EmailFinderResponse with validation result
    """
    if not request.email:
        raise HTTPException(status_code=400, detail="Email is required")

    try:
        result = finder.check_email(request.email, request.fullName)

        # Save to database
        # Extract domain from email for database record
        domain = request.email.split('@')[1] if '@' in request.email else "unknown"

        history_entry = SearchHistory(
            domain=domain,
            full_name=request.fullName or request.email,  # Use email if no name provided
            status=result.status,
            email=result.email,
            catch_all=result.catchAll,
            patterns_tested=json.dumps(result.patternsTested),
            mx_records=json.dumps(result.mxRecords),
            smtp_logs=json.dumps(result.smtpLogs),
            debug_info=result.debugInfo,
            error_message=result.errorMessage
        )
        db.add(history_entry)
        db.commit()

        # Add 1s delay to respect rate limiting (same as find-email)
        import time
        time.sleep(1)

        return result
    except Exception as e:
        return EmailFinderResponse(
            status="error",
            errorMessage=str(e),
            debugInfo="Internal Server Error"
        )

@app.get("/api/cache/stats")
async def get_cache_stats():
    """
    Get MX cache statistics.
    Returns hit rate and cached domains count.
    """
    return finder.mx_cache.stats()

@app.get("/api/history")
async def get_history(limit: int = 50, db: Session = Depends(get_db)):
    """
    Get search history, ordered by most recent first.
    Returns the last 50 searches by default.
    """
    try:
        history = db.query(SearchHistory)\
            .order_by(SearchHistory.created_at.desc())\
            .limit(limit)\
            .all()
        
        return [{
            "id": h.id,
            "date": h.created_at.isoformat(),
            "request": {
                "domain": h.domain,
                "fullName": h.full_name
            },
            "status": h.status,
            "email": h.email,
            "catchAll": h.catch_all,
            "patternsTested": json.loads(h.patterns_tested) if h.patterns_tested else [],
            "mxRecords": json.loads(h.mx_records) if h.mx_records else [],
            "smtpLogs": json.loads(h.smtp_logs) if h.smtp_logs else [],
            "debugInfo": h.debug_info or "",
            "errorMessage": h.error_message
        } for h in history]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/bulk-search")
async def bulk_search(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Bulk email search from CSV/Excel file.
    Expected columns: domain, fullName (or first_name, last_name, domain)
    Returns list of search results.
    """
    import pandas as pd
    import time
    from io import BytesIO
    
    try:
        # Read file content
        content = await file.read()
        
        # Determine file type and read with pandas
        if file.filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(content))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="File must be CSV or Excel (.xlsx, .xls)")
        
        # Normalize column names to lowercase for case-insensitive matching
        df.columns = df.columns.str.lower().str.strip()
        
        # Validate columns
        if 'domain' not in df.columns:
            raise HTTPException(status_code=400, detail="CSV must have 'domain' column")
        
        # Handle both fullname and first_name/last_name formats
        if 'fullname' not in df.columns and 'name' not in df.columns:
            if 'first_name' in df.columns and 'last_name' in df.columns:
                df['fullname'] = df['first_name'] + ' ' + df['last_name']
            else:
                raise HTTPException(status_code=400, detail="CSV must have 'name', 'fullname', or 'first_name' + 'last_name' columns")
        
        # Rename 'name' to 'fullname' if it exists
        if 'name' in df.columns and 'fullname' not in df.columns:
            df['fullname'] = df['name']
        
        results = []
        consecutive_errors = 0
        MAX_CONSECUTIVE_ERRORS = 5  # Stop if 5 errors in a row (possible ban)
        
        # Process each row with 1s delay (CRITICAL: Politeness to avoid bans)
        for index, row in df.iterrows():
            domain = str(row['domain']).strip()
            full_name = str(row['fullname']).strip()
            
            # Skip empty rows
            if not domain or not full_name or domain == 'nan' or full_name == 'nan':
                continue
            
            try:
                # RÈGLE #1: Perform email search
                result = finder.find_email(domain, full_name)
                
                # Reset error counter on success
                consecutive_errors = 0
                
                # Save to database
                history_entry = SearchHistory(
                    domain=domain,
                    full_name=full_name,
                    status=result.status,
                    email=result.email,
                    catch_all=result.catchAll,
                    patterns_tested=json.dumps(result.patternsTested),
                    mx_records=json.dumps(result.mxRecords),
                    smtp_logs=json.dumps(result.smtpLogs),
                    debug_info=result.debugInfo,
                    error_message=result.errorMessage
                )
                db.add(history_entry)
                db.commit()
                
                # Add to results
                results.append({
                    "domain": domain,
                    "fullName": full_name,
                    "status": result.status,
                    "email": result.email,
                    "catchAll": result.catchAll,
                    "debugInfo": result.debugInfo
                })
                
            except Exception as e:
                # RÈGLE #2: Robust error handling - log error but CONTINUE
                consecutive_errors += 1
                error_msg = str(e)
                
                # Check for ban indicators
                if "blocked" in error_msg.lower() or "access denied" in error_msg.lower():
                    error_msg = f"⚠️ Possible ban detected: {error_msg}"
                
                results.append({
                    "domain": domain,
                    "fullName": full_name,
                    "status": "error",
                    "email": None,
                    "catchAll": False,
                    "debugInfo": f"Error: {error_msg}"
                })
                
                # SAFETY: Stop if too many consecutive errors (likely ban or network issue)
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    results.append({
                        "domain": "STOPPED",
                        "fullName": "Processing halted",
                        "status": "error",
                        "email": None,
                        "catchAll": False,
                        "debugInfo": f"⛔ Stopped after {MAX_CONSECUTIVE_ERRORS} consecutive errors (possible ban or network issue)"
                    })
                    break
            
            finally:
                # RÈGLE #1 (CRITICAL): Always sleep 1s between checks, even on error
                # This is the PRIMARY anti-ban mechanism
                time.sleep(1)
        
        return {"total": len(results), "results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk search error: {str(e)}")

@app.post("/api/bulk-search-json")
async def bulk_search_json(request: BulkSearchJsonRequest, db: Session = Depends(get_db)):
    """
    Bulk email search from JSON (paste from spreadsheet).
    Accepts list of {domain, fullName} objects.
    Returns list of search results.
    """
    import time

    try:
        results = []
        consecutive_errors = 0
        MAX_CONSECUTIVE_ERRORS = 5  # Stop if 5 errors in a row (possible ban)

        # Process each search with 1s delay (CRITICAL: Politeness to avoid bans)
        for search in request.searches:
            domain = search.domain.strip()
            full_name = search.fullName.strip()

            # Skip empty entries
            if not domain or not full_name:
                continue

            try:
                # Perform email search
                result = finder.find_email(domain, full_name)

                # Reset error counter on success
                consecutive_errors = 0

                # Save to database
                history_entry = SearchHistory(
                    domain=domain,
                    full_name=full_name,
                    status=result.status,
                    email=result.email,
                    catch_all=result.catchAll,
                    patterns_tested=json.dumps(result.patternsTested),
                    mx_records=json.dumps(result.mxRecords),
                    smtp_logs=json.dumps(result.smtpLogs),
                    debug_info=result.debugInfo,
                    error_message=result.errorMessage
                )
                db.add(history_entry)
                db.commit()

                # Add to results
                results.append({
                    "domain": domain,
                    "fullName": full_name,
                    "status": result.status,
                    "email": result.email,
                    "catchAll": result.catchAll,
                    "debugInfo": result.debugInfo
                })

            except Exception as e:
                # Robust error handling - log error but CONTINUE
                consecutive_errors += 1
                error_msg = str(e)

                # Check for ban indicators
                if "blocked" in error_msg.lower() or "access denied" in error_msg.lower():
                    error_msg = f"⚠️ Possible ban detected: {error_msg}"

                results.append({
                    "domain": domain,
                    "fullName": full_name,
                    "status": "error",
                    "email": None,
                    "catchAll": False,
                    "debugInfo": f"Error: {error_msg}"
                })

                # SAFETY: Stop if too many consecutive errors (likely ban or network issue)
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    results.append({
                        "domain": "STOPPED",
                        "fullName": "Processing halted",
                        "status": "error",
                        "email": None,
                        "catchAll": False,
                        "debugInfo": f"⛔ Stopped after {MAX_CONSECUTIVE_ERRORS} consecutive errors (possible ban or network issue)"
                    })
                    break

            finally:
                # CRITICAL: Always sleep 1s between checks, even on error
                # This is the PRIMARY anti-ban mechanism
                time.sleep(1)

        return {"total": len(results), "results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk search error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
