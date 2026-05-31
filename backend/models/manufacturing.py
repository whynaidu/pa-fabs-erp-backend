from sqlalchemy import Column, String, Numeric, Integer, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from backend.database import Base


class ManufacturingLog(Base):
    __tablename__ = "manufacturing_logs"

    id = Column(String, primary_key=True, index=True)
    po_number = Column(String(80), ForeignKey("purchase_orders.po_number"), nullable=False, index=True)
    cycle_number = Column(Integer, nullable=False)
    loom_number = Column(Integer, ForeignKey("looms.loom_number"), nullable=False)
    beam_id = Column(String(30), nullable=True)
    metres_today = Column(Numeric(10, 2), nullable=False)
    fabric_metres = Column(Numeric(10, 2), nullable=True)
    total_manufactured = Column(Numeric(10, 2), nullable=False)
    balance_qty = Column(Numeric(10, 2), nullable=True)
    log_date = Column(DateTime(timezone=True), nullable=False)
    operator_name = Column(String(150), nullable=True)
    received_date = Column(DateTime(timezone=True), nullable=True)
    received_by = Column(String(150), nullable=True)
    remarks = Column(Text, nullable=True)
    is_done = Column(Boolean, nullable=False, default=False)
    submitted_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())