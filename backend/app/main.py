from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db import init_db
from app.routers import auth, candidates, employers, vacancies, interviews, hr, resumes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="SmartBot 2.0 API",
    description="AI recruiter chatbot backend for conducting real-time interviews",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(candidates.router, prefix="/api/candidates", tags=["candidates"])
app.include_router(employers.router, prefix="/api/employers", tags=["employers"])
app.include_router(vacancies.router, prefix="/api/vacancies", tags=["vacancies"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["resumes"])
app.include_router(interviews.router, prefix="/api/interviews", tags=["interviews"])
app.include_router(hr.router, prefix="/api/hr", tags=["hr"])


@app.get("/")
async def root():
    return {"message": "SmartBot 2.0 API is running!"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}
