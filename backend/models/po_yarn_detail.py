from sqlalchemy import Column, String, Numeric, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from backend.database import Base
import enum


class YarnType(str, enum.Enum):
    WARP = "warp"
    WEFT = "weft"


class POYarnDetail(Base):
    __tablename__ = "po_yarn_details"

    id = Column(String, primary_key=True, index=True)
    po_number = Column(String(80), ForeignKey("purchase_orders.po_number"), nullable=False, index=True)
    yarn_type = Column(SQLEnum(YarnType), nullable=False)
    count = Column(String(50), nullable=True)
    colour = Column(String(80), nullable=True)
    qty_kg = Column(Numeric(10, 2), nullable=True)
    bundles = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())