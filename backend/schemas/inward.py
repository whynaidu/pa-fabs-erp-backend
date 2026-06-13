from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
import json
from backend.models.inward import NextProcess
from backend.schemas.po import YarnRow


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
    warp_rows: Optional[List[YarnRow]] = None
    weft_rows: Optional[List[YarnRow]] = None
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

    @field_validator("warp_rows", "weft_rows", mode="before")
    @classmethod
    def _parse_rows(cls, v):
        # The ORM stores warp_rows/weft_rows as a JSON string; parse it back to a list.
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    class Config:
        from_attributes = True