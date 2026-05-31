from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from backend.models.po import POStatus
from backend.models.po_yarn_detail import YarnType


class YarnRow(BaseModel):
    count: str
    colour: str
    qty_kg: Optional[float] = None
    bundles: Optional[int] = None


class POBase(BaseModel):
    po_number: str
    description: Optional[str] = None
    purchaser: Optional[str] = None
    remarks: Optional[str] = None
    reed: Optional[str] = None
    pick: Optional[str] = None
    width: Optional[str] = None
    order_qty: float
    cost_per_meter: Optional[float] = None
    order_date: Optional[datetime] = None
    expected_date: Optional[datetime] = None
    warp_rows: List[YarnRow] = []
    weft_rows: List[YarnRow] = []


class POCreate(POBase):
    pass


class POUpdate(BaseModel):
    description: Optional[str] = None
    purchaser: Optional[str] = None
    remarks: Optional[str] = None
    reed: Optional[str] = None
    pick: Optional[str] = None
    width: Optional[str] = None
    order_qty: Optional[float] = None
    cost_per_meter: Optional[float] = None
    order_date: Optional[datetime] = None
    expected_date: Optional[datetime] = None
    status: Optional[POStatus] = None
    warp_rows: Optional[List[YarnRow]] = None
    weft_rows: Optional[List[YarnRow]] = None


class POYarnDetailResponse(BaseModel):
    id: str
    po_number: str
    yarn_type: YarnType
    count: Optional[str]
    colour: Optional[str]
    qty_kg: Optional[float]
    bundles: Optional[int]

    class Config:
        from_attributes = True


class POResponse(POBase):
    user_id: str
    status: POStatus
    created_at: datetime
    yarn_details: List[POYarnDetailResponse] = []

    class Config:
        from_attributes = True


class POYarnResponse(BaseModel):
    warp_counts: List[str] = []
    warp_colours: List[str] = []
    weft_counts: List[str] = []
    weft_colours: List[str] = []


class POCycle(BaseModel):
    cycle_number: int
    has_delivery: bool