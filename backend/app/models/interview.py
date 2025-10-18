import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Float, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db import Base
import enum


class InterviewStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SCORED = "scored"


class InterviewStage(str, enum.Enum):
    RESUME_FIT = "resume_fit"
    HARD_SKILLS = "hard_skills"
    SOFT_SKILLS = "soft_skills"
    FINISHED = "finished"


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vacancy_id = Column(UUID(as_uuid=True), ForeignKey("vacancies.id"), nullable=False)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    status = Column(Enum(InterviewStatus), default=InterviewStatus.PENDING)
    current_stage = Column(Enum(InterviewStage), default=InterviewStage.RESUME_FIT)
    ai_version = Column(String(50))
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    final_score = Column(Float)
    summary_json = Column(JSONB)  # Summary by categories and reasoning
    notes = Column(Text)  # HR comments
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    vacancy = relationship("Vacancy", back_populates="interviews")
    candidate = relationship("Candidate", back_populates="interviews")
    messages = relationship("InterviewMessage", back_populates="interview")
    evaluation_scores = relationship("EvaluationScore", back_populates="interview")
    evaluation_summary = relationship("EvaluationSummary", back_populates="interview")


class MessageSender(str, enum.Enum):
    BOT = "bot"
    CANDIDATE = "candidate"


class MessageType(str, enum.Enum):
    QUESTION = "question"
    ANSWER = "answer"
    INFO = "info"


class InterviewMessage(Base):
    __tablename__ = "interview_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id"), nullable=False)
    sender = Column(Enum(MessageSender), nullable=False)
    stage = Column(Enum(InterviewStage), nullable=False)
    message_type = Column(Enum(MessageType), nullable=False)
    message = Column(Text, nullable=False)
    ai_generated = Column(Boolean, default=False)
    score_impact = Column(Float)  # If answer affects evaluation
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    interview = relationship("Interview", back_populates="messages")


class EvaluationCategory(str, enum.Enum):
    RESUME_FIT = "resume_fit"
    HARD_SKILLS = "hard_skills"
    SOFT_SKILLS = "soft_skills"


class EvaluationScore(Base):
    __tablename__ = "evaluation_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id"), nullable=False)
    category = Column(Enum(EvaluationCategory), nullable=False)
    score = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)  # Adaptive weight (0-1)
    explanation = Column(Text)

    # Relationships
    interview = relationship("Interview", back_populates="evaluation_scores")


class EvaluationSummary(Base):
    __tablename__ = "evaluation_summary"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id"), nullable=False)
    overall_score = Column(Float, nullable=False)
    breakdown = Column(JSONB)  # {"resume_fit": 82, "hard_skills": 90, "soft_skills": 78}
    reasoning = Column(Text)
    ai_confidence = Column(Float)
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    interview = relationship("Interview", back_populates="evaluation_summary")
