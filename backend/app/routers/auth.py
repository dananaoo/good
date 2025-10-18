from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from app.db import get_db
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.dependencies import get_current_active_user
from app.models.user import User, UserRole
from app.models.employer import Employer
from app.models.candidate import Candidate
from app.schemas.user import UserCreate, UserResponse, Token, UserLogin
from app.schemas.employer import EmployerCreate
from app.schemas.candidate import CandidateCreate

router = APIRouter()


@router.post("/register/employer", response_model=Token)
async def register_employer(
    user_data: UserCreate,
    employer_data: EmployerCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new employer."""
    if user_data.role != UserRole.EMPLOYER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role for employer registration"
        )
    
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role
    )
    db.add(db_user)
    await db.flush()  # Get the user ID
    
    # Create employer profile
    db_employer = Employer(
        user_id=db_user.id,
        **employer_data.model_dump()
    )
    db.add(db_employer)
    
    await db.commit()
    await db.refresh(db_user)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(db_user.id), "role": db_user.role.value}
    )
    
    return Token(
        access_token=access_token,
        user=UserResponse.model_validate(db_user)
    )


@router.post("/register/candidate", response_model=Token)
async def register_candidate(
    user_data: UserCreate,
    candidate_data: CandidateCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new candidate."""
    if user_data.role != UserRole.CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role for candidate registration"
        )
    
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role
    )
    db.add(db_user)
    await db.flush()  # Get the user ID
    
    # Create candidate profile
    db_candidate = Candidate(
        user_id=db_user.id,
        **candidate_data.model_dump()
    )
    db.add(db_candidate)
    
    await db.commit()
    await db.refresh(db_user)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(db_user.id), "role": db_user.role.value}
    )
    
    return Token(
        access_token=access_token,
        user=UserResponse.model_validate(db_user)
    )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Login user."""
    # Get user by email
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )
    
    return Token(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information."""
    return UserResponse.model_validate(current_user)
