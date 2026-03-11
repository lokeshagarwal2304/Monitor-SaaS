from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, case, and_

from backend.database import get_db
from backend.models.check_result import CheckResult
from backend.models.website import Website
from backend.models.user import User
from backend.utils.dependencies import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/incidents")
def get_recent_incidents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get user's websites (or all if admin)
    if current_user.role.value == "admin":
        user_websites = db.query(Website.id).all()
        website_ids = [w.id for w in user_websites]
    else:
        user_websites = db.query(Website.id).filter(Website.owner_id == current_user.id).all()
        website_ids = [w.id for w in user_websites]
    
    if not website_ids:
        return []
    
    # Fetch the 20 most recent DOWN checks for user's websites
    incidents = db.query(CheckResult).filter(
        and_(
            CheckResult.is_up == False,
            CheckResult.website_id.in_(website_ids)
        )
    ).order_by(desc(CheckResult.checked_at)).limit(20).all()
    
    formatted_incidents = []
    for inc in incidents:
        # Get website info
        website = db.query(Website).filter(Website.id == inc.website_id).first()
        website_name = website.name if website else "Unknown"
        website_url = website.url if website else "Unknown"
        
        # Create meaningful message
        error_msg = inc.error_message or f"HTTP {inc.status_code}" if inc.status_code else "Connection Failed"
        message = f"{website_name} ({website_url}) is DOWN. {error_msg}"
        
        formatted_incidents.append({
            "id": inc.id,
            "website_id": inc.website_id,
            "website_name": website_name,
            "website_url": website_url,
            "time": inc.checked_at.strftime("%Y-%m-%d %H:%M:%S") if inc.checked_at else "Unknown",
            "status": "DOWN",
            "status_code": inc.status_code,
            "error": inc.error_message,
            "message": message
        })
    return formatted_incidents

@router.get("/common-errors")
def get_common_errors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get user's websites (or all if admin)
    if current_user.role.value == "admin":
        user_websites = db.query(Website.id).all()
        website_ids = [w.id for w in user_websites]
    else:
        user_websites = db.query(Website.id).filter(Website.owner_id == current_user.id).all()
        website_ids = [w.id for w in user_websites]
    
    if not website_ids:
        return []
    
    # Group and count error messages for user's websites
    common_errors = db.query(
        CheckResult.error_message.label('error'), 
        func.count(CheckResult.error_message).label('count')
    ).filter(
        and_(
            CheckResult.is_up == False,
            CheckResult.error_message != None,
            CheckResult.website_id.in_(website_ids)
        )
    ).group_by(CheckResult.error_message).order_by(desc('count')).limit(10).all()
    
    return [{"error": e.error or "Unknown Error", "count": e.count} for e in common_errors]

@router.get("/recent")
def get_recent_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent notifications including both UP and DOWN status changes"""
    # Get user's websites (or all if admin)
    if current_user.role.value == "admin":
        user_websites = db.query(Website).all()
    else:
        user_websites = db.query(Website).filter(Website.owner_id == current_user.id).all()
    
    website_ids = [w.id for w in user_websites]
    if not website_ids:
        return []
    
    # Get recent check results (both UP and DOWN) for user's websites
    recent_checks = db.query(CheckResult).filter(
        CheckResult.website_id.in_(website_ids)
    ).order_by(desc(CheckResult.checked_at)).limit(50).all()
    
    notifications = []
    for check in recent_checks:
        website = next((w for w in user_websites if w.id == check.website_id), None)
        if not website:
            continue
            
        status_text = "UP" if check.is_up else "DOWN"
        status_emoji = "✅" if check.is_up else "🔴"
        
        if check.is_up:
            message = f"{status_emoji} {website.name} is back UP"
        else:
            error_msg = check.error_message or f"HTTP {check.status_code}" if check.status_code else "Connection Failed"
            message = f"{status_emoji} {website.name} is DOWN - {error_msg}"
        
        notifications.append({
            "id": check.id,
            "website_id": check.website_id,
            "website_name": website.name,
            "website_url": website.url,
            "time": check.checked_at.strftime("%Y-%m-%d %H:%M:%S") if check.checked_at else "Unknown",
            "status": status_text,
            "is_up": check.is_up,
            "message": message,
            "response_time": check.response_time
        })
    
    return notifications