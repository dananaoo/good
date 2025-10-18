from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
from app.models.interview import InterviewStatus, InterviewStage, MessageSender, MessageType, EvaluationCategory


class InterviewBase(BaseModel):
    vacancy_id: str
    candidate_id: str
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
    id: str
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
    interview_id: str
    sender: MessageSender
    stage: InterviewStage
    message_type: MessageType
    message: str
    ai_generated: bool = False
    score_impact: Optional[float] = None


class InterviewMessageCreate(InterviewMessageBase):
    pass


class InterviewMessageResponse(InterviewMessageBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# Evaluation schemas
class EvaluationScoreBase(BaseModel):
    interview_id: str
    category: EvaluationCategory
    score: float
    weight: float
    explanation: Optional[str] = None


class EvaluationScoreCreate(EvaluationScoreBase):
    pass


class EvaluationScoreResponse(EvaluationScoreBase):
    id: str

    class Config:
        from_attributes = True


class EvaluationSummaryBase(BaseModel):
    interview_id: str
    overall_score: float
    breakdown: Dict[str, Any]
    reasoning: Optional[str] = None
    ai_confidence: Optional[float] = None


class EvaluationSummaryCreate(EvaluationSummaryBase):
    pass


class EvaluationSummaryResponse(EvaluationSummaryBase):
    id: str
    generated_at: datetime

    class Config:
        from_attributes = True
