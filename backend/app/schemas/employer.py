from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class EmployerBase(BaseModel):
    company_name: str
    industry: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None


class EmployerCreate(EmployerBase):
    pass


class EmployerUpdate(BaseModel):
    company_name: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    verified: Optional[bool] = None


class EmployerResponse(EmployerBase):
    id: UUID
    user_id: UUID
    verified: bool
    created_at: datetime

    class Config:
        from_attributes = True
