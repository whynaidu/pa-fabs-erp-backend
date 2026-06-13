from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from typing import List
from backend.database import get_db
from backend.models.user import User
from backend.models.delivery import Delivery
from backend.models.inward import InwardEntry
from backend.models.loom import Loom, LoomStatus
from backend.models.loom_allocation import LoomAllocation, AllocationStatus
from backend.models.manufacturing import ManufacturingLog
from backend.models.inventory import Inventory
from backend.models.po import PurchaseOrder, POStatus
from backend.models.user import UserRole
from backend.schemas.delivery import DeliveryCreate, DeliveryResponse, DCSlipResponse
from backend.api.deps import get_current_user, get_current_admin, require_po_access
import json
import uuid

router = APIRouter(prefix="/deliveries", tags=["Deliveries"])


def _delivery_readiness(db: Session, po_number: str, cycle_number: int) -> dict:
    """Delivery depends on MANUFACTURED fabric only (not loom-free / inventory):
    as soon as any metres have been woven for the PO+cycle it can be delivered."""
    manufactured = float(db.query(func.coalesce(func.sum(ManufacturingLog.metres_today), 0)).filter(
        ManufacturingLog.po_number == po_number,
        ManufacturingLog.cycle_number == cycle_number,
    ).scalar() or 0)
    reasons = []
    if manufactured <= 0:
        reasons.append("No fabric manufactured yet for this PO+cycle")
    if db.query(Delivery).filter(Delivery.po_number == po_number, Delivery.cycle_number == cycle_number).first():
        reasons.append("Delivery already exists for this PO+cycle")
    return {"ready": len(reasons) == 0, "reasons": reasons, "manufactured_metres": manufactured}


@router.post("/", response_model=DeliveryResponse)
def create_delivery(
    delivery: DeliveryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == delivery.po_number).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")

    inward = db.query(InwardEntry).filter(
        InwardEntry.po_number == delivery.po_number
    ).order_by(InwardEntry.cycle_number.desc()).first()

    if not inward:
        raise HTTPException(status_code=404, detail="No inward entry found for this PO")

    cycle_number = inward.cycle_number

    # One delivery per PO+cycle (full only).
    if db.query(Delivery).filter(
        Delivery.po_number == delivery.po_number,
        Delivery.cycle_number == cycle_number,
    ).first():
        raise HTTPException(status_code=400, detail="Delivery already exists for this PO+cycle")

    # Delivery is gated on manufactured fabric only (client rule).
    ready = _delivery_readiness(db, delivery.po_number, cycle_number)
    if not ready["ready"]:
        raise HTTPException(status_code=400, detail="; ".join(ready["reasons"]))

    # Pieces come from the user's piece table (No / Metres / Weight). If none are
    # supplied, fall back to the finished-fabric (inventory) rows for the cycle.
    if delivery.pieces_data:
        pieces = [p.model_dump() for p in delivery.pieces_data]
    else:
        inventory = db.query(Inventory).filter(
            Inventory.po_number == delivery.po_number,
            Inventory.cycle_number == cycle_number,
        ).all()
        pieces = [{"piece_no": str(i + 1), "metres": float(r.fabric_metres), "weight": None}
                  for i, r in enumerate(inventory)]

    if not pieces:
        raise HTTPException(status_code=400, detail="Delivery has no pieces — add at least one piece")

    total_metres = sum((p.get("metres") or 0) for p in pieces)
    total_weight = sum((p.get("weight") or 0) for p in pieces)
    no_pieces = len(pieces)
    pieces_json = json.dumps(pieces)

    dc_count = db.query(Delivery).count() + 1
    dc_number = f"DC-{str(dc_count).zfill(4)}"

    new_delivery = Delivery(
        id=f"delivery_{uuid.uuid4().hex}",
        po_number=delivery.po_number,
        cycle_number=cycle_number,
        dc_number=dc_number,
        delivery_date=delivery.delivery_date,
        customer_name=delivery.customer_name,
        design_no=delivery.design_no,
        reed_pick=delivery.reed_pick or (f"{po.reed}x{po.pick}" if po.reed and po.pick else None),
        description=delivery.description or po.description,
        pieces_data=pieces_json,
        no_pieces=no_pieces,
        grand_total_metres=total_metres,
        total_weight=total_weight,
        vehicle_number=delivery.vehicle_number,
        driver_name=delivery.driver_name,
        receiver_name=delivery.receiver_name,
        remarks=delivery.remarks,
        submitted_by=current_user.id
    )

    db.add(new_delivery)

    # Free every loom used by this PO+cycle — the only event that releases the
    # global lock. Done in the SAME transaction as the delivery insert so the
    # lock can never leak on partial failure.
    allocations = db.query(LoomAllocation).filter(
        LoomAllocation.po_number == delivery.po_number,
        LoomAllocation.cycle_number == cycle_number
    ).all()
    for alloc in allocations:
        loom = db.query(Loom).filter(Loom.loom_number == alloc.loom_number).first()
        if loom:
            loom.status = LoomStatus.FREE
            loom.current_po = None
            loom.current_cycle = None
            loom.current_beam = None
            loom.allocated_by = None
            loom.allocated_at = None

    po.status = POStatus.COMPLETE
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Delivery already exists for this PO+cycle")
    db.refresh(new_delivery)

    return new_delivery


@router.get("/", response_model=List[DeliveryResponse])
def list_deliveries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        deliveries = db.query(Delivery).order_by(Delivery.delivery_date.desc()).all()
    else:
        deliveries = db.query(Delivery).filter(
            Delivery.submitted_by == current_user.id
        ).order_by(Delivery.delivery_date.desc()).all()
    return deliveries


@router.get("/po/{po_number}/cycle/{cycle_number}/ready")
def delivery_ready(po_number: str, cycle_number: int, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    require_po_access(po_number, db, current_user)
    return _delivery_readiness(db, po_number, cycle_number)


@router.get("/po/{po_number}", response_model=List[DeliveryResponse])
def deliveries_for_po(po_number: str, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    require_po_access(po_number, db, current_user)
    return db.query(Delivery).filter(Delivery.po_number == po_number).order_by(
        Delivery.cycle_number).all()


@router.get("/{delivery_id}", response_model=DeliveryResponse)
def get_delivery(delivery_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    require_po_access(delivery.po_number, db, current_user)
    return delivery


@router.get("/{delivery_id}/dc-slip", response_model=DCSlipResponse)
def get_dc_slip(delivery_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")

    pieces = []
    if delivery.pieces_data:
        pieces = json.loads(delivery.pieces_data)

    return DCSlipResponse(
        dc_number=delivery.dc_number,
        date=delivery.delivery_date.strftime("%Y-%m-%d") if delivery.delivery_date else "",
        company_name="PA FABS",
        company_details="Crafted in Weaving · Namakkal, Tamil Nadu · GSTIN: 33ERVPM7456N1ZP · Ph: 8220774578",
        to_customer=delivery.customer_name,
        po_design_no=f"{delivery.po_number} / {delivery.design_no or ''}",
        description=delivery.description or "",
        reed_pick=delivery.reed_pick or "",
        vehicle_no=delivery.vehicle_number or "",
        driver=delivery.driver_name or "",
        receiver=delivery.receiver_name or "",
        pieces=pieces,
        no_pieces=delivery.no_pieces,
        grand_total_metres=delivery.grand_total_metres,
        remarks=delivery.remarks
    )