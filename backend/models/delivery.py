from sqlalchemy import Column, String, Numeric, Integer, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from backend.database import Base


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(String, primary_key=True, index=True)
    po_number = Column(String(80), ForeignKey("purchase_orders.po_number"), nullable=False, index=True)
    cycle_number = Column(Integer, nullable=False)
    dc_number = Column(String(20), nullable=False, unique=True)
    delivery_date = Column(DateTime(timezone=True), nullable=False)
    customer_name = Column(String(200), nullable=False)
    design_no = Column(String(100), nullable=True)
    reed_pick = Column(String(30), nullable=True)
    description = Column(Text, nullable=True)
    pieces_data = Column(Text, nullable=True)
    no_pieces = Column(Integer, nullable=True)
    grand_total_metres = Column(Numeric(10, 2), nullable=False)
    vehicle_number = Column(String(20), nullable=True)
    driver_name = Column(String(150), nullable=True)
    receiver_name = Column(String(150), nullable=True)
    remarks = Column(Text, nullable=True)
    submitted_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())