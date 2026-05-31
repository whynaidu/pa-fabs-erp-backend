from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from backend.models.loom import LoomStatus


class LoomResponse(BaseModel):
    loom_number: int
    status: LoomStatus
    current_po: Optional[str]
    current_cycle: Optional[int]
    current_beam: Optional[str]
    allocated_by: Optional[str]
    allocated_at: Optional[datetime]

    class Config:
        from_attributes = True


class LoomAllocationRequest(BaseModel):
    po_number: str
    beam_id: str
    loom_number: int
    weft_details: Optional[str] = None
    expected_done: Optional[datetime] = None


class LoomAllocationResponse(BaseModel):
    id: str
    po_number: str
    cycle_number: int
    beam_id: str
    loom_number: int
    weft_details: Optional[str]
    allocation_date: datetime
    expected_done: Optional[datetime]
    submitted_by: str
    created_at: datetime

    class Config:
        from_attributes = True