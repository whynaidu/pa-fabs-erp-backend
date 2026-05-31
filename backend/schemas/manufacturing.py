from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ManufacturingBase(BaseModel):
    loom_number: int = Field(gt=0)
    metres_today: float = Field(gt=0)
    fabric_metres: Optional[float] = None
    operator_name: Optional[str] = None
    received_date: Optional[datetime] = None
    received_by: Optional[str] = None
    remarks: Optional[str] = None
    is_done: bool = False
    log_date: datetime


class ManufacturingCreate(ManufacturingBase):
    pass


class ManufacturingResponse(ManufacturingBase):
    id: str
    po_number: str
    cycle_number: int
    beam_id: Optional[str]
    total_manufactured: float
    balance_qty: Optional[float]
    submitted_by: str
    created_at: datetime

    class Config:
        from_attributes = True