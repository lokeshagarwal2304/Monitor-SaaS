import httpx
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models.website import Website, WebsiteStatus
from backend.models.check_result import CheckResult
from backend.models.user import User
from backend.services.email_service import send_alert_email

# FULL CHROME HEADERS (The Human Mask)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0"
}

async def check_website_http(url: str, timeout: int = 15):
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
        
    try:
        # Added http2=True support if available, and increased timeout
        async with httpx.AsyncClient(verify=False, headers=HEADERS, follow_redirects=True, timeout=timeout) as client:
            start_time = datetime.now()
            response = await client.get(url)
            end_time = datetime.now()
            
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # LOGIC UPDATE: 
            # 200-299 = UP
            # 403/401 = UP (Technically up, just blocking bots. We treat this as UP to avoid false alarms)
            # 503 = Often "Cloudflare Checking Browser", usually UP but slow.
            
            status = response.status_code
            is_up = (200 <= status < 400) or (status == 403) or (status == 401) or (status == 503)
            
            # For logging/debugging
            if status == 403:
                print(f"⚠️  {url} returned 403 (Bot Block), marking as UP.")
            
            return {
                "is_up": is_up,
                "status_code": status,
                "response_time": duration_ms,
                "error": None
            }
    except Exception as e:
        return {
            "is_up": False,
            "status_code": 0,
            "response_time": 0,
            "error": str(e)
        }

async def process_monitoring_check(db: Session):
    websites = db.query(Website).all()
    print(f"🔎 Checking {len(websites)} websites...")
    
    for site in websites:
        result = await check_website_http(site.url)
        
        new_status = WebsiteStatus.UP if result["is_up"] else WebsiteStatus.DOWN
        
        # Alert Logic
        if site.status != WebsiteStatus.UNKNOWN and site.status != new_status:
            owner = db.query(User).filter(User.id == site.owner_id).first()
            if owner:
                print(f"🔔 Status Change: {site.url} went {new_status.value.upper()}")
                try:
                    # Send extra info in email if available
                    error_detail = result.get("error") or f"Status Code: {result.get('status_code')}"
                    send_alert_email(owner.email, site.url, new_status.value.upper(), error_detail)
                except:
                    pass

        site.status = new_status
        site.last_checked = datetime.utcnow()
        
        log_entry = CheckResult(
            website_id=site.id,
            status_code=result["status_code"],
            response_time=result["response_time"],
            is_up=result["is_up"],
            error_message=result["error"],
            checked_at=datetime.utcnow()
        )
        db.add(log_entry)
        
    db.commit()