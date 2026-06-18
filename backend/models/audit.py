from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from backend.database import Base


class AuditLog(Base):
    """Append-only record of every mutating API call — who did what, when, on which
    entity, and whether it succeeded. Written by the audit middleware in main.py."""
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, index=True)
    username = Column(String(150), nullable=True, index=True)
    action = Column(String(30), nullable=True)        # create / update / delete / login / ...
    entity = Column(String(60), nullable=True, index=True)
    entity_id = Column(String(160), nullable=True)
    method = Column(String(10), nullable=True)
    path = Column(String(300), nullable=True)
    status_code = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
