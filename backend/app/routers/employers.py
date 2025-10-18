from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from app.db import get_db
from app.core.dependencies import get_current_active_user, require_employer
from app.models.user import User
from app.models.employer import Employer
from app.schemas.employer import EmployerCreate, EmployerResponse, EmployerUpdate

router = APIRouter()


@router.post("/", response_model=EmployerResponse)
async def create_employer(
    employer_data: EmployerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employer)
):
    """Create employer profile."""
    # Check if employer already exists for this user
    result = await db.execute(
        select(Employer).where(Employer.user_id == current_user.id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employer profile already exists"
        )
    
    db_employer = Employer(
        user_id=current_user.id,
        **employer_data.model_dump()
    )
    db.add(db_employer)
    await db.commit()
    await db.refresh(db_employer)
    
    return EmployerResponse.model_validate(db_employer)


@router.get("/me", response_model=EmployerResponse)
async def get_my_employer_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employer)
):
    """Get current user's employer profile."""
    result = await db.execute(
        select(Employer).where(Employer.user_id == current_user.id)
    )
    employer = result.scalar_one_or_none()
    
    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer profile not found"
        )
    
    return EmployerResponse.model_validate(employer)


@router.put("/me", response_model=EmployerResponse)
async def update_my_employer_profile(
    employer_update: EmployerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employer)
):
    """Update current user's employer profile."""
    result = await db.execute(
        select(Employer).where(Employer.user_id == current_user.id)
    )
    employer = result.scalar_one_or_none()
    
    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer profile not found"
        )
    
    update_data = employer_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employer, field, value)
    
    await db.commit()
    await db.refresh(employer)
    
    return EmployerResponse.model_validate(employer)


@router.get("/{employer_id}", response_model=EmployerResponse)
async def get_employer(
    employer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get employer by ID."""
    result = await db.execute(
        select(Employer).where(Employer.id == employer_id)
    )
    employer = result.scalar_one_or_none()
    
    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer not found"
        )
    
    return EmployerResponse.model_validate(employer)
