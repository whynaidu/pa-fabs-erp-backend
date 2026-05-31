from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class InventoryBase(BaseModel):
    po_number: str
    loom_number: int
    fabric_metres: float
    quality_grade: Optional[str] = None
    received_date: datetime
    received_by: str
    remarks: Optional[str] = None


class InventoryCreate(InventoryBase):
    pass


class InventoryResponse(InventoryBase):
    id: str
    cycle_number: int
    beam_id: Optional[str]
    submitted_by: str
    created_at: datetime

    class Config:
        from_attributes = True