from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import uuid
import json
from backend.database import get_db
from backend.models.user import User
from backend.models.inward import InwardEntry
from backend.models.po import PurchaseOrder, POStatus
from backend.models.delivery import Delivery
from backend.schemas.inward import InwardCreate, InwardResponse
from backend.api.deps import get_current_user, require_po_access, get_current_admin, admin_partial_update

router = APIRouter(prefix="/inwards", tags=["Inward Entries"])


@router.post("/", response_model=InwardResponse)
def create_inward(
    inward: InwardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == inward.po_number).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")

    max_cycle = db.query(func.max(InwardEntry.cycle_number)).filter(
        InwardEntry.po_number == inward.po_number
    ).scalar() or 0

    if max_cycle > 0:
        prev_delivery = db.query(Delivery).filter(
            Delivery.po_number == inward.po_number,
            Delivery.cycle_number == max_cycle
        ).first()
        if not prev_delivery:
            raise HTTPException(
                status_code=400,
                detail=f"Previous cycle {max_cycle} delivery must be completed before starting new cycle"
            )

    new_inward = InwardEntry(
        id=f"inward_{uuid.uuid4().hex}",
        po_number=inward.po_number,
        cycle_number=max_cycle + 1,
        warp_count=inward.warp_count,
        warp_colour=inward.warp_colour,
        warp_kg=inward.warp_kg,
        warp_bundles=inward.warp_bundles,
        weft_count=inward.weft_count,
        weft_colour=inward.weft_colour,
        weft_kg=inward.weft_kg,
        weft_bundles=inward.weft_bundles,
        rm_number=inward.rm_number,
        cone_bag_count=inward.cone_bag_count,
        next_process=inward.next_process,
        location=inward.location,
        warp_rows=json.dumps([r.model_dump() for r in inward.warp_rows]) if inward.warp_rows else None,
        weft_rows=json.dumps([r.model_dump() for r in inward.weft_rows]) if inward.weft_rows else None,
        cost=inward.cost,
        received_by=inward.received_by,
        is_done=inward.is_done,
        entry_date=inward.entry_date,
        submitted_by=current_user.id
    )

    db.add(new_inward)
    db.commit()
    db.refresh(new_inward)

    po.status = POStatus.IN_PROGRESS
    db.commit()

    return new_inward


@router.get("/", response_model=List[InwardResponse])
def list_inwards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        inwards = db.query(InwardEntry).all()
    else:
        inwards = db.query(InwardEntry).filter(
            InwardEntry.submitted_by == current_user.id
        ).all()
    return inwards


@router.get("/po/{po_number}", response_model=List[InwardResponse])
def inwards_for_po(po_number: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_po_access(po_number, db, current_user)
    return db.query(InwardEntry).filter(InwardEntry.po_number == po_number).order_by(InwardEntry.cycle_number).all()


@router.get("/po/{po_number}/cycle/{cycle_number}", response_model=List[InwardResponse])
def inwards_for_cycle(po_number: str, cycle_number: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_po_access(po_number, db, current_user)
    return db.query(InwardEntry).filter(
        InwardEntry.po_number == po_number, InwardEntry.cycle_number == cycle_number
    ).all()


@router.get("/po/{po_number}/can-start")
def can_start_cycle(po_number: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Cycle guard: a new inward (cycle N+1) is allowed only when the previous
    cycle has a completed delivery. First cycle is always allowed."""
    require_po_access(po_number, db, current_user)
    max_cycle = db.query(func.max(InwardEntry.cycle_number)).filter(
        InwardEntry.po_number == po_number
    ).scalar() or 0
    if max_cycle == 0:
        return {"can_start": True, "next_cycle": 1, "reason": None}
    delivered = db.query(Delivery).filter(
        Delivery.po_number == po_number, Delivery.cycle_number == max_cycle
    ).first() is not None
    return {
        "can_start": delivered,
        "next_cycle": max_cycle + 1 if delivered else max_cycle,
        "reason": None if delivered else f"Cycle {max_cycle} delivery not complete",
    }


@router.get("/{inward_id}", response_model=InwardResponse)
def get_inward(inward_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    inward = db.query(InwardEntry).filter(InwardEntry.id == inward_id).first()
    if not inward:
        raise HTTPException(status_code=404, detail="Inward entry not found")
    require_po_access(inward.po_number, db, current_user)
    return inward


@router.patch("/{inward_id}/done", response_model=InwardResponse)
def mark_inward_done(inward_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    inward = db.query(InwardEntry).filter(InwardEntry.id == inward_id).first()
    if not inward:
        raise HTTPException(status_code=404, detail="Inward entry not found")
    require_po_access(inward.po_number, db, current_user)
    inward.is_done = True
    db.commit()
    db.refresh(inward)
    return inward


@router.put("/{inward_id}", response_model=InwardResponse)
def update_inward(inward_id: str, payload: dict = Body(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    # Whitelisted admin edit — scalar fields only (PO/cycle and warp/weft JSON rows immutable here).
    inward = db.query(InwardEntry).filter(InwardEntry.id == inward_id).first()
    if not inward:
        raise HTTPException(status_code=404, detail="Inward entry not found")
    return admin_partial_update(inward, payload,
        {"location", "rm_number", "cone_bag_count", "cost", "received_by", "entry_date", "is_done"}, db)


@router.delete("/{inward_id}")
def delete_inward(inward_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    inward = db.query(InwardEntry).filter(InwardEntry.id == inward_id).first()
    if not inward:
        raise HTTPException(status_code=404, detail="Inward entry not found")
    db.delete(inward)
    db.commit()
    return {"message": "Inward entry deleted"}