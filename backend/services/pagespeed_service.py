import httpx
import asyncio
import time
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models.pagespeed import PageSpeedResult
from backend.models.website import Website, WebsiteStatus
from backend.config import PAGESPEED_API_KEY

def standardize_url(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")

async def get_basic_performance(url: str):
    """
    Performs a simple HEAD or GET check to measure response time and status.
    """
    url = standardize_url(url)
    start_time = time.time()
    try:
        # Use a strict timeout to prevent hanging the event loop
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            response = await client.get(url)
            end_time = time.time()
            load_time_ms = round((end_time - start_time) * 1000, 2)
            
            # Simple scoring: <500ms=90+, 500-1500=50-89, >1500=<50
            if load_time_ms < 500:
                score = 90 + min(10, int((500 - load_time_ms) / 50))
            elif load_time_ms < 1500:
                score = 50 + int((1500 - load_time_ms) / 25)
            else:
                score = max(10, 50 - int((load_time_ms - 1500) / 100))
            
            return {
                "success": True,
                "status": "UP" if response.is_success else "DOWN",
                "score": min(100, score),
                "load_time": load_time_ms,
                "fcp": None
            }
    except (httpx.TimeoutException, httpx.ConnectError) as e:
        return {
            "success": False,
            "error": "Connection Timeout" if isinstance(e, httpx.TimeoutException) else "Connection Failed",
            "status": "DOWN",
            "score": 0,
            "load_time": 0,
            "fcp": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status": "DOWN",
            "score": 0,
            "load_time": 0,
            "fcp": None
        }

async def run_pagespeed_check(url: str):
    """
    Main entry point for checking a monitor.
    Uses basic check for status and also tries Google API if available for richer data.
    """
    # 1. Start with the basic check for status and baseline score
    basic = await get_basic_performance(url)
    if basic["status"] == "DOWN":
        return basic
    
    # 2. Try to augment with Google PageSpeed for FCP and deeper score if possible
    # But only if basic check says the site is reachable
    url_norm = standardize_url(url)
    # We'll skip Google API here to save on quota per request unless explicitly desired
    # but the user wanted "Score (0-100), Load Time, Status, Last Checked".
    # I'll stick to basic check primarily as it's faster and fulfills the requirement of "Basic performance score"
    # and use Google API as an optional enhancement if key is provided.
    
    if PAGESPEED_API_KEY:
        api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url_norm}&category=performance&key={PAGESPEED_API_KEY}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(api_url)
                if response.status_code == 200:
                    data = response.json()
                    lighthouse = data.get("lighthouseResult", {})
                    perf_score = lighthouse.get("categories", {}).get("performance", {}).get("score", 0) * 100
                    fcp = lighthouse.get("audits", {}).get("first-contentful-paint", {}).get("numericValue", 0)
                    
                    # Update with richer data
                    basic["score"] = int(perf_score)
                    basic["fcp"] = fcp
        except:
            pass # Fallback to basic data is fine
            
    return basic

async def check_all_monitors_pagespeed(db: Session):
    monitors = db.query(Website).filter(Website.status != WebsiteStatus.PAUSED).all()
    for site in monitors:
        results = await run_pagespeed_check(site.url)
        # Store result
        ps_result = PageSpeedResult(
            monitor_id=site.id,
            score=results["score"],
            load_time=results["load_time"],
            status=results["status"],
            fcp=results.get("fcp"),
            checked_at=datetime.utcnow()
        )
        db.add(ps_result)
    db.commit()
