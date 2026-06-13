from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User, UserRole, UserStatus
from backend.services.auth_service import decode_access_token
from typing import Optional

security = HTTPBearer()


def require_po_access(po_number: str, db: Session, current_user: User) -> None:
    """Non-admins may only access POs they own (spec: 'Users see own POs only').
    Admins have full visibility. Unknown POs are left to the endpoint's own 404."""
    if current_user.role == UserRole.ADMIN:
        return
    from backend.models.po import PurchaseOrder
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_number).first()
    if po is not None and po.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this PO")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_approved or user.status != UserStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not approved",
        )
    return user


def admin_partial_update(obj, payload: dict, allowed: set, db: Session):
    """Apply only whitelisted scalar fields from an admin edit. Derived/JSON state
    (totals, pieces_data, warp/weft rows, PO+cycle identity) is intentionally NOT
    editable here — keeps admin corrections safe and side-effect free."""
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Body must be an object")
    for key, value in payload.items():
        if key in allowed:
            setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if credentials is None:
        return None
    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        if payload is None:
            return None
        username: str = payload.get("sub")
        if username is None:
            return None
        user = db.query(User).filter(User.username == username).first()
        return user
    except:
        return None