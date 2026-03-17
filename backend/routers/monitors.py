from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, case

from backend.database import get_db
from backend.models.website import Website, WebsiteStatus
from backend.models.check_result import CheckResult
from backend.models.incident import Incident
from backend.models.user import User
from backend.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/monitors", tags=["Monitors"])

class MonitorUpdate(BaseModel):
    url: Optional[str] = None
    friendly_name: Optional[str] = None
    interval: Optional[int] = None
    region: Optional[str] = None
    notifications: Optional[str] = None
    timeout: Optional[int] = None
    keyword: Optional[str] = None
    ssl_check: Optional[bool] = None
    redirect_follow: Optional[bool] = None

@router.get("/{monitor_id}")
def get_monitor(
    monitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    monitor = db.query(Website).filter(Website.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
        
    if str(current_user.role.value).upper() != "ADMIN" and monitor.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return {
        "id": monitor.id,
        "name": monitor.name,
        "url": monitor.url,
        "type": "HTTPS" if str(monitor.url).startswith("https") else "HTTP",
        "status": monitor.status,
        "interval": monitor.check_interval,
        "created_at": monitor.created_at,
        "last_checked": monitor.last_checked,
        "up_since": monitor.up_since,
        "region": monitor.region,
        "notifications": monitor.notifications,
        "timeout": monitor.timeout,
        "keyword": monitor.keyword,
        "ssl_check": bool(monitor.ssl_check),
        "redirect_follow": bool(monitor.redirect_follow)
    }

@router.get("/{monitor_id}/checks")
def get_monitor_checks(
    monitor_id: int,
    limit: int = 100,
    hours: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Authorization checks would ideally be extracted, but doing inline for speed
    monitor = db.query(Website).filter(Website.id == monitor_id).first()
    if not monitor or (str(current_user.role.value).upper() != "ADMIN" and monitor.owner_id != current_user.id):
        raise HTTPException(status_code=404, detail="Monitor not found")
        
    query = db.query(CheckResult).filter(CheckResult.website_id == monitor_id)
    
    if hours:
        since = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(CheckResult.checked_at >= since)
        # If hours is specified, we might want more than 100 checks
        # Let's increase the default limit in that case if it's still 100
        if limit == 100:
            limit = 1000 
            
    checks = query.order_by(desc(CheckResult.checked_at)).limit(limit).all()
    
    return [
        {
            "id": c.id,
            "status": "UP" if c.is_up else "DOWN",
            "response_time": c.response_time,
            "status_code": c.status_code,
            "checked_at": c.checked_at,
            "error": c.error_message
        } for c in checks
    ]

@router.get("/{monitor_id}/stats")
def get_monitor_stats(
    monitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    monitor = db.query(Website).filter(Website.id == monitor_id).first()
    if not monitor or (str(current_user.role.value).upper() != "ADMIN" and monitor.owner_id != current_user.id):
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    # Calculate stats over last 24h or total
    since_24h = datetime.utcnow() - timedelta(hours=24)
    
    stats = db.query(
        func.avg(CheckResult.response_time).label('avg_response'),
        func.min(CheckResult.response_time).label('min_response'),
        func.max(CheckResult.response_time).label('max_response'),
        func.count(CheckResult.id).label('total_checks')
    ).filter(CheckResult.website_id == monitor.id).first()
    
    # 24h counts
    up_count_24h = db.query(func.count(CheckResult.id)).filter(
        CheckResult.website_id == monitor.id,
        CheckResult.is_up == True,
        CheckResult.checked_at >= since_24h
    ).scalar() or 0
    
    down_count_24h = db.query(func.count(CheckResult.id)).filter(
        CheckResult.website_id == monitor.id,
        CheckResult.is_up == False,
        CheckResult.checked_at >= since_24h
    ).scalar() or 0
    
    # Since we don't log "PAUSED" checks in CheckResult (they are skipped),
    # we return 1 if current status is paused, as requested by UI logic
    paused_count_24h = 1 if monitor.status == WebsiteStatus.PAUSED else 0
    
    total_checks = stats.total_checks or 0
    
    # Global/Total stats
    up_checks_total = db.query(func.count(CheckResult.id)).filter(
        CheckResult.website_id == monitor.id,
        CheckResult.is_up == True
    ).scalar() or 0
    
    uptime_percentage = (up_checks_total / total_checks * 100) if total_checks > 0 else None
    
    return {
        "average_response_time": round(stats.avg_response, 2) if stats.avg_response else 0,
        "minimum_response_time": round(stats.min_response, 2) if stats.min_response else 0,
        "maximum_response_time": round(stats.max_response, 2) if stats.max_response else 0,
        "uptime_percentage": round(uptime_percentage, 2) if uptime_percentage is not None else None,
        "total_checks": total_checks,
        "up_count_24h": up_count_24h,
        "down_count_24h": down_count_24h,
        "paused_count_24h": paused_count_24h
    }

@router.get("/{monitor_id}/incidents")
def get_monitor_incidents(
    monitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    monitor = db.query(Website).filter(Website.id == monitor_id).first()
    if not monitor or (str(current_user.role.value).upper() != "ADMIN" and monitor.owner_id != current_user.id):
        raise HTTPException(status_code=404, detail="Monitor not found")
        
    incidents = db.query(Incident).filter(Incident.monitor_id == monitor.id).order_by(desc(Incident.started_at)).limit(50).all()
    
    return [
        {
            "id": inc.id,
            "started_at": inc.started_at,
            "resolved_at": inc.resolved_at,
            "duration": inc.duration,
            "reason": inc.reason
        } for inc in incidents
    ]

@router.put("/{monitor_id}")
def update_monitor(
    monitor_id: int,
    monitor_update: MonitorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    monitor = db.query(Website).filter(Website.id == monitor_id).first()
    if not monitor or (current_user.role.value != "admin" and monitor.owner_id != current_user.id):
        raise HTTPException(status_code=404, detail="Monitor not found")

    if monitor_update.url is not None:
        monitor.url = monitor_update.url
    if monitor_update.friendly_name is not None:
        monitor.name = monitor_update.friendly_name
    if monitor_update.interval is not None:
        monitor.check_interval = monitor_update.interval
    if monitor_update.region is not None:
        monitor.region = monitor_update.region
    if monitor_update.notifications is not None:
        monitor.notifications = monitor_update.notifications
    if monitor_update.timeout is not None:
        monitor.timeout = monitor_update.timeout
    if monitor_update.keyword is not None:
        monitor.keyword = monitor_update.keyword
    if monitor_update.ssl_check is not None:
        monitor.ssl_check = 1 if monitor_update.ssl_check else 0
    if monitor_update.redirect_follow is not None:
        monitor.redirect_follow = 1 if monitor_update.redirect_follow else 0

    db.commit()
    return {"status": "success", "message": "Monitor updated successfully"}


@router.post("/{monitor_id}/toggle-pause")
def toggle_pause(
    monitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    monitor = db.query(Website).filter(Website.id == monitor_id).first()
    if not monitor or (current_user.role.value != "admin" and monitor.owner_id != current_user.id):
        raise HTTPException(status_code=404, detail="Monitor not found")
        
    if monitor.status == WebsiteStatus.PAUSED:
        monitor.status = WebsiteStatus.ACTIVE
    else:
        monitor.status = WebsiteStatus.PAUSED
        
    db.commit()
    db.refresh(monitor)
    return {"monitor_id": monitor.id, "status": monitor.status}


# ── PART 5: Test Notification ─────────────────────────────────────────────────
@router.post("/{monitor_id}/test-notification")
def test_notification(
    monitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from backend.services.email_service import send_test_notification
    from datetime import datetime

    monitor = db.query(Website).filter(Website.id == monitor_id).first()
    if not monitor or (current_user.role.value != "admin" and monitor.owner_id != current_user.id):
        raise HTTPException(status_code=404, detail="Monitor not found")

    timestamp = datetime.utcnow().strftime("%d %b %Y %H:%M:%S UTC")
    recipients = [current_user.email]

    # Also notify Super Admin (Rule 7)
    if current_user.role.value != "admin":
        admins = db.query(User).filter(User.role.in_(["admin", "ADMIN"])).all()
        for admin in admins:
            if admin.email not in recipients:
                recipients.append(admin.email)

    sent_to = []
    errors = []
    for email in recipients:
        owner_name = current_user.name if email == current_user.email else "Admin"
        ok, msg = send_test_notification(
            to_email=email,
            user_name=owner_name,
            monitor_name=monitor.name or monitor.url,
            monitor_url=monitor.url,
            timestamp=timestamp
        )
        if ok:
            sent_to.append(email)
        else:
            errors.append(f"{email}: {msg}")

    if sent_to:
        return {"status": "success", "message": f"Test notification sent to {', '.join(sent_to)}"}
    elif errors:
        # SMTP not configured is treated as a graceful warning, not a failure
        return {"status": "warning", "message": "SMTP not configured. Check your .env file to enable email alerts."}
    else:
        raise HTTPException(status_code=500, detail="Failed to send notifications")


# ── All Incidents (admin) / Own Incidents (user) ──────────────────────────────
@router.get("/all-incidents")
def list_all_incidents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.value == "admin":
        incidents = db.query(Incident).order_by(desc(Incident.started_at)).limit(200).all()
    else:
        # Only own monitors
        my_monitor_ids = [
            r.id for r in db.query(Website.id).filter(Website.owner_id == current_user.id).all()
        ]
        incidents = db.query(Incident).filter(
            Incident.monitor_id.in_(my_monitor_ids)
        ).order_by(desc(Incident.started_at)).limit(200).all()

    result = []
    for inc in incidents:
        monitor = db.query(Website).filter(Website.id == inc.monitor_id).first()
        owner = db.query(User).filter(User.id == inc.user_id).first() if inc.user_id else None
        result.append({
            "id": inc.id,
            "monitor_id": inc.monitor_id,
            "monitor_name": inc.monitor_name or (monitor.name if monitor else ""),
            "monitor_url": monitor.url if monitor else "",
            "user_name": owner.name if owner else "System",
            "previous_status": inc.previous_status or "up",
            "new_status": inc.new_status or "down",
            "started_at": inc.started_at,
            "resolved_at": inc.resolved_at,
            "duration_seconds": inc.duration_seconds or inc.duration,
            "reason": inc.reason
        })
    return result
