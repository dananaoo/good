from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
import uuid
import os
import aiofiles

from app.db import get_db
from app.core.dependencies import get_current_active_user, require_candidate
from app.models.user import User
from app.models.candidate import Candidate
from app.models.resume import Resume
from app.schemas.resume import ResumeCreate, ResumeResponse, ResumeUpdate

router = APIRouter()


@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_candidate)
):
    """Upload resume file and extract text."""
    # Check file type
    if not file.filename.lower().endswith(('.pdf', '.doc', '.docx')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, DOC, and DOCX files are allowed"
        )
    
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
    
    # Create upload directory if it doesn't exist
    upload_dir = "uploads/resumes"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{file_id}{file_extension}"
    file_path = os.path.join(upload_dir, filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Extract text from file
    resume_text = await extract_text_from_file(file_path, file_extension)
    
    # Create resume record
    db_resume = Resume(
        candidate_id=candidate.id,
        resume_text=resume_text,
        file_url=file_path,
        parsed_json={}  # TODO: Implement structured parsing
    )
    db.add(db_resume)
    await db.commit()
    await db.refresh(db_resume)
    
    return ResumeResponse.model_validate(db_resume)


async def extract_text_from_file(file_path: str, file_extension: str) -> str:
    """Extract text from uploaded file."""
    try:
        if file_extension.lower() == '.pdf':
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
            return text
        
        elif file_extension.lower() in ['.doc', '.docx']:
            from docx import Document
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        
        else:
            return ""
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error extracting text from file: {str(e)}"
        )


@router.get("/me", response_model=List[ResumeResponse])
async def get_my_resumes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_candidate)
):
    """Get current user's resumes."""
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
        select(Resume).where(Resume.candidate_id == candidate.id)
    )
    resumes = result.scalars().all()
    
    return [ResumeResponse.model_validate(resume) for resume in resumes]


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_candidate)
):
    """Get resume by ID."""
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id)
    )
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Check if resume belongs to current user
    result = await db.execute(
        select(Candidate).where(
            and_(
                Candidate.id == resume.candidate_id,
                Candidate.user_id == current_user.id
            )
        )
    )
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return ResumeResponse.model_validate(resume)
