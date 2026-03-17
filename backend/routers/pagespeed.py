from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.database import get_db
from backend.models.website import Website, WebsiteStatus
from backend.models.pagespeed import PageSpeedResult
from backend.models.user import User
from backend.utils.dependencies import get_current_user
from backend.services.pagespeed_service import run_pagespeed_check, get_basic_performance, standardize_url

router = APIRouter(prefix="/api/pagespeed", tags=["PageSpeed"])

@router.get("/list")
def get_latest_pagespeed_results(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_role = str(current_user.role.value) if hasattr(current_user.role, 'value') else str(current_user.role)
    
    if user_role.upper() == "ADMIN":
        websites = db.query(Website).all()
    else:
        websites = db.query(Website).filter(Website.owner_id == current_user.id).all()
        
    results = []
    
    for site in websites:
        try:
            latest = db.query(PageSpeedResult).filter(PageSpeedResult.monitor_id == site.id).order_by(desc(PageSpeedResult.checked_at)).first()
            
            # Determine perf status (FAST/SLOW)
            perf_status = "UNKNOWN"
            if latest and latest.load_time is not None:
                try:
                    lt = float(latest.load_time)
                    if lt < 1000: perf_status = "FAST"
                    elif lt < 3000: perf_status = "AVERAGE"
                    else: perf_status = "SLOW"
                except:
                    perf_status = "ERROR"
            elif latest:
                perf_status = "PENDING"

            if latest:
                results.append({
                    "monitor_id": site.id,
                    "monitor_name": site.name or str(site.url).replace("https://", "").replace("http://", ""),
                    "website": str(site.url),
                    "score": latest.score if latest.score is not None else 0,
                    "load_time": round(float(latest.load_time), 2) if latest.load_time is not None else 0,
                    "check_status": str(latest.status or "UP"),
                    "status": perf_status,
                    "fcp": round(float(latest.fcp), 2) if latest.fcp else 0,
                    "last_checked": latest.checked_at.isoformat() if hasattr(latest.checked_at, 'isoformat') else None,
                })
            else:
                results.append({
                    "monitor_id": site.id,
                    "monitor_name": site.name or str(site.url).replace("https://", "").replace("http://", ""),
                    "website": str(site.url),
                    "score": None,
                    "load_time": 0,
                    "check_status": "UNKNOWN",
                    "status": "PENDING",
                    "fcp": 0,
                    "last_checked": None,
                })
        except Exception as e:
            print(f"Error processing pagespeed result for site {site.id}: {str(e)}")
            continue
            
    return results

@router.post("/check/{monitor_id}")
async def trigger_pagespeed_check(monitor_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_role = str(current_user.role.value) if hasattr(current_user.role, 'value') else str(current_user.role)
    
    if user_role.upper() == "ADMIN":
        site = db.query(Website).filter(Website.id == monitor_id).first()
    else:
        site = db.query(Website).filter(Website.id == monitor_id, Website.owner_id == current_user.id).first()
        
    if not site:
        raise HTTPException(status_code=404, detail="Monitor not found")
        
    res = await run_pagespeed_check(site.url)
    
    # Store result in DB
    new_result = PageSpeedResult(
        monitor_id=site.id,
        score=res["score"],
        load_time=res["load_time"],
        status=res["status"],
        fcp=res.get("fcp"),
        checked_at=datetime.utcnow()
    )
    db.add(new_result)
    db.commit()
    
    return {"status": "success", "data": res}

@router.get("/")
async def get_pagespeed_check(url: str = Query(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
            
        # Standardize
        norm_url = standardize_url(url)
        
        # Check if it belongs to a monitor
        site = db.query(Website).filter(
            (Website.url == norm_url) | (Website.url == url)
        ).first()
        
        if site:
            # Check if we have a recent result
            latest = db.query(PageSpeedResult).filter(PageSpeedResult.monitor_id == site.id).order_by(desc(PageSpeedResult.checked_at)).first()
            if latest:
                # Determine status
                ps = "UNKNOWN"
                try:
                    lt = float(latest.load_time) if latest.load_time is not None else 0
                    if lt > 0:
                        if lt < 1000: ps = "FAST"
                        elif lt < 3000: ps = "AVERAGE"
                        else: ps = "SLOW"
                    else:
                        ps = "PENDING"
                except:
                    ps = "ERROR"
                
                return {
                    "monitor_id": site.id,
                    "monitor_name": site.name or str(site.url).replace("https://", "").replace("http://", ""),
                    "website": str(site.url),
                    "score": latest.score if latest.score is not None else 0,
                    "load_time": round(float(latest.load_time), 2) if latest.load_time is not None else 0,
                    "status": ps,
                    "check_status": str(latest.status or "UP"),
                    "last_checked": latest.checked_at.isoformat() if hasattr(latest.checked_at, "isoformat") else None
                }
                
        # If not site or no result, run fresh
        res = await run_pagespeed_check(url)
        
        # Determine Status
        perf_status = "UNKNOWN"
        load_val = res.get("load_time", 0)
        lt = float(load_val) if load_val is not None else 0
        
        if lt > 0:
            if lt < 1000: perf_status = "FAST"
            elif lt < 3000: perf_status = "AVERAGE"
            else: perf_status = "SLOW"
        
        return {
            "monitor_id": site.id if site else None,
            "monitor_name": str(url).replace("https://", "").replace("http://", ""),
            "website": str(url),
            "score": res.get("score", 0),
            "load_time": lt,
            "status": perf_status,
            "check_status": res.get("status", "UP"),
            "last_checked": datetime.utcnow().isoformat()
        }
    except Exception as e:
        import traceback
        print("ERROR in PageSpeed Check API:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def sync_all_pagespeed(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Refresh all monitors for the current user.
    """
    user_role = str(current_user.role.value) if hasattr(current_user.role, 'value') else str(current_user.role)
    
    if user_role.upper() == "ADMIN":
        websites = db.query(Website).all()
    else:
        websites = db.query(Website).filter(Website.owner_id == current_user.id).all()
        
    for site in websites:
        res = await run_pagespeed_check(site.url)
        new_result = PageSpeedResult(
            monitor_id=site.id,
            score=res["score"],
            load_time=res["load_time"],
            status=res["status"],
            fcp=res.get("fcp"),
            checked_at=datetime.utcnow()
        )
        db.add(new_result)
    
    db.commit()
    return {"status": "success", "count": len(websites)}