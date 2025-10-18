import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EMPLOYER = "employer"
    CANDIDATE = "candidate"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    employer = relationship("Employer", back_populates="user", uselist=False)
    candidate = relationship("Candidate", back_populates="user", uselist=False)
