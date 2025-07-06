import time
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List

from app.models.schemas import (
    SearchRequest,
    SearchResponse,
    ProcessEmbeddingsRequest,
    ProcessEmbeddingsResponse,
    ChatRequest,
    ChatResponse,
    ChatContextResponse,
    EmbeddingStats,
    ErrorResponse
)
from app.services.embedding_service import EmbeddingService
from app.services.open_router_client import OpenRouterAPI

router = APIRouter(prefix="/embeddings")

# Initialize services
embedding_service = EmbeddingService.get_instance()

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

@router.post("/chat-context", response_model=ChatContextResponse)
async def get_chat_context(request: SearchRequest):
    """
    Get context for a chat query without calling OpenRouter (for testing)
    """
    start_time = time.time()
    
    try:
        # Get context using embeddings
        context_chunks = embedding_service.search(
            query=request.query,
            max_results=request.max_results or 5,
            threshold=request.threshold or 0.7
        )
        
        # Format context for display
        context_texts = []
        context_sources = []
        
        for chunk in context_chunks:
            context_texts.append({
                "source": chunk.metadata.source,
                "content_preview": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                "score": chunk.score
            })
            context_sources.append({
                "source": chunk.metadata.source,
                "key": chunk.metadata.key,
                "score": chunk.score
            })
        
        execution_time = time.time() - start_time
        
        return ChatContextResponse(
            query=request.query,
            context_chunks=context_texts,
            context_sources=context_sources,
            total_chunks=len(context_chunks),
            execution_time=round(execution_time, 4),
            success=True,
            error=None
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        return ChatContextResponse(
            query=request.query,
            context_chunks=[],
            context_sources=[],
            total_chunks=0,
            execution_time=round(execution_time, 4),
            success=False,
            error=str(e)
        )

@router.post("/chat", response_model=ChatResponse)
async def chat_with_context(request: ChatRequest):
    """
    Chat with AI using embeddings for context
    """
    start_time = time.time()
    
    try:
        # Unwrap optional fields with defaults
        model = request.model or "google/gemini-2.5-flash-lite-preview-06-17"
        temperature = request.temperature or 0.7
        max_tokens = request.max_tokens or 1000
        
        # Initialize OpenRouter client
        client = OpenRouterAPI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Prepare context parameters
        max_ctx = request.max_context_results or 3
        thresh = request.similarity_threshold or 0.3
        result = client.send_request_with_embeddings(
            user_query=request.query,
            embedding_service=embedding_service,
            max_context_results=max_ctx,
            similarity_threshold=thresh,
            system_prompt=None
        )
        
        execution_time = time.time() - start_time
        
        if result["success"]:
            # Extract the AI response
            ai_response = result["response"]["choices"][0]["message"]["content"]
            
            return ChatResponse(
                query=request.query,
                response=ai_response,
                context_used=result["context_used"],
                execution_time=round(execution_time, 4),
                success=True,
                error=None
            )
        else:
            return ChatResponse(
                query=request.query,
                response="",
                context_used=result["context_used"],
                execution_time=round(execution_time, 4),
                success=False,
                error=result["error"]
            )
        
    except Exception as e:
        execution_time = time.time() - start_time
        return ChatResponse(
            query=request.query,
            response="",
            context_used={"chunks_found": 0, "sources": [], "query": request.query, "threshold": request.similarity_threshold},
            execution_time=round(execution_time, 4),
            success=False,
            error=str(e)
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
