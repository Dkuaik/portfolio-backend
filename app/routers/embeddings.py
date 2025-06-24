import time
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List

from app.models.schemas import (
    SearchRequest, 
    SearchResponse, 
    ProcessEmbeddingsRequest,
    ProcessEmbeddingsResponse,
    EmbeddingStats,
    ErrorResponse
)
from app.services.embedding_service import EmbeddingService

router = APIRouter(prefix="/embeddings")

@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    Search for similar documents using semantic search
    """
    start_time = time.time()
    
    try:
        embedding_service = EmbeddingService.get_instance()
        # Perform search
        results = embedding_service.search(
            query=request.query,
            max_results=request.max_results,
            threshold=request.threshold
        )
        
        execution_time = time.time() - start_time
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            execution_time=round(execution_time, 4)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/process", response_model=ProcessEmbeddingsResponse)
async def process_embeddings(
    request: ProcessEmbeddingsRequest,
    background_tasks: BackgroundTasks
):
    """
    Process documents and create/update embeddings
    """
    try:
        result = embedding_service.process_embeddings(
            force_update=request.force_update
        )
        
        return ProcessEmbeddingsResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process embeddings: {str(e)}"
        )

@router.get("/stats", response_model=EmbeddingStats)
async def get_embedding_stats():
    """
    Get current embedding statistics
    """
    try:
        return embedding_service.get_stats()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )

@router.post("/rebuild")
async def rebuild_embeddings(background_tasks: BackgroundTasks):
    """
    Rebuild all embeddings from scratch (background task)
    """
    def rebuild_task():
        try:
            embedding_service.process_embeddings(force_update=True)
            print("✅ Embeddings rebuilt successfully")
        except Exception as e:
            print(f"❌ Failed to rebuild embeddings: {str(e)}")
    
    background_tasks.add_task(rebuild_task)
    
    return {
        "message": "Rebuild task started in background",
        "status": "processing"
    }
