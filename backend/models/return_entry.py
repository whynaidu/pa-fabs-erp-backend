from sqlalchemy import Column, String, Numeric, Integer, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from backend.database import Base
import enum


class ReturnType(str, enum.Enum):
    WARPING_RETURN = "warping_return"
    WINDING_RETURN = "winding_return"


class ReturnEntry(Base):
    __tablename__ = "return_entries"

    id = Column(String, primary_key=True, index=True)
    po_number = Column(String(80), ForeignKey("purchase_orders.po_number"), nullable=False, index=True)
    cycle_number = Column(Integer, nullable=False)
    outward_id = Column(String, ForeignKey("outward_entries.id"), nullable=True)
    return_type = Column(SQLEnum(ReturnType), nullable=False)
    beams_returned = Column(Integer, nullable=True)
    warp_metres = Column(Numeric(10, 2), nullable=True)
    weft_metres = Column(Numeric(10, 2), nullable=True)
    return_cones = Column(Integer, nullable=True)
    quality_grade = Column(String(1), nullable=True)
    operator_name = Column(String(150), nullable=True)
    receiver_name = Column(String(150), nullable=True)
    return_date = Column(DateTime(timezone=True), nullable=False)
    remarks = Column(Text, nullable=True)
    submitted_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())