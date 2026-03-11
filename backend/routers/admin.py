from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models.user import User
from backend.models.check_result import CheckResult
from backend.utils.dependencies import get_current_admin_user
from backend.schemas.user import UserResponse

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    # Requires get_current_admin_user dependency check
    return db.query(User).all()

@router.get("/logs", summary="Get all monitoring logs (Admin only)")
def get_all_logs(db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    logs = db.query(CheckResult).order_by(desc(CheckResult.checked_at)).limit(100).all()
    return logs