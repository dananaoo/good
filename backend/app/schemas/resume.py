from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class ResumeBase(BaseModel):
    resume_text: Optional[str] = None
    file_url: Optional[str] = None
    parsed_json: Optional[Dict[str, Any]] = None


class ResumeCreate(ResumeBase):
    candidate_id: str


class ResumeUpdate(BaseModel):
    resume_text: Optional[str] = None
    file_url: Optional[str] = None
    parsed_json: Optional[Dict[str, Any]] = None


class ResumeResponse(ResumeBase):
    id: str
    candidate_id: str
    created_at: datetime

    class Config:
        from_attributes = True
