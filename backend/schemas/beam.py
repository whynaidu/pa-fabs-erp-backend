from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from backend.models.beam import BeamStatus


class BeamResponse(BaseModel):
    id: str
    po_number: str
    cycle_number: int
    beam_number: str
    beam_metres: float
    warp_colour: Optional[str]
    warp_count: Optional[str]
    quality_grade: Optional[str]
    status: BeamStatus
    created_at: datetime

    class Config:
        from_attributes = True