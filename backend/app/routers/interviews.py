from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
import uuid

from app.db import get_db
from app.core.dependencies import get_current_active_user, require_employer_or_candidate
from app.models.user import User
from app.models.interview import Interview, InterviewStatus, InterviewStage
from app.models.candidate import Candidate
from app.models.vacancy import Vacancy
from app.models.employer import Employer
from app.schemas.interview import InterviewCreate, InterviewResponse, InterviewUpdate
from app.websocket.interview import websocket_endpoint

router = APIRouter()


@router.post("/", response_model=InterviewResponse)
async def create_interview(
    interview_data: InterviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employer_or_candidate)
):
    """Create a new interview."""
    # Verify candidate and vacancy exist
    result = await db.execute(
        select(Candidate).where(Candidate.id == uuid.UUID(interview_data.candidate_id))
    )
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    result = await db.execute(
        select(Vacancy).where(Vacancy.id == uuid.UUID(interview_data.vacancy_id))
    )
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    # Check if interview already exists
    result = await db.execute(
        select(Interview).where(
            and_(
                Interview.candidate_id == uuid.UUID(interview_data.candidate_id),
                Interview.vacancy_id == uuid.UUID(interview_data.vacancy_id)
            )
        )
    )
    existing_interview = result.scalar_one_or_none()
    
    if existing_interview:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview already exists for this candidate and vacancy"
        )
    
    # Create interview
    db_interview = Interview(
        **interview_data.model_dump()
    )
    db.add(db_interview)
    await db.commit()
    await db.refresh(db_interview)
    
    return InterviewResponse.model_validate(db_interview)


@router.get("/", response_model=List[InterviewResponse])
async def get_interviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[InterviewStatus] = None,
    candidate_id: Optional[str] = None,
    vacancy_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employer_or_candidate)
):
    """Get list of interviews with optional filtering."""
    query = select(Interview)
    
    # Apply filters
    filters = []
    
    if status:
        filters.append(Interview.status == status)
    
    if candidate_id:
        filters.append(Interview.candidate_id == uuid.UUID(candidate_id))
    
    if vacancy_id:
        filters.append(Interview.vacancy_id == uuid.UUID(vacancy_id))
    
    # Role-based filtering
    if current_user.role.value == "candidate":
        # Candidates can only see their own interviews
        result = await db.execute(
            select(Candidate).where(Candidate.user_id == current_user.id)
        )
        candidate = result.scalar_one_or_none()
        
        if candidate:
            filters.append(Interview.candidate_id == candidate.id)
        else:
            return []  # No candidate profile means no interviews
    
    elif current_user.role.value == "employer":
        # Employers can only see interviews for their vacancies
        result = await db.execute(
            select(Employer).where(Employer.user_id == current_user.id)
        )
        employer = result.scalar_one_or_none()
        
        if employer:
            result = await db.execute(
                select(Vacancy).where(Vacancy.employer_id == employer.id)
            )
            vacancies = result.scalars().all()
            vacancy_ids = [v.id for v in vacancies]
            
            if vacancy_ids:
                filters.append(Interview.vacancy_id.in_(vacancy_ids))
            else:
                return []  # No vacancies means no interviews
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(skip).limit(limit).order_by(Interview.created_at.desc())
    
    result = await db.execute(query)
    interviews = result.scalars().all()
    
    return [InterviewResponse.model_validate(interview) for interview in interviews]


@router.get("/{interview_id}", response_model=InterviewResponse)
async def get_interview(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employer_or_candidate)
):
    """Get interview by ID."""
    result = await db.execute(
        select(Interview).where(Interview.id == interview_id)
    )
    interview = result.scalar_one_or_none()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    # Check permissions
    if current_user.role.value == "candidate":
        result = await db.execute(
            select(Candidate).where(Candidate.user_id == current_user.id)
        )
        candidate = result.scalar_one_or_none()
        
        if not candidate or interview.candidate_id != candidate.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    elif current_user.role.value == "employer":
        result = await db.execute(
            select(Employer).where(Employer.user_id == current_user.id)
        )
        employer = result.scalar_one_or_none()
        
        if employer:
            result = await db.execute(
                select(Vacancy).where(
                    and_(
                        Vacancy.id == interview.vacancy_id,
                        Vacancy.employer_id == employer.id
                    )
                )
            )
            vacancy = result.scalar_one_or_none()
            
            if not vacancy:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
    
    return InterviewResponse.model_validate(interview)


@router.put("/{interview_id}", response_model=InterviewResponse)
async def update_interview(
    interview_id: uuid.UUID,
    interview_update: InterviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employer_or_candidate)
):
    """Update interview."""
    result = await db.execute(
        select(Interview).where(Interview.id == interview_id)
    )
    interview = result.scalar_one_or_none()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    # Only employers can update interviews (add notes, etc.)
    if current_user.role.value != "employer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employers can update interviews"
        )
    
    # Verify employer owns the vacancy
    result = await db.execute(
        select(Employer).where(Employer.user_id == current_user.id)
    )
    employer = result.scalar_one_or_none()
    
    if employer:
        result = await db.execute(
            select(Vacancy).where(
                and_(
                    Vacancy.id == interview.vacancy_id,
                    Vacancy.employer_id == employer.id
                )
            )
        )
        vacancy = result.scalar_one_or_none()
        
        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    update_data = interview_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(interview, field, value)
    
    await db.commit()
    await db.refresh(interview)
    
    return InterviewResponse.model_validate(interview)


@router.websocket("/ws/{interview_id}")
async def websocket_interview(websocket: WebSocket, interview_id: uuid.UUID):
    """WebSocket endpoint for real-time interview communication."""
    await websocket_endpoint(websocket, str(interview_id))
