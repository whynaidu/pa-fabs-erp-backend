from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime, timezone
from backend.database import get_db
from backend.models.user import User
from backend.models.loom import Loom, LoomStatus
from backend.models.loom_allocation import LoomAllocation, AllocationStatus
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
        allocation_date=datetime.now(timezone.utc),
        expected_done=allocation.expected_done,
        submitted_by=current_user.id
    )

    db.add(new_allocation)

    loom.status = LoomStatus.OCCUPIED
    loom.current_po = allocation.po_number
    loom.current_cycle = inward.cycle_number
    loom.current_beam = allocation.beam_id
    loom.allocated_by = current_user.id
    loom.allocated_at = datetime.now(timezone.utc)

    beam.status = BeamStatus.ALLOCATED

    db.commit()
    db.refresh(new_allocation)
    return new_allocation


@router.get("/allocations", response_model=List[LoomAllocationResponse])
def list_allocations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(LoomAllocation).order_by(LoomAllocation.created_at.desc()).all()


@router.get("/allocations/po/{po_number}/cycle/{cycle_number}", response_model=List[LoomAllocationResponse])
def allocations_for_cycle(po_number: str, cycle_number: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(LoomAllocation).filter(
        LoomAllocation.po_number == po_number, LoomAllocation.cycle_number == cycle_number
    ).all()


@router.get("/allocations/{alloc_id}", response_model=LoomAllocationResponse)
def get_allocation(alloc_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    alloc = db.query(LoomAllocation).filter(LoomAllocation.id == alloc_id).first()
    if not alloc:
        raise HTTPException(status_code=404, detail="Allocation not found")
    return alloc


@router.patch("/allocations/{alloc_id}/status", response_model=LoomAllocationResponse)
def update_allocation_status(alloc_id: str, status: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update an allocation's status (active / completed / cancelled). Putting it
    on hold parks the loom (on-hold); reactivating re-occupies it. The loom is
    only freed by a delivery, never here."""
    alloc = db.query(LoomAllocation).filter(LoomAllocation.id == alloc_id).first()
    if not alloc:
        raise HTTPException(status_code=404, detail="Allocation not found")
    try:
        new_status = AllocationStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status (active/completed/cancelled)")
    alloc.status = new_status
    loom = db.query(Loom).filter(Loom.loom_number == alloc.loom_number).first()
    if loom and loom.status != LoomStatus.FREE:
        if status == "hold" or new_status == AllocationStatus.CANCELLED:
            loom.status = LoomStatus.ON_HOLD
        elif new_status == AllocationStatus.ACTIVE:
            loom.status = LoomStatus.OCCUPIED
    db.commit()
    db.refresh(alloc)
    return alloc


@router.get("/{loom_number}", response_model=LoomResponse)
def get_loom(loom_number: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    loom = db.query(Loom).filter(Loom.loom_number == loom_number).first()
    if not loom:
        raise HTTPException(status_code=404, detail="Loom not found")
    return loom