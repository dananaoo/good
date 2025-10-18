import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db import Base


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True))
    event = Column(String(255), nullable=False)
    details = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
