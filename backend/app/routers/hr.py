from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
import uuid

from app.db import get_db
from app.core.dependencies import require_employer
from app.models.user import User
from app.models.interview import Interview, InterviewStatus, InterviewMessage, EvaluationSummary
from app.models.candidate import Candidate
from app.models.vacancy import Vacancy
from app.models.employer import Employer
from app.models.resume import Resume
from app.schemas.interview import InterviewResponse, EvaluationSummaryResponse

router = APIRouter()


@router.get("/interviews", response_model=List[InterviewResponse])
async def get_hr_interviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[InterviewStatus] = None,
    vacancy_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employer)
):
    """Get interviews for HR dashboard with candidate and vacancy details."""
    # Get employer profile
    result = await db.execute(
        select(Employer).where(Employer.user_id == current_user.id)
    )
    employer = result.scalar_one_or_none()
    
    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer profile not found"
        )
    
    # Build query with joins
    query = select(Interview).join(Vacancy).where(Vacancy.employer_id == employer.id)
    
    # Apply filters
    filters = []
    
    if status:
        filters.append(Interview.status == status)
    
    if vacancy_id:
        filters.append(Interview.vacancy_id == uuid.UUID(vacancy_id))
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(skip).limit(limit).order_by(Interview.created_at.desc())
    
    result = await db.execute(query)
    interviews = result.scalars().all()
    
    return [InterviewResponse.model_validate(interview) for interview in interviews]


@router.get("/interviews/{interview_id}", response_model=InterviewResponse)
async def get_hr_interview_detail(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employer)
):
    """Get detailed interview information for HR."""
    # Get employer profile
    result = await db.execute(
        select(Employer).where(Employer.user_id == current_user.id)
    )
    employer = result.scalar_one_or_none()
    
    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer profile not found"
        )
    
    # Get interview with verification
    result = await db.execute(
        select(Interview).join(Vacancy).where(
            and_(
                Interview.id == interview_id,
                Vacancy.employer_id == employer.id
            )
        )
    )
    interview = result.scalar_one_or_none()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    return InterviewResponse.model_validate(interview)


@router.get("/interviews/{interview_id}/messages")
async def get_interview_messages(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employer)
):
    """Get all messages from an interview."""
    # Verify access
    result = await db.execute(
        select(Employer).where(Employer.user_id == current_user.id)
    )
    employer = result.scalar_one_or_none()
    
    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer profile not found"
        )
    
    # Get interview with verification
    result = await db.execute(
        select(Interview).join(Vacancy).where(
            and_(
                Interview.id == interview_id,
                Vacancy.employer_id == employer.id
            )
        )
    )
    interview = result.scalar_one_or_none()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    # Get messages
    result = await db.execute(
        select(InterviewMessage).where(InterviewMessage.interview_id == interview.id)
        .order_by(InterviewMessage.created_at)
    )
    messages = result.scalars().all()
    
    return [
        {
            "id": str(msg.id),
            "sender": msg.sender.value,
            "stage": msg.stage.value,
            "message_type": msg.message_type.value,
            "message": msg.message,
            "created_at": msg.created_at.isoformat()
        }
        for msg in messages
    ]


@router.get("/interviews/{interview_id}/evaluation", response_model=EvaluationSummaryResponse)
async def get_interview_evaluation(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employer)
):
    """Get interview evaluation summary."""
    # Verify access
    result = await db.execute(
        select(Employer).where(Employer.user_id == current_user.id)
    )
    employer = result.scalar_one_or_none()
    
    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer profile not found"
        )
    
    # Get interview with verification
    result = await db.execute(
        select(Interview).join(Vacancy).where(
            and_(
                Interview.id == interview_id,
                Vacancy.employer_id == employer.id
            )
        )
    )
    interview = result.scalar_one_or_none()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    # Get evaluation summary
    result = await db.execute(
        select(EvaluationSummary).where(EvaluationSummary.interview_id == interview.id)
    )
    evaluation = result.scalar_one_or_none()
    
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found"
        )
    
    return EvaluationSummaryResponse.model_validate(evaluation)


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employer)
):
    """Get HR dashboard statistics."""
    # Get employer profile
    result = await db.execute(
        select(Employer).where(Employer.user_id == current_user.id)
    )
    employer = result.scalar_one_or_none()
    
    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer profile not found"
        )
    
    # Get employer's vacancies
    result = await db.execute(
        select(Vacancy).where(Vacancy.employer_id == employer.id)
    )
    vacancies = result.scalars().all()
    vacancy_ids = [v.id for v in vacancies]
    
    if not vacancy_ids:
        return {
            "total_interviews": 0,
            "completed_interviews": 0,
            "pending_interviews": 0,
            "average_score": 0,
            "total_vacancies": 0,
            "active_vacancies": 0
        }
    
    # Get interview statistics
    result = await db.execute(
        select(func.count(Interview.id)).where(Interview.vacancy_id.in_(vacancy_ids))
    )
    total_interviews = result.scalar() or 0
    
    result = await db.execute(
        select(func.count(Interview.id)).where(
            and_(
                Interview.vacancy_id.in_(vacancy_ids),
                Interview.status == InterviewStatus.COMPLETED
            )
        )
    )
    completed_interviews = result.scalar() or 0
    
    result = await db.execute(
        select(func.count(Interview.id)).where(
            and_(
                Interview.vacancy_id.in_(vacancy_ids),
                Interview.status == InterviewStatus.PENDING
            )
        )
    )
    pending_interviews = result.scalar() or 0
    
    # Get average score
    result = await db.execute(
        select(func.avg(Interview.final_score)).where(
            and_(
                Interview.vacancy_id.in_(vacancy_ids),
                Interview.final_score.isnot(None)
            )
        )
    )
    average_score = result.scalar() or 0
    
    # Get vacancy statistics
    total_vacancies = len(vacancies)
    active_vacancies = len([v for v in vacancies if v.is_active])
    
    return {
        "total_interviews": total_interviews,
        "completed_interviews": completed_interviews,
        "pending_interviews": pending_interviews,
        "average_score": round(average_score, 1) if average_score else 0,
        "total_vacancies": total_vacancies,
        "active_vacancies": active_vacancies
    }
