from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from backend.database import get_db
from backend.models.user import User
from backend.models.outward import OutwardEntry
from backend.models.inward import InwardEntry
from backend.schemas.outward import OutwardCreate, OutwardResponse
from backend.api.deps import get_current_user, require_po_access

router = APIRouter(prefix="/outwards", tags=["Outward Entries"])


@router.post("/", response_model=OutwardResponse)
def create_outward(
    outward: OutwardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inward = db.query(InwardEntry).filter(
        InwardEntry.po_number == outward.po_number
    ).order_by(InwardEntry.cycle_number.desc()).first()

    if not inward:
        raise HTTPException(status_code=404, detail="No inward entry found for this PO")

    new_outward = OutwardEntry(
        id=f"outward_{uuid.uuid4().hex}",
        po_number=outward.po_number,
        cycle_number=inward.cycle_number,
        process_type=outward.process_type,
        operator_name=outward.operator_name,
        warp_count=outward.warp_count,
        warp_colour=outward.warp_colour,
        warp_metres=outward.warp_metres,
        warp_cones=outward.warp_cones,
        weft_count=outward.weft_count,
        weft_colour=outward.weft_colour,
        weft_kg=outward.weft_kg,
        weft_cones=outward.weft_cones,
        beams_expected=outward.beams_expected,
        outward_date=outward.outward_date,
        expected_return=outward.expected_return,
        is_done=outward.is_done,
        submitted_by=current_user.id
    )

    db.add(new_outward)
    db.commit()
    db.refresh(new_outward)
    return new_outward


@router.get("/", response_model=List[OutwardResponse])
def list_outwards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        outwards = db.query(OutwardEntry).all()
    else:
        outwards = db.query(OutwardEntry).filter(
            OutwardEntry.submitted_by == current_user.id
        ).all()
    return outwards


@router.get("/po/{po_number}/cycle/{cycle_number}", response_model=List[OutwardResponse])
def outwards_for_cycle(po_number: str, cycle_number: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_po_access(po_number, db, current_user)
    return db.query(OutwardEntry).filter(
        OutwardEntry.po_number == po_number, OutwardEntry.cycle_number == cycle_number
    ).all()


@router.get("/{outward_id}", response_model=OutwardResponse)
def get_outward(outward_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    outward = db.query(OutwardEntry).filter(OutwardEntry.id == outward_id).first()
    if not outward:
        raise HTTPException(status_code=404, detail="Outward entry not found")
    return outward


@router.patch("/{outward_id}/done", response_model=OutwardResponse)
def mark_outward_done(outward_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    outward = db.query(OutwardEntry).filter(OutwardEntry.id == outward_id).first()
    if not outward:
        raise HTTPException(status_code=404, detail="Outward entry not found")
    outward.is_done = True
    db.commit()
    db.refresh(outward)
    return outward