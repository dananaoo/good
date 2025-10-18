from pydantic import BaseModel
from datetime import datetime
from typing import Optional


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
    id: str
    user_id: str
    verified: bool
    created_at: datetime

    class Config:
        from_attributes = True
