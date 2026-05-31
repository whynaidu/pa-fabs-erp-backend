from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from backend.database import Base
import enum


class LoomStatus(str, enum.Enum):
    FREE = "free"
    OCCUPIED = "occupied"
    ON_HOLD = "on-hold"


class Loom(Base):
    __tablename__ = "looms"

    loom_number = Column(Integer, primary_key=True)
    status = Column(SQLEnum(LoomStatus), nullable=False, default=LoomStatus.FREE)
    current_po = Column(String(80), nullable=True)
    current_cycle = Column(Integer, nullable=True)
    current_beam = Column(String(30), nullable=True)
    allocated_by = Column(String(150), nullable=True)
    allocated_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())