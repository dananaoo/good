from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
from app.models.vacancy import VacancyEmploymentType, WorkSchedule
from uuid import UUID


class VacancyBase(BaseModel):
    title: str
    department: Optional[str] = None
    company_name: str
    industry: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    experience_min: Optional[float] = None
    experience_max: Optional[float] = None
    employment_type: Optional[VacancyEmploymentType] = None
    work_schedule: Optional[WorkSchedule] = None
    education_level: Optional[str] = None
    required_languages: Optional[Dict[str, Any]] = None
    required_skills: Optional[List[str]] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    requirements: Optional[List[str]] = None
    conditions: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    
    # Interview focus settings
    interview_focus_resume_fit: Optional[bool] = True
    interview_focus_hard_skills: Optional[bool] = False
    interview_focus_soft_skills: Optional[bool] = False


class VacancyCreate(VacancyBase):
    employer_id: uuid.UUID


class VacancyUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    company_name: Optional[str] = None
    industry: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    experience_min: Optional[float] = None
    experience_max: Optional[float] = None
    employment_type: Optional[VacancyEmploymentType] = None
    work_schedule: Optional[WorkSchedule] = None
    education_level: Optional[str] = None
    required_languages: Optional[Dict[str, Any]] = None
    required_skills: Optional[List[str]] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    requirements: Optional[List[str]] = None
    conditions: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Interview focus settings
    interview_focus_resume_fit: Optional[bool] = None
    interview_focus_hard_skills: Optional[bool] = None
    interview_focus_soft_skills: Optional[bool] = None


class VacancyResponse(VacancyBase):
    id: uuid.UUID
    employer_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
