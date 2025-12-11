"""
Lender Matching Platform - FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, Base
from app.api import applications_router, lenders_router

settings = get_settings()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="""
    Loan underwriting and lender matching platform.
    
    Evaluates business loan applications against multiple lenders' credit policies
    and identifies the best matching lenders with detailed reasoning.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://imshambles.github.io",  # GitHub Pages
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(applications_router)
app.include_router(lenders_router)


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "name": settings.app_name,
        "status": "healthy",
        "version": "1.0.0",
    }


@app.get("/api/health")
def health_check():
    """API health check"""
    return {"status": "ok"}
