from sqlalchemy import Column, String, Numeric, Integer, DateTime, ForeignKey, Boolean, Enum as SQLEnum, Text
from sqlalchemy.sql import func
from backend.database import Base
import enum


class ProcessType(str, enum.Enum):
    WARPING = "warping"
    WINDING = "winding"


class OutwardEntry(Base):
    __tablename__ = "outward_entries"

    id = Column(String, primary_key=True, index=True)
    po_number = Column(String(80), ForeignKey("purchase_orders.po_number"), nullable=False, index=True)
    cycle_number = Column(Integer, nullable=False)
    process_type = Column(SQLEnum(ProcessType), nullable=False)
    operator_name = Column(String(150), nullable=False)
    warp_count = Column(String(50), nullable=True)
    warp_colour = Column(String(80), nullable=True)
    warp_metres = Column(Numeric(10, 2), nullable=True)
    warp_cones = Column(Integer, nullable=True)
    weft_count = Column(String(50), nullable=True)
    weft_colour = Column(String(80), nullable=True)
    weft_kg = Column(Numeric(10, 2), nullable=True)
    weft_cones = Column(Integer, nullable=True)
    beams_expected = Column(Integer, nullable=True)
    outward_date = Column(DateTime(timezone=True), nullable=False)
    expected_return = Column(DateTime(timezone=True), nullable=True)
    is_done = Column(Boolean, nullable=False, default=False)
    submitted_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())