from sqlalchemy import Column, String, Numeric, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from backend.database import Base
import enum


class BeamStatus(str, enum.Enum):
    AVAILABLE = "available"
    ALLOCATED = "allocated"
    COMPLETED = "completed"


class Beam(Base):
    __tablename__ = "beams"

    id = Column(String, primary_key=True, index=True)
    po_number = Column(String(80), ForeignKey("purchase_orders.po_number"), nullable=False, index=True)
    cycle_number = Column(Integer, nullable=False)
    return_entry_id = Column(String, ForeignKey("return_entries.id"), nullable=True)
    beam_number = Column(String(30), nullable=False, unique=True)
    beam_metres = Column(Numeric(10, 2), nullable=False)
    warp_colour = Column(String(80), nullable=True)
    warp_count = Column(String(50), nullable=True)
    quality_grade = Column(String(1), nullable=True)
    status = Column(SQLEnum(BeamStatus), nullable=False, default=BeamStatus.AVAILABLE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())