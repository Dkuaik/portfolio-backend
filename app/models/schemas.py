from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentMetadata(BaseModel):
    """Document metadata model"""
    key: str = Field(..., description="Document key/identifier")
    source: str = Field(..., description="Document source")
    size: Optional[int] = Field(None, description="Document size in bytes")
    last_modified: Optional[str] = Field(None, description="Last modified date")

class DocumentChunk(BaseModel):
    """Document chunk model"""
    content: str = Field(..., description="Chunk content")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    score: Optional[float] = Field(None, description="Similarity score")

class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., description="Search query", min_length=1, max_length=1000)
    max_results: Optional[int] = Field(5, description="Maximum number of results", ge=1, le=20)
    threshold: Optional[float] = Field(0.7, description="Similarity threshold", ge=0.0, le=1.0)

class SearchResponse(BaseModel):
    """Search response model"""
    query: str = Field(..., description="Original search query")
    results: List[DocumentChunk] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results found")
    execution_time: float = Field(..., description="Query execution time in seconds")

class EmbeddingStats(BaseModel):
    """Embedding statistics model"""
    total_documents: int = Field(..., description="Total number of documents processed")
    total_chunks: int = Field(..., description="Total number of chunks created")
    last_update: Optional[str] = Field(None, description="Last update timestamp")
    vector_store_size: Optional[int] = Field(None, description="Vector store size in bytes")

class ProcessEmbeddingsRequest(BaseModel):
    """Process embeddings request model"""
    force_update: Optional[bool] = Field(False, description="Force update all embeddings")

class ProcessEmbeddingsResponse(BaseModel):
    """Process embeddings response model"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Status message")
    stats: EmbeddingStats = Field(..., description="Embedding statistics")
    execution_time: float = Field(..., description="Processing time in seconds")

class HealthCheck(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")
    services: Dict[str, str] = Field(..., description="Service status details")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="Error timestamp")
