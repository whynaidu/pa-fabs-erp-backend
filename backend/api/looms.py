from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime
from backend.database import get_db
from backend.models.user import User
from backend.models.loom import Loom, LoomStatus
from backend.models.loom_allocation import LoomAllocation
from backend.models.inward import InwardEntry
from backend.models.beam import Beam, BeamStatus
from backend.schemas.loom import LoomResponse, LoomAllocationRequest, LoomAllocationResponse
from backend.api.deps import get_current_user

router = APIRouter(prefix="/looms", tags=["Looms"])


@router.get("/", response_model=List[LoomResponse])
def list_looms(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    looms = db.query(Loom).order_by(Loom.loom_number).all()
    return looms


@router.get("/free", response_model=List[LoomResponse])
def list_free_looms(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    looms = db.query(Loom).filter(Loom.status == LoomStatus.FREE).order_by(Loom.loom_number).all()
    return looms


@router.post("/allocate", response_model=LoomAllocationResponse)
def allocate_loom(
    allocation: LoomAllocationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    loom = db.query(Loom).filter(Loom.loom_number == allocation.loom_number).first()
    if not loom:
        raise HTTPException(status_code=404, detail="Loom not found")

    if loom.status != LoomStatus.FREE:
        raise HTTPException(status_code=400, detail=f"Loom {allocation.loom_number} is not free")

    inward = db.query(InwardEntry).filter(
        InwardEntry.po_number == allocation.po_number
    ).order_by(InwardEntry.cycle_number.desc()).first()

    if not inward:
        raise HTTPException(status_code=404, detail="No inward entry found for this PO")

    beam = db.query(Beam).filter(
        Beam.beam_number == allocation.beam_id,
        Beam.po_number == allocation.po_number,
        Beam.cycle_number == inward.cycle_number
    ).first()

    if not beam:
        raise HTTPException(status_code=404, detail="Beam not found")

    new_allocation = LoomAllocation(
        id=f"alloc_{uuid.uuid4().hex}",
        po_number=allocation.po_number,
        cycle_number=inward.cycle_number,
        beam_id=allocation.beam_id,
        loom_number=allocation.loom_number,
        weft_details=allocation.weft_details,
        allocation_date=datetime.utcnow(),
        expected_done=allocation.expected_done,
        submitted_by=current_user.id
    )

    db.add(new_allocation)

    loom.status = LoomStatus.OCCUPIED
    loom.current_po = allocation.po_number
    loom.current_cycle = inward.cycle_number
    loom.current_beam = allocation.beam_id
    loom.allocated_by = current_user.username
    loom.allocated_at = datetime.utcnow()

    beam.status = BeamStatus.ALLOCATED

    db.commit()
    db.refresh(new_allocation)
    return new_allocation


@router.get("/allocations", response_model=List[LoomAllocationResponse])
def list_allocations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(LoomAllocation).order_by(LoomAllocation.created_at.desc()).all()


@router.get("/{loom_number}", response_model=LoomResponse)
def get_loom(loom_number: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    loom = db.query(Loom).filter(Loom.loom_number == loom_number).first()
    if not loom:
        raise HTTPException(status_code=404, detail="Loom not found")
    return loom