from sqlalchemy import Column, String, Numeric, Integer, DateTime, ForeignKey, Boolean, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from backend.database import Base
import enum


class NextProcess(str, enum.Enum):
    WARPING = "warping"
    WINDING = "winding"
    BOTH = "both"


class InwardEntry(Base):
    __tablename__ = "inward_entries"

    id = Column(String, primary_key=True, index=True)
    po_number = Column(String(80), ForeignKey("purchase_orders.po_number"), nullable=False, index=True)
    cycle_number = Column(Integer, nullable=False)
    warp_count = Column(String(50), nullable=True)
    warp_colour = Column(String(80), nullable=True)
    warp_kg = Column(Numeric(10, 2), nullable=True)
    warp_bundles = Column(Integer, nullable=True)
    weft_count = Column(String(50), nullable=True)
    weft_colour = Column(String(80), nullable=True)
    weft_kg = Column(Numeric(10, 2), nullable=True)
    weft_bundles = Column(Integer, nullable=True)
    rm_number = Column(String(80), nullable=True)
    cone_bag_count = Column(Integer, nullable=True)
    next_process = Column(SQLEnum(NextProcess), nullable=True)
    location = Column(String(120), nullable=True)
    warp_rows = Column(Text, nullable=True)   # JSON array of {count,colour,qty_kg,bundles}, moved from PO
    weft_rows = Column(Text, nullable=True)    # JSON array of {count,colour,qty_kg,bundles}, moved from PO
    cost = Column(Numeric(10, 2), nullable=True)
    received_by = Column(String(150), nullable=True)
    is_done = Column(Boolean, nullable=False, default=False)
    submitted_by = Column(String, nullable=False)
    entry_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())