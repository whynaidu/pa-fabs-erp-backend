from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.user import User, UserStatus, UserRole
from backend.schemas.user import UserResponse, UserUpdate
from backend.api.deps import get_current_admin

router = APIRouter(tags=["Admin"])


@router.get("/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    users = db.query(User).all()
    return users


@router.put("/users/{user_id}/approve", response_model=UserResponse)
def approve_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_approved = True
    user.status = UserStatus.APPROVED
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}/reject", response_model=UserResponse)
def reject_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_approved = False
    user.status = UserStatus.REJECTED
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(user_id: str, role: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        user.role = UserRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role (admin/user)")
    db.commit()
    db.refresh(user)
    return user