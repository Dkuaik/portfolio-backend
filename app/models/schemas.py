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
    max_results: int = Field(5, description="Maximum number of results", ge=1, le=20)
    threshold: float = Field(0.7, description="Similarity threshold", ge=0.0, le=1.0)

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
    force_update: bool = Field(False, description="Force update all embeddings")

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

class ChatRequest(BaseModel):
    """Chat request with embeddings context"""
    query: str = Field(..., description="User query/question", min_length=1, max_length=2000)
    context_query: Optional[str] = Field(None, description="Specific query for context search (if different from main query)")
    max_context_results: int = Field(3, description="Maximum context chunks to include", ge=1, le=10)
    similarity_threshold: float = Field(0.3, description="Similarity threshold for context", ge=0.0, le=1.0)
    model: str = Field("google/gemini-2.5-flash-lite-preview-06-17", description="Model to use for chat")
    temperature: float = Field(0.7, description="Response randomness", ge=0.0, le=2.0)
    max_tokens: int = Field(1000, description="Maximum tokens in response", ge=100, le=4000)

class ContextChunk(BaseModel):
    """Context chunk model"""
    source: str = Field(..., description="Source document")
    content_preview: str = Field(..., description="Preview of the content chunk")
    score: float = Field(..., description="Similarity score")

class ContextSource(BaseModel):
    """Context source information"""
    source: str = Field(..., description="Source document key for context")
    key: str = Field(..., description="Document key")
    score: float = Field(..., description="Similarity score")

class ChatResponse(BaseModel):
    """Chat response with context information"""
    query: str = Field(..., description="Original user query")
    response: str = Field(..., description="AI response")
    context_used: Dict[str, Any] = Field(..., description="Information about context used")
    execution_time: float = Field(..., description="Total execution time")
    success: bool = Field(..., description="Whether the request was successful")
    error: Optional[str] = Field(None, description="Error message if any")

class ChatContextResponse(BaseModel):
    """Chat context response model"""
    query: str = Field(..., description="Original user query")
    context_chunks: List[ContextChunk] = Field(..., description="List of context chunks")
    context_sources: List[ContextSource] = Field(..., description="Source details for each chunk")
    total_chunks: int = Field(..., description="Total number of context chunks")
    execution_time: float = Field(..., description="Time taken to retrieve context")
    success: bool = Field(..., description="Whether context retrieval was successful")
    error: Optional[str] = Field(None, description="Error message if any")

class OpenRouterClient(BaseModel):
    """OpenRouter client configuration"""
    model: str = Field("google/gemini-2.5-flash-lite-preview-06-17", description="Model to use for chat")
    temperature: float = Field(0.7, description="Temperature for response generation", ge=0.0, le=2.0)
    max_tokens: int = Field(1000, description="Maximum tokens in response", ge=100, le=4000)
    
    class Config:
        """Pydantic configuration"""
        extra = "forbid"  # Disallow extra fields