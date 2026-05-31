from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import uuid
from backend.database import get_db
from backend.models.user import User
from backend.models.return_entry import ReturnEntry
from backend.models.inward import InwardEntry
from backend.models.beam import Beam, BeamStatus
from backend.schemas.return_entry import ReturnCreate, ReturnResponse
from backend.api.deps import get_current_user, require_po_access

router = APIRouter(prefix="/returns", tags=["Return Entries"])


@router.post("/", response_model=ReturnResponse)
def create_return(
    return_data: ReturnCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inward = db.query(InwardEntry).filter(
        InwardEntry.po_number == return_data.po_number
    ).order_by(InwardEntry.cycle_number.desc()).first()

    if not inward:
        raise HTTPException(status_code=404, detail="No inward entry found for this PO")

    new_return = ReturnEntry(
        id=f"return_{uuid.uuid4().hex}",
        po_number=return_data.po_number,
        cycle_number=inward.cycle_number,
        return_type=return_data.return_type,
        beams_returned=return_data.beams_returned,
        warp_metres=return_data.warp_metres,
        weft_metres=return_data.weft_metres,
        return_cones=return_data.return_cones,
        quality_grade=return_data.quality_grade,
        operator_name=return_data.operator_name,
        receiver_name=return_data.receiver_name,
        return_date=return_data.return_date,
        remarks=return_data.remarks,
        submitted_by=current_user.id
    )

    # A warping return auto-generates beams. beam_number is globally unique (it is
    # the FK target for loom allocations), so the running number is global, not
    # per-cycle. The return + its beams are committed together (one transaction) so
    # a beam-numbering collision can never leave an orphaned return; retry on the
    # rare race (rollback expunges the pending rows, so re-add each attempt).
    beam_entries = list(return_data.beam_entries) if (
        return_data.return_type == "warping_return" and return_data.beam_entries) else []
    for attempt in range(5):
        db.add(new_return)
        if beam_entries:
            base = db.query(Beam).count()
            for idx, beam_entry in enumerate(beam_entries):
                db.add(Beam(
                    id=f"beam_{uuid.uuid4().hex}",
                    po_number=return_data.po_number,
                    cycle_number=inward.cycle_number,
                    return_entry_id=new_return.id,
                    beam_number=f"B{str(base + idx + 1).zfill(3)}",
                    beam_metres=beam_entry.beam_metres,
                    quality_grade=return_data.quality_grade,
                    status=BeamStatus.AVAILABLE,
                ))
        try:
            db.commit()
            break
        except IntegrityError:
            db.rollback()
            if attempt == 4:
                raise HTTPException(status_code=409, detail="Could not allocate beam numbers; retry")

    db.refresh(new_return)
    return new_return


@router.get("/", response_model=List[ReturnResponse])
def list_returns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        returns = db.query(ReturnEntry).all()
    else:
        returns = db.query(ReturnEntry).filter(
            ReturnEntry.submitted_by == current_user.id
        ).all()
    return returns


@router.get("/po/{po_number}/cycle/{cycle_number}", response_model=List[ReturnResponse])
def returns_for_cycle(po_number: str, cycle_number: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_po_access(po_number, db, current_user)
    return db.query(ReturnEntry).filter(
        ReturnEntry.po_number == po_number, ReturnEntry.cycle_number == cycle_number
    ).all()


@router.get("/{return_id}", response_model=ReturnResponse)
def get_return(return_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return_entry = db.query(ReturnEntry).filter(ReturnEntry.id == return_id).first()
    if not return_entry:
        raise HTTPException(status_code=404, detail="Return entry not found")
    require_po_access(return_entry.po_number, db, current_user)
    return return_entry