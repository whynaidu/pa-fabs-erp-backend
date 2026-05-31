from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
import csv
import io
from backend.database import get_db
from backend.models.user import User
from backend.models.po import PurchaseOrder
from backend.models.inward import InwardEntry
from backend.models.outward import OutwardEntry
from backend.models.return_entry import ReturnEntry
from backend.models.beam import Beam
from backend.models.loom import Loom
from backend.models.loom_allocation import LoomAllocation
from backend.models.manufacturing import ManufacturingLog
from backend.models.inventory import Inventory
from backend.models.delivery import Delivery
from backend.api.deps import get_current_admin

router = APIRouter(prefix="/export", tags=["Export & Reports"])

_MODULES = {
    "pos": PurchaseOrder,
    "inwards": InwardEntry,
    "outwards": OutwardEntry,
    "returns": ReturnEntry,
    "beams": Beam,
    "looms": Loom,
    "allocations": LoomAllocation,
    "manufacturing": ManufacturingLog,
    "inventory": Inventory,
    "deliveries": Delivery,
}


@router.get("/csv/{module}")
def export_csv(module: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    model = _MODULES.get(module)
    if model is None:
        raise HTTPException(status_code=404, detail=f"Unknown module. Choose from: {', '.join(_MODULES)}")
    columns = [c.name for c in model.__table__.columns]
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(columns)
    for row in db.query(model).all():
        writer.writerow([getattr(row, c) for c in columns])
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{module}.csv"'},
    )


@router.get("/po/{po_number}/report")
def po_report(po_number: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_number).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")
    cols = lambda r: {c.name: getattr(r, c.name) for c in r.__table__.columns}
    return {
        "po": cols(po),
        "inwards": [cols(r) for r in db.query(InwardEntry).filter(InwardEntry.po_number == po_number).all()],
        "outwards": [cols(r) for r in db.query(OutwardEntry).filter(OutwardEntry.po_number == po_number).all()],
        "returns": [cols(r) for r in db.query(ReturnEntry).filter(ReturnEntry.po_number == po_number).all()],
        "beams": [cols(r) for r in db.query(Beam).filter(Beam.po_number == po_number).all()],
        "allocations": [cols(r) for r in db.query(LoomAllocation).filter(LoomAllocation.po_number == po_number).all()],
        "manufacturing": [cols(r) for r in db.query(ManufacturingLog).filter(ManufacturingLog.po_number == po_number).all()],
        "inventory": [cols(r) for r in db.query(Inventory).filter(Inventory.po_number == po_number).all()],
        "deliveries": [cols(r) for r in db.query(Delivery).filter(Delivery.po_number == po_number).all()],
    }
