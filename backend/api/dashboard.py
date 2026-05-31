from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from backend.database import get_db
from backend.models.user import User, UserStatus
from backend.models.po import PurchaseOrder, POStatus
from backend.models.inward import InwardEntry
from backend.models.outward import OutwardEntry
from backend.models.return_entry import ReturnEntry
from backend.models.beam import Beam
from backend.models.loom import Loom, LoomStatus
from backend.models.loom_allocation import LoomAllocation
from backend.models.manufacturing import ManufacturingLog
from backend.models.inventory import Inventory
from backend.models.delivery import Delivery
from backend.api.deps import get_current_admin
from backend.schemas.loom import LoomResponse
from typing import List

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    looms = db.query(Loom).all()
    status_counts = {}
    for s in POStatus:
        status_counts[s.value] = db.query(PurchaseOrder).filter(PurchaseOrder.status == s).count()
    total_metres = float(db.query(func.coalesce(func.sum(ManufacturingLog.metres_today), 0)).scalar() or 0)
    return {
        "counts": {
            "purchase_orders": db.query(PurchaseOrder).count(),
            "inwards": db.query(InwardEntry).count(),
            "outwards": db.query(OutwardEntry).count(),
            "returns": db.query(ReturnEntry).count(),
            "beams": db.query(Beam).count(),
            "allocations": db.query(LoomAllocation).count(),
            "manufacturing_logs": db.query(ManufacturingLog).count(),
            "inventory": db.query(Inventory).count(),
            "deliveries": db.query(Delivery).count(),
            "users_pending": db.query(User).filter(User.status == UserStatus.PENDING).count(),
        },
        "po_status": status_counts,
        "looms": {
            "total": len(looms),
            "free": sum(1 for l in looms if l.status == LoomStatus.FREE),
            "occupied": sum(1 for l in looms if l.status == LoomStatus.OCCUPIED),
            "on_hold": sum(1 for l in looms if l.status == LoomStatus.ON_HOLD),
        },
        "total_metres_produced": total_metres,
    }


@router.get("/looms", response_model=List[LoomResponse])
def admin_looms(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    return db.query(Loom).order_by(Loom.loom_number).all()


@router.get("/warehouse")
def admin_warehouse(po_number: Optional[str] = None, cycle_number: Optional[int] = None,
                    db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    def q(model):
        query = db.query(model)
        if po_number:
            query = query.filter(model.po_number == po_number)
        if cycle_number is not None:
            query = query.filter(model.cycle_number == cycle_number)
        return query.all()
    serialize = lambda rows: [
        {c.name: getattr(r, c.name) for c in r.__table__.columns} for r in rows
    ]
    return {
        "inwards": serialize(q(InwardEntry)),
        "outwards": serialize(q(OutwardEntry)),
        "returns": serialize(q(ReturnEntry)),
    }


@router.get("/manufacturing")
def admin_manufacturing(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    rows = []
    for po in db.query(PurchaseOrder).all():
        produced = float(db.query(func.coalesce(func.sum(ManufacturingLog.metres_today), 0)).filter(
            ManufacturingLog.po_number == po.po_number).scalar() or 0)
        order_qty = float(po.order_qty or 0)
        rows.append({
            "po_number": po.po_number,
            "order_qty": order_qty,
            "produced": produced,
            "balance": order_qty - produced,
            "completion_pct": round(produced / order_qty * 100, 1) if order_qty else 0,
            "status": po.status.value if po.status else None,
        })
    return rows


@router.get("/delivery")
def admin_delivery(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    rows = db.query(Delivery).order_by(Delivery.created_at.desc()).all()
    return [{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in rows]
