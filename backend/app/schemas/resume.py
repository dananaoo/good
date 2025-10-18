from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
import uuid


class ResumeBase(BaseModel):
    resume_text: Optional[str] = None
    file_url: Optional[str] = None
    parsed_json: Optional[Dict[str, Any]] = None


class ResumeCreate(ResumeBase):
    candidate_id: uuid.UUID


class ResumeUpdate(BaseModel):
    resume_text: Optional[str] = None
    file_url: Optional[str] = None
    parsed_json: Optional[Dict[str, Any]] = None


class ResumeResponse(ResumeBase):
    id: uuid.UUID
    candidate_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
