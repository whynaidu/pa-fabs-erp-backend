from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from backend.models.inward import NextProcess


class InwardBase(BaseModel):
    po_number: str
    warp_count: Optional[str] = None
    warp_colour: Optional[str] = None
    warp_kg: Optional[float] = None
    warp_bundles: Optional[int] = None
    weft_count: Optional[str] = None
    weft_colour: Optional[str] = None
    weft_kg: Optional[float] = None
    weft_bundles: Optional[int] = None
    rm_number: Optional[str] = None
    cone_bag_count: Optional[int] = None
    next_process: Optional[NextProcess] = None
    location: Optional[str] = None
    cost: Optional[float] = None
    received_by: Optional[str] = None
    is_done: bool = False
    entry_date: datetime


class InwardCreate(InwardBase):
    pass


class InwardResponse(InwardBase):
    id: str
    cycle_number: int
    submitted_by: str
    created_at: datetime

    class Config:
        from_attributes = True