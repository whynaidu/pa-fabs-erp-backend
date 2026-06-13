from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from backend.database import get_db
from backend.models.user import User
from backend.models.po import PurchaseOrder
from backend.models.po_yarn_detail import POYarnDetail, YarnType
from backend.schemas.po import POCreate, POUpdate, POResponse, POYarnResponse, POCycle
from backend.models.inward import InwardEntry
from backend.models.outward import OutwardEntry
from backend.models.return_entry import ReturnEntry
from backend.models.beam import Beam
from backend.models.loom_allocation import LoomAllocation
from backend.models.manufacturing import ManufacturingLog
from backend.models.inventory import Inventory
from backend.models.delivery import Delivery
from backend.api.deps import get_current_user, get_current_admin, require_po_access
import uuid

router = APIRouter(prefix="/pos", tags=["Purchase Orders"])


def create_yarn_details(db: Session, po_number: str, warp_rows: list, weft_rows: list):
    # Rows arrive as Pydantic models (create) or plain dicts (update via .dict()).
    g = lambda row, k: row.get(k) if isinstance(row, dict) else getattr(row, k, None)
    for yarn_type, rows in ((YarnType.WARP, warp_rows), (YarnType.WEFT, weft_rows)):
        for row in rows:
            db.add(POYarnDetail(
                id=f"yarn_{uuid.uuid4().hex}",
                po_number=po_number,
                yarn_type=yarn_type,
                count=g(row, "count"),
                colour=g(row, "colour"),
                qty_kg=g(row, "qty_kg"),
                bundles=g(row, "bundles"),
            ))
    db.commit()


def _to_yarn_row(r):
    return {"count": r.count or "", "colour": r.colour or "",
            "qty_kg": float(r.qty_kg) if r.qty_kg is not None else None,
            "bundles": r.bundles}


def _set_yarn(po, rows):
    po.warp_rows = [_to_yarn_row(r) for r in rows if r.yarn_type == YarnType.WARP]
    po.weft_rows = [_to_yarn_row(r) for r in rows if r.yarn_type == YarnType.WEFT]
    return po


def attach_yarn(po, db: Session):
    """Attach a single PO's warp/weft yarn rows (stored separately) onto the ORM
    object so the response includes them — these feed the dropdowns on every form."""
    rows = db.query(POYarnDetail).filter(POYarnDetail.po_number == po.po_number).all()
    return _set_yarn(po, rows)


def attach_yarn_bulk(pos, db: Session):
    """Same as attach_yarn but for a list — one query instead of N (avoids N+1)."""
    if not pos:
        return pos
    numbers = [p.po_number for p in pos]
    rows = db.query(POYarnDetail).filter(POYarnDetail.po_number.in_(numbers)).all()
    by_po = {}
    for r in rows:
        by_po.setdefault(r.po_number, []).append(r)
    for p in pos:
        _set_yarn(p, by_po.get(p.po_number, []))
    return pos


@router.post("/", response_model=POResponse)
def create_po(po: POCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po.po_number).first()
    if db_po:
        raise HTTPException(status_code=400, detail="PO number already exists")

    db_po = PurchaseOrder(
        po_number=po.po_number,
        user_id=current_user.id,
        description=po.description,
        purchaser=po.purchaser,
        remarks=po.remarks,
        reed=po.reed,
        pick=po.pick,
        reed_on=po.reed_on,
        pick_on=po.pick_on,
        width=po.width,
        order_qty=po.order_qty,
        cost_per_meter=po.cost_per_meter,
        warp_count=po.warp_count,
        weft_count=po.weft_count,
        total_ends=po.total_ends,
        shortage_percentage=po.shortage_percentage,
        order_date=po.order_date,
        expected_date=po.expected_date
    )
    db.add(db_po)
    db.commit()
    db.refresh(db_po)

    if po.warp_rows or po.weft_rows:
        create_yarn_details(db, po.po_number, po.warp_rows, po.weft_rows)
        db.refresh(db_po)

    return attach_yarn(db_po, db)


@router.get("/", response_model=List[POResponse])
def list_pos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        pos = db.query(PurchaseOrder).all()
    else:
        pos = db.query(PurchaseOrder).filter(PurchaseOrder.user_id == current_user.id).all()
    return attach_yarn_bulk(pos, db)


@router.get("/{po_number}", response_model=POResponse)
def get_po(po_number: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_number).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")

    if current_user.role != "admin" and po.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this PO")

    return attach_yarn(po, db)


@router.get("/{po_number}/yarn", response_model=POYarnResponse)
def get_po_yarn(po_number: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_po_access(po_number, db, current_user)
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_number).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")

    yarn_details = db.query(POYarnDetail).filter(POYarnDetail.po_number == po_number).all()

    warp_counts = list(set([y.count for y in yarn_details if y.yarn_type == YarnType.WARP and y.count]))
    warp_colours = list(set([y.colour for y in yarn_details if y.yarn_type == YarnType.WARP and y.colour]))
    weft_counts = list(set([y.count for y in yarn_details if y.yarn_type == YarnType.WEFT and y.count]))
    weft_colours = list(set([y.colour for y in yarn_details if y.yarn_type == YarnType.WEFT and y.colour]))

    return POYarnResponse(
        warp_counts=warp_counts,
        warp_colours=warp_colours,
        weft_counts=weft_counts,
        weft_colours=weft_colours
    )


@router.get("/{po_number}/cycles", response_model=List[POCycle])
def get_po_cycles(po_number: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_po_access(po_number, db, current_user)
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_number).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")

    inwards = db.query(InwardEntry).filter(InwardEntry.po_number == po_number).all()
    cycles = []
    for inward in inwards:
        has_delivery = db.query(Delivery).filter(
            Delivery.po_number == po_number,
            Delivery.cycle_number == inward.cycle_number
        ).first() is not None
        cycles.append(POCycle(cycle_number=inward.cycle_number, has_delivery=has_delivery))

    return sorted(cycles, key=lambda x: x.cycle_number)


@router.get("/{po_number}/timeline")
def get_po_timeline(po_number: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    """Full per-cycle timeline for a PO (admin only)."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_number).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")
    cols = lambda r: {c.name: getattr(r, c.name) for c in r.__table__.columns}
    cycles = {}
    for model, key in [(InwardEntry, "inward"), (OutwardEntry, "outwards"), (ReturnEntry, "returns"),
                       (Beam, "beams"), (LoomAllocation, "allocations"), (ManufacturingLog, "manufacturing"),
                       (Inventory, "inventory"), (Delivery, "delivery")]:
        for r in db.query(model).filter(model.po_number == po_number).all():
            cyc = cycles.setdefault(r.cycle_number, {})
            if key in ("inward", "delivery"):
                cyc[key] = cols(r)
            else:
                cyc.setdefault(key, []).append(cols(r))
    return {"po_number": po_number, "cycles": [
        {"cycle_number": n, **cycles[n]} for n in sorted(cycles)
    ]}


@router.put("/{po_number}", response_model=POResponse)
def update_po(
    po_number: str,
    po_update: POUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_number).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")

    if current_user.role != "admin" and po.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this PO")

    update_data = po_update.dict(exclude_unset=True)
    warp_rows = update_data.pop("warp_rows", None)
    weft_rows = update_data.pop("weft_rows", None)

    for field, value in update_data.items():
        setattr(po, field, value)

    db.commit()
    db.refresh(po)

    if warp_rows is not None or weft_rows is not None:
        db.query(POYarnDetail).filter(POYarnDetail.po_number == po_number).delete()
        create_yarn_details(db, po_number, warp_rows or [], weft_rows or [])
        db.refresh(po)

    return attach_yarn(po, db)


@router.delete("/{po_number}")
def delete_po(po_number: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_number).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")

    db.query(POYarnDetail).filter(POYarnDetail.po_number == po_number).delete()
    db.delete(po)
    db.commit()
    return {"message": "PO deleted successfully"}