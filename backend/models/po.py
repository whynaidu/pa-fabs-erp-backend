from sqlalchemy import Column, String, Numeric, DateTime, Enum as SQLEnum, Text
from sqlalchemy.sql import func
from backend.database import Base
import enum


class POStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    po_number = Column(String(80), primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    purchaser = Column(String(150), nullable=True)
    remarks = Column(Text, nullable=True)
    reed = Column(String(20), nullable=True)
    pick = Column(String(20), nullable=True)
    width = Column(String(20), nullable=True)
    order_qty = Column(Numeric(10, 2), nullable=False)
    cost_per_meter = Column(Numeric(10, 2), nullable=True)
    order_date = Column(DateTime(timezone=True), nullable=True)
    expected_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(SQLEnum(POStatus), nullable=False, default=POStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())