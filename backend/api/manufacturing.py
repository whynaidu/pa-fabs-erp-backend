from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import func
from backend.database import get_db
from backend.models.user import User
from backend.models.manufacturing import ManufacturingLog
from backend.models.loom import Loom, LoomStatus
from backend.models.loom_allocation import LoomAllocation, AllocationStatus
from backend.models.inventory import Inventory
from backend.models.po import PurchaseOrder
from backend.schemas.manufacturing import ManufacturingCreate, ManufacturingResponse
from backend.api.deps import get_current_user, require_po_access
from datetime import datetime
import uuid

router = APIRouter(prefix="/manufacturing", tags=["Manufacturing"])


def _ensure_inventory_from_log(db: Session, log: ManufacturingLog, user_id: str) -> None:
    """When weaving is marked done, receive the woven fabric into inventory so the
    cycle becomes deliverable. Idempotent per (po, cycle, loom); uses fabric_metres
    if given, else the day's metres. A separate explicit inventory entry can still
    override grade/received-by."""
    metres = log.fabric_metres if log.fabric_metres is not None else log.metres_today
    if not metres or float(metres) <= 0:
        return
    exists = db.query(Inventory).filter(
        Inventory.po_number == log.po_number,
        Inventory.cycle_number == log.cycle_number,
        Inventory.loom_number == log.loom_number,
    ).first()
    if exists:
        return
    db.add(Inventory(
        id=f"inv_{uuid.uuid4().hex}",
        po_number=log.po_number,
        cycle_number=log.cycle_number,
        loom_number=log.loom_number,
        beam_id=log.beam_id,
        fabric_metres=metres,
        received_date=log.received_date or log.log_date,
        received_by=log.received_by or "system",
        submitted_by=user_id,
    ))


@router.post("/", response_model=ManufacturingResponse)
def create_manufacturing_log(
    manufacturing: ManufacturingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    loom = db.query(Loom).filter(Loom.loom_number == manufacturing.loom_number).first()
    if not loom:
        raise HTTPException(status_code=404, detail="Loom not found")

    if loom.status != LoomStatus.OCCUPIED:
        raise HTTPException(status_code=400, detail="Loom is not occupied")

    prev_total = db.query(func.sum(ManufacturingLog.metres_today)).filter(
        ManufacturingLog.loom_number == manufacturing.loom_number
    ).scalar() or 0

    new_total = float(prev_total) + float(manufacturing.metres_today)
    balance = None

    if loom.current_po:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == loom.current_po).first()
        if po:
            balance = float(po.order_qty) - new_total

    new_log = ManufacturingLog(
        id=f"mfg_{uuid.uuid4().hex}",
        po_number=loom.current_po or "",
        cycle_number=loom.current_cycle or 1,
        loom_number=manufacturing.loom_number,
        beam_id=loom.current_beam,
        metres_today=manufacturing.metres_today,
        fabric_metres=manufacturing.fabric_metres,
        total_manufactured=new_total,
        balance_qty=balance,
        operator_name=manufacturing.operator_name,
        received_date=manufacturing.received_date,
        received_by=manufacturing.received_by,
        remarks=manufacturing.remarks,
        is_done=manufacturing.is_done,
        log_date=manufacturing.log_date,
        submitted_by=current_user.id
    )

    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    if manufacturing.is_done:
        allocation = db.query(LoomAllocation).filter(
            LoomAllocation.loom_number == manufacturing.loom_number,
            LoomAllocation.status == AllocationStatus.ACTIVE
        ).first()
        if allocation:
            allocation.status = AllocationStatus.COMPLETED
        _ensure_inventory_from_log(db, new_log, current_user.id)
        db.commit()

    return new_log


@router.get("/", response_model=List[ManufacturingResponse])
def list_manufacturing_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        logs = db.query(ManufacturingLog).order_by(ManufacturingLog.log_date.desc()).all()
    else:
        logs = db.query(ManufacturingLog).filter(
            ManufacturingLog.submitted_by == current_user.id
        ).order_by(ManufacturingLog.log_date.desc()).all()
    return logs


@router.get("/po/{po_number}/cycle/{cycle_number}", response_model=List[ManufacturingResponse])
def manufacturing_for_cycle(po_number: str, cycle_number: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_po_access(po_number, db, current_user)
    return db.query(ManufacturingLog).filter(
        ManufacturingLog.po_number == po_number, ManufacturingLog.cycle_number == cycle_number
    ).order_by(ManufacturingLog.log_date.desc()).all()


@router.patch("/{mfg_id}/done", response_model=ManufacturingResponse)
def mark_manufacturing_done(mfg_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Mark weaving complete on this log's loom. The loom allocation is closed,
    but the loom stays Occupied until the delivery for the PO+cycle is saved."""
    log = db.query(ManufacturingLog).filter(ManufacturingLog.id == mfg_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Manufacturing log not found")
    require_po_access(log.po_number, db, current_user)
    log.is_done = True
    allocation = db.query(LoomAllocation).filter(
        LoomAllocation.loom_number == log.loom_number,
        LoomAllocation.status == AllocationStatus.ACTIVE,
    ).first()
    if allocation:
        allocation.status = AllocationStatus.COMPLETED
    _ensure_inventory_from_log(db, log, current_user.id)
    db.commit()
    db.refresh(log)
    return log


@router.get("/loom/{loom_number}", response_model=List[ManufacturingResponse])
def get_manufacturing_for_loom(loom_number: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logs = db.query(ManufacturingLog).filter(
        ManufacturingLog.loom_number == loom_number
    ).order_by(ManufacturingLog.log_date.desc()).all()
    return logs