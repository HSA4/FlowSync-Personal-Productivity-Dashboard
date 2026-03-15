"""Health Check Endpoint"""
from fastapi import APIRouter
from datetime import datetime

from app.models.common import HealthResponse
from app.db.database import db
from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    db_status = "connected" if db.health_check() else "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        version=settings.APP_VERSION,
        database=db_status,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }
