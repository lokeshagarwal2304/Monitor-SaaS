from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models.website import Website
from backend.models.check_result import CheckResult
from backend.models.user import User
from backend.schemas.website import WebsiteCreate, WebsiteResponse, WebsiteBulkImport
from backend.utils.dependencies import get_current_user

router = APIRouter(prefix="/websites", tags=["Websites"])

@router.get("/", response_model=List[WebsiteResponse])
def list_websites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.value == "admin":
        websites = db.query(Website).all()
    else:
        websites = db.query(Website).filter(Website.owner_id == current_user.id).all()
    
    # REAL DATA VISUALS: Attach last 24 checks to each website
    results = []
    for site in websites:
        # Fetch last 24 logs
        logs = db.query(CheckResult).filter(CheckResult.website_id == site.id).order_by(desc(CheckResult.checked_at)).limit(24).all()
        
        # Create simple history objects for the frontend
        history_data = [{"is_up": log.is_up, "response_time": log.response_time} for log in reversed(logs)]
        
        # Convert SQLAlchemy model to Pydantic model manually to attach history
        site_dict = WebsiteResponse.from_orm(site)
        site_dict.history = history_data
        results.append(site_dict)
        
    return results

@router.post("/", response_model=WebsiteResponse)
def add_website(
    website: WebsiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_site = Website(
        url=str(website.url),
        name=website.name,
        check_interval=website.check_interval,
        owner_id=current_user.id
    )
    db.add(new_site)
    db.commit()
    db.refresh(new_site)
    # Return empty history for new site
    res = WebsiteResponse.from_orm(new_site)
    res.history = []
    return res

# NEW: Bulk Import Endpoint
@router.post("/bulk")
def bulk_import_websites(
    payload: WebsiteBulkImport,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Split by lines or commas
    raw_urls = payload.urls.replace(",", "\n").split("\n")
    added_count = 0
    
    for raw_url in raw_urls:
        clean_url = raw_url.strip()
        if not clean_url: continue
        
        if not clean_url.startswith(('http://', 'https://')):
            clean_url = 'https://' + clean_url
            
        # Check duplicate
        exists = db.query(Website).filter(Website.url == clean_url, Website.owner_id == current_user.id).first()
        if not exists:
            new_site = Website(
                url=clean_url,
                name=clean_url.split("//")[-1], # Use domain as name
                check_interval=5,
                owner_id=current_user.id
            )
            db.add(new_site)
            added_count += 1
            
    db.commit()
    return {"message": f"Successfully imported {added_count} websites"}

@router.delete("/{website_id}")
def delete_website(
    website_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    site = db.query(Website).filter(Website.id == website_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    
    if current_user.role.value != "admin" and site.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    db.delete(site)
    db.commit()
    return {"message": "Deleted"}