from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid

from app.db import get_db
from app.core.dependencies import get_current_active_user, require_candidate, require_employer_or_candidate
from app.models.user import User
from app.models.candidate import (
    Candidate, CandidateExperience, CandidateEducation, 
    CandidateSkill, CandidateLanguage, CandidateAchievement, CandidateLink
)
from app.schemas.candidate import (
    CandidateCreate, CandidateResponse, CandidateUpdate,
    CandidateExperienceCreate, CandidateExperienceResponse,
    CandidateEducationCreate, CandidateEducationResponse,
    CandidateSkillCreate, CandidateSkillResponse,
    CandidateLanguageCreate, CandidateLanguageResponse,
    CandidateAchievementCreate, CandidateAchievementResponse,
    CandidateLinkCreate, CandidateLinkResponse
)

router = APIRouter()


@router.post("/", response_model=CandidateResponse)
async def create_candidate(
    candidate_data: CandidateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_candidate)
):
    """Create candidate profile."""
    # Check if candidate already exists for this user
    result = await db.execute(
        select(Candidate).where(Candidate.user_id == current_user.id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate profile already exists"
        )
    
    db_candidate = Candidate(
        user_id=current_user.id,
        **candidate_data.model_dump()
    )
    db.add(db_candidate)
    await db.commit()
    await db.refresh(db_candidate)
    
    return CandidateResponse.model_validate(db_candidate)


@router.get("/me", response_model=CandidateResponse)
async def get_my_candidate_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_candidate)
):
    """Get current user's candidate profile."""
    result = await db.execute(
        select(Candidate).where(Candidate.user_id == current_user.id)
    )
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found"
        )
    
    return CandidateResponse.model_validate(candidate)


@router.put("/me", response_model=CandidateResponse)
async def update_my_candidate_profile(
    candidate_update: CandidateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_candidate)
):
    """Update current user's candidate profile."""
    result = await db.execute(
        select(Candidate).where(Candidate.user_id == current_user.id)
    )
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found"
        )
    
    update_data = candidate_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(candidate, field, value)
    
    await db.commit()
    await db.refresh(candidate)
    
    return CandidateResponse.model_validate(candidate)


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employer_or_candidate)
):
    """Get candidate by ID."""
    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    return CandidateResponse.model_validate(candidate)


# Experience endpoints
@router.post("/me/experiences", response_model=CandidateExperienceResponse)
async def add_experience(
    experience_data: CandidateExperienceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_candidate)
):
    """Add work experience to candidate profile."""
    # Get candidate profile
    result = await db.execute(
        select(Candidate).where(Candidate.user_id == current_user.id)
    )
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found"
        )
    
    db_experience = CandidateExperience(
        candidate_id=candidate.id,
        **experience_data.model_dump()
    )
    db.add(db_experience)
    await db.commit()
    await db.refresh(db_experience)
    
    return CandidateExperienceResponse.model_validate(db_experience)


@router.get("/me/experiences", response_model=List[CandidateExperienceResponse])
async def get_my_experiences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_candidate)
):
    """Get current user's work experiences."""
    result = await db.execute(
        select(Candidate).where(Candidate.user_id == current_user.id)
    )
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found"
        )
    
    result = await db.execute(
        select(CandidateExperience).where(CandidateExperience.candidate_id == candidate.id)
    )
    experiences = result.scalars().all()
    
    return [CandidateExperienceResponse.model_validate(exp) for exp in experiences]


# Education endpoints
@router.post("/me/educations", response_model=CandidateEducationResponse)
async def add_education(
    education_data: CandidateEducationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_candidate)
):
    """Add education to candidate profile."""
    # Get candidate profile
    result = await db.execute(
        select(Candidate).where(Candidate.user_id == current_user.id)
    )
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found"
        )
    
    db_education = CandidateEducation(
        candidate_id=candidate.id,
        **education_data.model_dump()
    )
    db.add(db_education)
    await db.commit()
    await db.refresh(db_education)
    
    return CandidateEducationResponse.model_validate(db_education)


@router.get("/me/educations", response_model=List[CandidateEducationResponse])
async def get_my_educations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_candidate)
):
    """Get current user's education records."""
    result = await db.execute(
        select(Candidate).where(Candidate.user_id == current_user.id)
    )
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found"
        )
    
    result = await db.execute(
        select(CandidateEducation).where(CandidateEducation.candidate_id == candidate.id)
    )
    educations = result.scalars().all()
    
    return [CandidateEducationResponse.model_validate(edu) for edu in educations]


# Skills endpoints
@router.post("/me/skills", response_model=CandidateSkillResponse)
async def add_skill(
    skill_data: CandidateSkillCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_candidate)
):
    """Add skill to candidate profile."""
    # Get candidate profile
    result = await db.execute(
        select(Candidate).where(Candidate.user_id == current_user.id)
    )
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found"
        )
    
    db_skill = CandidateSkill(
        candidate_id=candidate.id,
        **skill_data.model_dump()
    )
    db.add(db_skill)
    await db.commit()
    await db.refresh(db_skill)
    
    return CandidateSkillResponse.model_validate(db_skill)


@router.get("/me/skills", response_model=List[CandidateSkillResponse])
async def get_my_skills(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_candidate)
):
    """Get current user's skills."""
    result = await db.execute(
        select(Candidate).where(Candidate.user_id == current_user.id)
    )
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found"
        )
    
    result = await db.execute(
        select(CandidateSkill).where(CandidateSkill.candidate_id == candidate.id)
    )
    skills = result.scalars().all()
    
    return [CandidateSkillResponse.model_validate(skill) for skill in skills]
