from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import uuid
from backend.database import get_db
from backend.models.user import User, UserRole
from backend.models.inventory import Inventory
from backend.models.loom import Loom
from backend.models.po import PurchaseOrder
from backend.schemas.inventory import InventoryCreate, InventoryResponse
from backend.api.deps import get_current_user, get_current_admin, require_po_access, admin_partial_update

router = APIRouter(prefix="/inventory-inward", tags=["Inventory Inward"])


@router.post("/", response_model=InventoryResponse)
def create_inventory(
    inv: InventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == inv.po_number).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")

    loom = db.query(Loom).filter(Loom.loom_number == inv.loom_number).first()
    if not loom:
        raise HTTPException(status_code=404, detail="Loom not found")

    # The loom carries the live PO+cycle+beam while occupied (it is freed only at
    # delivery), so the cycle and beam for this finished fabric come from it.
    cycle_number = loom.current_cycle
    beam_id = loom.current_beam
    if cycle_number is None or loom.current_po != inv.po_number:
        raise HTTPException(
            status_code=400,
            detail="Loom is not currently running this PO; cannot record finished fabric",
        )

    record = Inventory(
        id=f"inv_{uuid.uuid4().hex}",
        po_number=inv.po_number,
        cycle_number=cycle_number,
        loom_number=inv.loom_number,
        beam_id=beam_id,
        fabric_metres=inv.fabric_metres,
        quality_grade=inv.quality_grade,
        received_date=inv.received_date,
        received_by=inv.received_by,
        remarks=inv.remarks,
        submitted_by=current_user.id,
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Finished fabric already recorded for this loom in this cycle")
    db.refresh(record)
    return record


@router.get("/", response_model=List[InventoryResponse])
def list_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.ADMIN:
        return db.query(Inventory).order_by(Inventory.created_at.desc()).all()
    return db.query(Inventory).filter(Inventory.submitted_by == current_user.id).order_by(Inventory.created_at.desc()).all()


@router.get("/po/{po_number}/cycle/{cycle_number}", response_model=List[InventoryResponse])
def inventory_for_cycle(
    po_number: str,
    cycle_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_po_access(po_number, db, current_user)
    return db.query(Inventory).filter(
        Inventory.po_number == po_number,
        Inventory.cycle_number == cycle_number,
    ).all()


# Whitelisted admin edit — only the listed columns may be updated
@router.put("/{inv_id}", response_model=InventoryResponse)
def update_inventory(inv_id: str, payload: dict = Body(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    obj = db.query(Inventory).filter(Inventory.id == inv_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return admin_partial_update(obj, payload, {"fabric_metres", "quality_grade", "received_date", "received_by", "remarks"}, db)


@router.delete("/{inv_id}")
def delete_inventory(inv_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    record = db.query(Inventory).filter(Inventory.id == inv_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Inventory record not found")
    db.delete(record)
    db.commit()
    return {"message": "Inventory record deleted"}
