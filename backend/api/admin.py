from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.user import User, UserStatus, UserRole
from backend.schemas.user import UserResponse, UserUpdate
from backend.services.auth_service import get_password_hash
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


@router.patch("/users/{user_id}/password", response_model=UserResponse)
def admin_reset_password(user_id: str, payload: dict = Body(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    """Admin sets a new password for a user (e.g. after a forgot-password request)."""
    new_pw = (payload or {}).get("new_password", "")
    if len(new_pw) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = get_password_hash(new_pw)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    if user.username == "admin":
        raise HTTPException(status_code=400, detail="The default admin account cannot be deleted")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}