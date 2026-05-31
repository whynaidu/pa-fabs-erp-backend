from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from backend.models.outward import ProcessType


class OutwardBase(BaseModel):
    po_number: str
    process_type: ProcessType
    operator_name: str
    warp_count: Optional[str] = None
    warp_colour: Optional[str] = None
    warp_metres: Optional[float] = None
    warp_cones: Optional[int] = None
    weft_count: Optional[str] = None
    weft_colour: Optional[str] = None
    weft_kg: Optional[float] = None
    weft_cones: Optional[int] = None
    beams_expected: Optional[int] = None
    outward_date: datetime
    expected_return: Optional[datetime] = None
    is_done: bool = False


class OutwardCreate(OutwardBase):
    pass


class OutwardResponse(OutwardBase):
    id: str
    cycle_number: int
    submitted_by: str
    created_at: datetime

    class Config:
        from_attributes = True