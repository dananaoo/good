from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional, List
from app.models.candidate import EmploymentType
from uuid import UUID

class CandidateBase(BaseModel):
    full_name: str
    city: Optional[str] = None
    country: Optional[str] = None
    citizenship: Optional[str] = None
    birth_date: Optional[date] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    expected_salary: Optional[int] = None
    currency: Optional[str] = None
    employment_type: Optional[EmploymentType] = None
    summary: Optional[str] = None


class CandidateCreate(CandidateBase):
    pass


class CandidateUpdate(BaseModel):
    full_name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    citizenship: Optional[str] = None
    birth_date: Optional[date] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    expected_salary: Optional[int] = None
    currency: Optional[str] = None
    employment_type: Optional[EmploymentType] = None
    summary: Optional[str] = None


class CandidateResponse(CandidateBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Experience schemas
class CandidateExperienceBase(BaseModel):
    company_name: str
    position: str
    industry: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    responsibilities: Optional[str] = None
    achievements: Optional[str] = None
    technologies: Optional[List[str]] = None


class CandidateExperienceCreate(CandidateExperienceBase):
    pass


class CandidateExperienceResponse(CandidateExperienceBase):
    id: str
    candidate_id: str

    class Config:
        from_attributes = True


# Education schemas
class CandidateEducationBase(BaseModel):
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_year: int
    end_year: Optional[int] = None
    is_current: bool = False


class CandidateEducationCreate(CandidateEducationBase):
    pass


class CandidateEducationResponse(CandidateEducationBase):
    id: str
    candidate_id: str

    class Config:
        from_attributes = True


# Skill schemas
class CandidateSkillBase(BaseModel):
    skill_name: str
    skill_level: Optional[int] = None  # 1-5 rating
    category: Optional[str] = None


class CandidateSkillCreate(CandidateSkillBase):
    pass


class CandidateSkillResponse(CandidateSkillBase):
    id: str
    candidate_id: str

    class Config:
        from_attributes = True


# Language schemas
class CandidateLanguageBase(BaseModel):
    language: str
    level: Optional[str] = None


class CandidateLanguageCreate(CandidateLanguageBase):
    pass


class CandidateLanguageResponse(CandidateLanguageBase):
    id: str
    candidate_id: str

    class Config:
        from_attributes = True


# Achievement schemas
class CandidateAchievementBase(BaseModel):
    title: str
    description: Optional[str] = None
    organization: Optional[str] = None
    date: Optional[date] = None


class CandidateAchievementCreate(CandidateAchievementBase):
    pass


class CandidateAchievementResponse(CandidateAchievementBase):
    id: str
    candidate_id: str

    class Config:
        from_attributes = True


# Link schemas
class CandidateLinkBase(BaseModel):
    type: str  # "LinkedIn", "GitHub", "Portfolio"
    url: str


class CandidateLinkCreate(CandidateLinkBase):
    pass


class CandidateLinkResponse(CandidateLinkBase):
    id: str
    candidate_id: str

    class Config:
        from_attributes = True
