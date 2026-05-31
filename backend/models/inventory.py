from sqlalchemy import Column, String, Numeric, Integer, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from backend.database import Base


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(String, primary_key=True, index=True)
    po_number = Column(String(80), ForeignKey("purchase_orders.po_number"), nullable=False, index=True)
    cycle_number = Column(Integer, nullable=False)
    loom_number = Column(Integer, ForeignKey("looms.loom_number"), nullable=False)
    beam_id = Column(String(30), nullable=True)
    fabric_metres = Column(Numeric(10, 2), nullable=False)
    quality_grade = Column(String(1), nullable=True)
    received_date = Column(DateTime(timezone=True), nullable=False)
    received_by = Column(String(150), nullable=False)
    remarks = Column(Text, nullable=True)
    submitted_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())