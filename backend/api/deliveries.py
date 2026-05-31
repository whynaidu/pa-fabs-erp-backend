from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.user import User
from backend.models.delivery import Delivery
from backend.models.inward import InwardEntry
from backend.models.loom import Loom, LoomStatus
from backend.models.loom_allocation import LoomAllocation
from backend.models.po import PurchaseOrder
from backend.schemas.delivery import DeliveryCreate, DeliveryResponse, DCSlipResponse
from backend.api.deps import get_current_user
import json

router = APIRouter(prefix="/deliveries", tags=["Deliveries"])


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

    total_metres = sum([p.metres for p in (delivery.pieces_data or [])])
    no_pieces = len(delivery.pieces_data or [])

    dc_count = db.query(Delivery).count() + 1
    dc_number = f"DC-{str(dc_count).zfill(4)}"

    pieces_json = json.dumps([p.dict() for p in (delivery.pieces_data or [])]) if delivery.pieces_data else None

    new_delivery = Delivery(
        id=f"delivery_{hash(dc_number)}",
        po_number=delivery.po_number,
        cycle_number=inward.cycle_number,
        dc_number=dc_number,
        delivery_date=delivery.delivery_date,
        customer_name=delivery.customer_name,
        design_no=delivery.design_no,
        reed_pick=delivery.reed_pick,
        description=delivery.description,
        pieces_data=pieces_json,
        no_pieces=no_pieces,
        grand_total_metres=total_metres,
        vehicle_number=delivery.vehicle_number,
        driver_name=delivery.driver_name,
        receiver_name=delivery.receiver_name,
        remarks=delivery.remarks,
        submitted_by=current_user.id
    )

    db.add(new_delivery)
    db.commit()
    db.refresh(new_delivery)

    allocations = db.query(LoomAllocation).filter(
        LoomAllocation.po_number == delivery.po_number,
        LoomAllocation.cycle_number == inward.cycle_number
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

    po.status = "complete"
    db.commit()

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


@router.get("/{delivery_id}", response_model=DeliveryResponse)
def get_delivery(delivery_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return delivery


@router.get("/{delivery_id}/dc-slip", response_model=DCSlipResponse)
def get_dc_slip(delivery_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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