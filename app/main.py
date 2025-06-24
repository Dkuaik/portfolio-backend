from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import embeddings, health
from app.core.config import settings

# Create FastAPI instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Portfolio Backend API - Sistema de embeddings y búsqueda semántica",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(embeddings.router, prefix="/api/v1", tags=["Embeddings"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Portfolio Backend API",
        "version": settings.VERSION,
        "docs": "/docs"
    }
