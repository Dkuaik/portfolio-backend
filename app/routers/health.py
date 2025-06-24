from fastapi import APIRouter
from datetime import datetime
from app.models.schemas import HealthCheck
from app.core.config import settings

router = APIRouter(prefix="/health")

@router.get("", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now(),
        version=settings.VERSION,
        services={
            "api": "healthy",
            "embeddings": "healthy",
            "vector_store": "healthy"
        }
    )
