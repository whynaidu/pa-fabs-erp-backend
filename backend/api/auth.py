from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User, UserRole, UserStatus
from backend.schemas.user import UserCreate, UserLogin, Token, UserResponse
from backend.services.auth_service import verify_password, get_password_hash, create_access_token
from backend.api.deps import get_current_user
from datetime import timedelta
from backend.config import settings
import uuid

router = APIRouter(tags=["Authentication"])


@router.post("/forgot-password")
def forgot_password(payload: dict = Body(...), db: Session = Depends(get_db)):
    """Self-service reset: the account is verified by matching BOTH username and
    email (no mail server in this dev env), then the new password is set."""
    username = (payload or {}).get("username", "").strip()
    email = (payload or {}).get("email", "").strip()
    new_pw = (payload or {}).get("new_password", "")
    if not username or not email or not new_pw:
        raise HTTPException(status_code=400, detail="Username, email and new password are required")
    if len(new_pw) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    user = db.query(User).filter(User.username == username, User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account matches that username + email")
    user.password_hash = get_password_hash(new_pw)
    db.commit()
    return {"message": "Password reset successful — you can sign in now"}


@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = get_password_hash(user.password)
    db_user = User(
        id=f"user_{uuid.uuid4().hex}",
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        username=user.username,
        password_hash=hashed_password,
        role=user.role,
        department=user.department,
        is_approved=False,
        status=UserStatus.PENDING
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_credentials.username).first()
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        requested_role = UserRole(user_credentials.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role",
        )
    if user.role != requested_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role mismatch",
        )

    if not user.is_approved or user.status != UserStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not approved",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user