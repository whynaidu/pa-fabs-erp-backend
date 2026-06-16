from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from backend.models.return_entry import ReturnType


class BeamEntry(BaseModel):
    beam_metres: float = Field(gt=0)
    total_ends: Optional[int] = None   # auto-filled from the PO; may be absent if the PO has none


class ReturnBase(BaseModel):
    po_number: str
    return_type: ReturnType
    beams_returned: Optional[int] = None
    warp_metres: Optional[float] = None
    weft_metres: Optional[float] = None
    return_cones: Optional[int] = None
    quality_grade: Optional[str] = None
    operator_name: Optional[str] = None
    receiver_name: Optional[str] = None
    return_date: datetime
    remarks: Optional[str] = None
    beam_entries: Optional[List[BeamEntry]] = None


class ReturnCreate(ReturnBase):
    pass


class ReturnResponse(ReturnBase):
    id: str
    cycle_number: int
    outward_id: Optional[str]
    submitted_by: str
    created_at: datetime

    class Config:
        from_attributes = True