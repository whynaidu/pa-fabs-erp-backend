from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import func
from backend.database import get_db
from backend.models.user import User
from backend.models.manufacturing import ManufacturingLog
from backend.models.loom import Loom
from backend.models.po import PurchaseOrder
from backend.schemas.manufacturing import ManufacturingCreate, ManufacturingResponse
from backend.api.deps import get_current_user
from datetime import datetime

router = APIRouter(prefix="/manufacturing", tags=["Manufacturing"])


@router.post("/", response_model=ManufacturingResponse)
def create_manufacturing_log(
    manufacturing: ManufacturingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    loom = db.query(Loom).filter(Loom.loom_number == manufacturing.loom_number).first()
    if not loom:
        raise HTTPException(status_code=404, detail="Loom not found")

    if loom.status != "occupied":
        raise HTTPException(status_code=400, detail="Loom is not occupied")

    prev_total = db.query(func.sum(ManufacturingLog.metres_today)).filter(
        ManufacturingLog.loom_number == manufacturing.loom_number
    ).scalar() or 0

    new_total = prev_total + manufacturing.metres_today
    balance = None

    if loom.current_po:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == loom.current_po).first()
        if po:
            balance = float(po.order_qty) - new_total

    new_log = ManufacturingLog(
        id=f"mfg_{hash(manufacturing.loom_number + str(manufacturing.log_date))}",
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
        allocation = db.query(backend.models.loom_allocation.LoomAllocation).filter(
            backend.models.loom_allocation.LoomAllocation.loom_number == manufacturing.loom_number,
            backend.models.loom_allocation.LoomAllocation.status == "active"
        ).first()
        if allocation:
            allocation.status = "completed"
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


@router.get("/{loom_number}", response_model=List[ManufacturingResponse])
def get_manufacturing_for_loom(loom_number: int, db: Session = Depends(get_db)):
    logs = db.query(ManufacturingLog).filter(
        ManufacturingLog.loom_number == loom_number
    ).order_by(ManufacturingLog.log_date.desc()).all()
    return logs