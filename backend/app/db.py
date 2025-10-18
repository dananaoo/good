from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        # Import all models to ensure they are registered
        from app.models import (
            User, Employer, Candidate, CandidateExperience, CandidateEducation,
            CandidateSkill, CandidateLanguage, CandidateAchievement, CandidateLink,
            Resume, Vacancy, Interview, InterviewMessage, EvaluationScore,
            EvaluationSummary, SystemLog
        )
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
