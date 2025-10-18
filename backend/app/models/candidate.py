import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Text, DateTime, Date, Integer, Boolean, ForeignKey, Enum, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base
import enum


class EmploymentType(str, enum.Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    REMOTE = "remote"
    HYBRID = "hybrid"
    INTERNSHIP = "internship"


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    full_name = Column(String(255), nullable=False)
    city = Column(String(255))
    country = Column(String(255))
    citizenship = Column(String(255))
    birth_date = Column(Date)
    phone = Column(String(50))
    email = Column(String(255))
    expected_salary = Column(Integer)
    currency = Column(String(10))
    employment_type = Column(Enum(EmploymentType))
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="candidate")
    experiences = relationship("CandidateExperience", back_populates="candidate")
    educations = relationship("CandidateEducation", back_populates="candidate")
    skills = relationship("CandidateSkill", back_populates="candidate")
    languages = relationship("CandidateLanguage", back_populates="candidate")
    achievements = relationship("CandidateAchievement", back_populates="candidate")
    links = relationship("CandidateLink", back_populates="candidate")
    resumes = relationship("Resume", back_populates="candidate")
    interviews = relationship("Interview", back_populates="candidate")


class CandidateExperience(Base):
    __tablename__ = "candidate_experiences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    company_name = Column(String(255), nullable=False)
    position = Column(String(255), nullable=False)
    industry = Column(String(255))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    responsibilities = Column(Text)
    achievements = Column(Text)
    technologies = Column(ARRAY(String))

    # Relationships
    candidate = relationship("Candidate", back_populates="experiences")


class CandidateEducation(Base):
    __tablename__ = "candidate_educations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    institution = Column(String(255), nullable=False)
    degree = Column(String(255), nullable=False)
    field_of_study = Column(String(255))
    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer)
    is_current = Column(Boolean, default=False)

    # Relationships
    candidate = relationship("Candidate", back_populates="educations")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    skill_name = Column(String(100), nullable=False)
    skill_level = Column(Integer)  # 1-5 rating
    category = Column(String(50))  # "Hard", "Soft", "Language"

    # Relationships
    candidate = relationship("Candidate", back_populates="skills")


class CandidateLanguage(Base):
    __tablename__ = "candidate_languages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    language = Column(String(50), nullable=False)
    level = Column(String(20))  # "Native", "B2", etc.

    # Relationships
    candidate = relationship("Candidate", back_populates="languages")


class CandidateAchievement(Base):
    __tablename__ = "candidate_achievements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    organization = Column(String(255))
    date = Column(Date)

    # Relationships
    candidate = relationship("Candidate", back_populates="achievements")


class CandidateLink(Base):
    __tablename__ = "candidate_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    type = Column(String(50), nullable=False)  # "LinkedIn", "GitHub", "Portfolio"
    url = Column(Text, nullable=False)

    # Relationships
    candidate = relationship("Candidate", back_populates="links")
