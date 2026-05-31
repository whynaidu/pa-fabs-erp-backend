from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.user import User
from backend.models.inward import InwardEntry
from backend.models.po import PurchaseOrder
from backend.models.delivery import Delivery
from backend.schemas.inward import InwardCreate, InwardResponse
from backend.api.deps import get_current_user

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
        id=f"inward_{hash(inward.po_number + str(max_cycle + 1))}",
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
        cost=inward.cost,
        received_by=inward.received_by,
        is_done=inward.is_done,
        entry_date=inward.entry_date,
        submitted_by=current_user.id
    )

    db.add(new_inward)
    db.commit()
    db.refresh(new_inward)

    po.status = "in_progress"
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


@router.get("/{inward_id}", response_model=InwardResponse)
def get_inward(inward_id: str, db: Session = Depends(get_db)):
    inward = db.query(InwardEntry).filter(InwardEntry.id == inward_id).first()
    if not inward:
        raise HTTPException(status_code=404, detail="Inward entry not found")
    return inward