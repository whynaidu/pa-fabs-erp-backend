from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.sql import func
from backend.database import Base
import enum


class AllocationStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LoomAllocation(Base):
    __tablename__ = "loom_allocations"

    id = Column(String, primary_key=True, index=True)
    po_number = Column(String(80), ForeignKey("purchase_orders.po_number"), nullable=False, index=True)
    cycle_number = Column(Integer, nullable=False)
    beam_id = Column(String(30), ForeignKey("beams.beam_number"), nullable=False)
    loom_number = Column(Integer, ForeignKey("looms.loom_number"), nullable=False)
    weft_details = Column(Text, nullable=True)
    allocation_date = Column(DateTime(timezone=True), nullable=False)
    expected_done = Column(DateTime(timezone=True), nullable=True)
    status = Column(SQLEnum(AllocationStatus), nullable=False, default=AllocationStatus.ACTIVE)
    submitted_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())