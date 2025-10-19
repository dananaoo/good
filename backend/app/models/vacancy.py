import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Float, ForeignKey, Enum, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db import Base
import enum


class VacancyEmploymentType(str, enum.Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    INTERNSHIP = "internship"
    CONTRACT = "contract"


class WorkSchedule(str, enum.Enum):
    FULL_DAY = "full-day"
    SHIFT = "shift"
    REMOTE = "remote"
    HYBRID = "hybrid"
    FLEXIBLE = "flexible"


class Vacancy(Base):
    __tablename__ = "vacancies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employer_id = Column(UUID(as_uuid=True), ForeignKey("employers.id"), nullable=False)
    title = Column(String(255), nullable=False)
    department = Column(String(255))
    company_name = Column(String(255), nullable=False)
    industry = Column(String(255))
    city = Column(String(255))
    region = Column(String(255))
    country = Column(String(255))
    experience_min = Column(Float)
    experience_max = Column(Float)
    employment_type = Column(Enum(VacancyEmploymentType))
    work_schedule = Column(Enum(WorkSchedule))
    education_level = Column(String(255))
    required_languages = Column(JSONB)
    required_skills = Column(ARRAY(String))
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    currency = Column(String(10))
    responsibilities = Column(ARRAY(String))
    requirements = Column(ARRAY(String))
    conditions = Column(ARRAY(String))
    benefits = Column(ARRAY(String))
    description = Column(Text)
    source_url = Column(Text)
    
    # Interview focus settings (what AI should focus on during interviews)
    interview_focus_resume_fit = Column(Boolean, default=True)  # Profile and vacancy main matches
    interview_focus_hard_skills = Column(Boolean, default=False)  # Technical skills assessment
    interview_focus_soft_skills = Column(Boolean, default=False)  # Soft skills and motivation
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    employer = relationship("Employer", back_populates="vacancies")
    interviews = relationship("Interview", back_populates="vacancy")
