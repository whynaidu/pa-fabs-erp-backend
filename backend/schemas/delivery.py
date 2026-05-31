from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PieceData(BaseModel):
    type: Optional[str] = None
    piece_no: str
    metres: float


class DeliveryBase(BaseModel):
    po_number: str
    delivery_date: datetime
    customer_name: str
    design_no: Optional[str] = None
    reed_pick: Optional[str] = None
    description: Optional[str] = None
    pieces_data: Optional[List[PieceData]] = None
    vehicle_number: Optional[str] = None
    driver_name: Optional[str] = None
    receiver_name: Optional[str] = None
    remarks: Optional[str] = None


class DeliveryCreate(DeliveryBase):
    pass


class DeliveryResponse(DeliveryBase):
    id: str
    cycle_number: int
    dc_number: str
    no_pieces: Optional[int]
    grand_total_metres: float
    submitted_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class DCSlipResponse(BaseModel):
    dc_number: str
    date: str
    company_name: str
    company_details: str
    to_customer: str
    po_design_no: str
    description: str
    reed_pick: str
    vehicle_no: str
    driver: str
    receiver: str
    pieces: List[dict]
    no_pieces: int
    grand_total_metres: float
    remarks: Optional[str]