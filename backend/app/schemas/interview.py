from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
import uuid
from app.models.interview import InterviewStatus, InterviewStage, MessageSender, MessageType, EvaluationCategory


class InterviewBase(BaseModel):
    vacancy_id: uuid.UUID
    candidate_id: uuid.UUID
    ai_version: Optional[str] = None


class InterviewCreate(InterviewBase):
    pass


class InterviewUpdate(BaseModel):
    status: Optional[InterviewStatus] = None
    current_stage: Optional[InterviewStage] = None
    ai_version: Optional[str] = None
    ended_at: Optional[datetime] = None
    final_score: Optional[float] = None
    summary_json: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class InterviewResponse(InterviewBase):
    id: uuid.UUID
    status: InterviewStatus
    current_stage: InterviewStage
    started_at: datetime
    ended_at: Optional[datetime] = None
    final_score: Optional[float] = None
    summary_json: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Message schemas
class InterviewMessageBase(BaseModel):
    interview_id: uuid.UUID
    sender: MessageSender
    stage: InterviewStage
    message_type: MessageType
    message: str
    ai_generated: bool = False
    score_impact: Optional[float] = None


class InterviewMessageCreate(InterviewMessageBase):
    pass


class InterviewMessageResponse(InterviewMessageBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


# Evaluation schemas
class EvaluationScoreBase(BaseModel):
    interview_id: uuid.UUID
    category: EvaluationCategory
    score: float
    weight: float
    explanation: Optional[str] = None


class EvaluationScoreCreate(EvaluationScoreBase):
    pass


class EvaluationScoreResponse(EvaluationScoreBase):
    id: uuid.UUID

    class Config:
        from_attributes = True


class EvaluationSummaryBase(BaseModel):
    interview_id: uuid.UUID
    overall_score: float
    breakdown: Dict[str, Any]
    reasoning: Optional[str] = None
    ai_confidence: Optional[float] = None


class EvaluationSummaryCreate(EvaluationSummaryBase):
    pass


class EvaluationSummaryResponse(EvaluationSummaryBase):
    id: uuid.UUID
    generated_at: datetime

    class Config:
        from_attributes = True
