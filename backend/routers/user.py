from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.utils.dependencies import get_current_user

router = APIRouter(prefix="/user", tags=["User"])

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    profile_image: Optional[str] = None

@router.get("/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "profile_image": current_user.profile_image
    }

@router.put("/profile")
def update_profile(
    data: UserProfileUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if data.name is not None:
        current_user.name = data.name
        
    if data.profile_image is not None:
        current_user.profile_image = data.profile_image
        
    # Only admin can change roles
    if data.role is not None and current_user.role == UserRole.ADMIN:
        try:
            current_user.role = UserRole(data.role)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role")
            
    # Email updates might need extra logic to avoid duplicate, but keeping simple for now
    if data.email is not None and data.email != current_user.email:
        # Check if email is available
        existing = db.query(User).filter(User.email == data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already taken")
        # Only admin or self can update email, we already checked self or it's admin? Wait, self can update their own email.
        current_user.email = data.email
        
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "Profile updated successfully",
        "profile": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role.value if hasattr(current_user.role, 'value') else current_user.role,
            "profile_image": current_user.profile_image
        }
    }
