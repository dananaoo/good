from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
import uuid

from app.db import get_db
from app.core.dependencies import get_current_active_user, require_employer
from app.models.user import User
from app.models.vacancy import Vacancy
from app.schemas.vacancy import VacancyCreate, VacancyResponse, VacancyUpdate

router = APIRouter()


@router.post("/", response_model=VacancyResponse)
async def create_vacancy(
    vacancy_data: VacancyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employer)
):
    """Create a new vacancy."""
    # Get employer profile
    from app.models.employer import Employer
    result = await db.execute(
        select(Employer).where(Employer.user_id == current_user.id)
    )
    employer = result.scalar_one_or_none()
    
    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer profile not found"
        )
    
    db_vacancy = Vacancy(
        employer_id=employer.id,
        **vacancy_data.model_dump()
    )
    db.add(db_vacancy)
    await db.commit()
    await db.refresh(db_vacancy)
    
    return VacancyResponse.model_validate(db_vacancy)


@router.get("/", response_model=List[VacancyResponse])
async def get_vacancies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    city: Optional[str] = None,
    employment_type: Optional[str] = None,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get list of vacancies with optional filtering."""
    query = select(Vacancy)
    
    # Apply filters
    filters = [Vacancy.is_active == is_active]
    
    if city:
        filters.append(Vacancy.city.ilike(f"%{city}%"))
    
    if employment_type:
        filters.append(Vacancy.employment_type == employment_type)
    
    query = query.where(and_(*filters))
    query = query.offset(skip).limit(limit).order_by(Vacancy.created_at.desc())
    
    result = await db.execute(query)
    vacancies = result.scalars().all()
    
    return [VacancyResponse.model_validate(vacancy) for vacancy in vacancies]


@router.get("/my", response_model=List[VacancyResponse])
async def get_my_vacancies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employer)
):
    """Get current employer's vacancies."""
    # Get employer profile
    from app.models.employer import Employer
    result = await db.execute(
        select(Employer).where(Employer.user_id == current_user.id)
    )
    employer = result.scalar_one_or_none()
    
    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer profile not found"
        )
    
    query = select(Vacancy).where(Vacancy.employer_id == employer.id)
    query = query.offset(skip).limit(limit).order_by(Vacancy.created_at.desc())
    
    result = await db.execute(query)
    vacancies = result.scalars().all()
    
    return [VacancyResponse.model_validate(vacancy) for vacancy in vacancies]


@router.get("/{vacancy_id}", response_model=VacancyResponse)
async def get_vacancy(
    vacancy_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get vacancy by ID."""
    result = await db.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    return VacancyResponse.model_validate(vacancy)


@router.put("/{vacancy_id}", response_model=VacancyResponse)
async def update_vacancy(
    vacancy_id: uuid.UUID,
    vacancy_update: VacancyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employer)
):
    """Update vacancy."""
    # Get employer profile
    from app.models.employer import Employer
    result = await db.execute(
        select(Employer).where(Employer.user_id == current_user.id)
    )
    employer = result.scalar_one_or_none()
    
    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer profile not found"
        )
    
    # Get vacancy
    result = await db.execute(
        select(Vacancy).where(
            and_(
                Vacancy.id == vacancy_id,
                Vacancy.employer_id == employer.id
            )
        )
    )
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    update_data = vacancy_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vacancy, field, value)
    
    await db.commit()
    await db.refresh(vacancy)
    
    return VacancyResponse.model_validate(vacancy)


@router.delete("/{vacancy_id}")
async def delete_vacancy(
    vacancy_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employer)
):
    """Delete vacancy (soft delete by setting is_active=False)."""
    # Get employer profile
    from app.models.employer import Employer
    result = await db.execute(
        select(Employer).where(Employer.user_id == current_user.id)
    )
    employer = result.scalar_one_or_none()
    
    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer profile not found"
        )
    
    # Get vacancy
    result = await db.execute(
        select(Vacancy).where(
            and_(
                Vacancy.id == vacancy_id,
                Vacancy.employer_id == employer.id
            )
        )
    )
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    vacancy.is_active = False
    await db.commit()
    
    return {"message": "Vacancy deleted successfully"}
