import os
import json
import hashlib
import time
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from app.services.markdown_processor import MarkdownLoader
from app.core.config import settings
from app.models.schemas import DocumentChunk, DocumentMetadata, EmbeddingStats

class EmbeddingService:
    """Service for managing embeddings and vector search (Singleton pattern)"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Only initialize once (singleton pattern)
        if not self._initialized:
            self.store_dir = Path(settings.VECTOR_STORE_DIR)
            self.hash_file = Path(settings.HASH_FILE)
            self.embeddings = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL)
            self.vector_store = None
            self._load_vector_store()
            self._initialized = True
    
    def _load_vector_store(self):
        """Load existing vector store if available"""
        try:
            if self.store_dir.exists():
                self.vector_store = FAISS.load_local(
                    self.store_dir.as_posix(), 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print(f"✅ Vector store loaded from {self.store_dir}")
            else:
                print("⚠️ No existing vector store found")
        except Exception as e:
            print(f"❌ Error loading vector store: {str(e)}")
            self.vector_store = None
    
    def _sha256(self, text: str) -> str:
        """Calculate SHA256 hash of text"""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    
    def _load_previous_hashes(self) -> dict:
        """Load previously processed document hashes"""
        if self.hash_file.exists():
            try:
                return json.loads(self.hash_file.read_text())
            except Exception as e:
                print(f"❌ Error loading hashes: {str(e)}")
        return {}
    
    def _save_hashes(self, hashes: dict):
        """Save document hashes"""
        try:
            self.hash_file.parent.mkdir(parents=True, exist_ok=True)
            self.hash_file.write_text(json.dumps(hashes, indent=2))
        except Exception as e:
            print(f"❌ Error saving hashes: {str(e)}")
            raise
    
    def process_embeddings(self, force_update: bool = False) -> dict:
        """Process documents and create/update embeddings"""
        start_time = time.time()
        
        try:
            # Load documents from S3
            loader = MarkdownLoader(bucket_name=settings.S3_BUCKET_NAME)
            documents = loader.load()
            
            if not documents:
                return {
                    "success": False,
                    "message": "No documents found to process",
                    "stats": self.get_stats(),
                    "execution_time": time.time() - start_time
                }
            
            # Load previous hashes
            prev_hashes = {} if force_update else self._load_previous_hashes()
            
            # Filter new/changed documents
            new_docs, kept_docs = [], []
            current_hashes = {}
            
            for doc in documents:
                key = doc.metadata["key"]
                content_hash = self._sha256(doc.page_content)
                current_hashes[key] = content_hash
                
                if prev_hashes.get(key) != content_hash:
                    new_docs.append(doc)
                else:
                    kept_docs.append(doc)
            
            print(f"→ {len(new_docs)} docs to process / {len(kept_docs)} unchanged")
            
            if not new_docs and not force_update:
                return {
                    "success": True,
                    "message": "No changes detected. Vector store is up to date.",
                    "stats": self.get_stats(),
                    "execution_time": time.time() - start_time
                }
            
            # Create text splitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            
            # Split documents into chunks
            chunks = text_splitter.split_documents(new_docs)
            print(f"📄 Created {len(chunks)} chunks from {len(new_docs)} documents")
            
            # Create or update vector store
            if self.vector_store is None or force_update:
                # Create new vector store
                all_chunks = text_splitter.split_documents(documents)
                self.vector_store = FAISS.from_documents(all_chunks, self.embeddings)
                print("🆕 Created new vector store")
            else:
                # Add new chunks to existing store
                if chunks:
                    new_vector_store = FAISS.from_documents(chunks, self.embeddings)
                    self.vector_store.merge_from(new_vector_store)
                    print(f"➕ Added {len(chunks)} new chunks to vector store")
            
            # Save vector store
            self.store_dir.mkdir(parents=True, exist_ok=True)
            self.vector_store.save_local(self.store_dir.as_posix())
            
            # Save updated hashes
            self._save_hashes(current_hashes)
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "message": f"Successfully processed {len(new_docs)} documents and created {len(chunks)} chunks",
                "stats": self.get_stats(),
                "execution_time": execution_time
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error processing embeddings: {str(e)}",
                "stats": self.get_stats(),
                "execution_time": time.time() - start_time
            }
    
    def search(self, query: str, max_results: int = 5, threshold: float = 0.7) -> List[DocumentChunk]:
        """Search for similar documents"""
        print(f"🔍 DEBUG: Starting search with query: '{query}', max_results: {max_results}, threshold: {threshold}")
        
        if not self.vector_store:
            print("❌ DEBUG: Vector store not available")
            raise ValueError("Vector store not available. Please process embeddings first.")
        
        print(f"✅ DEBUG: Vector store is available")
        
        try:
            # Perform similarity search with scores
            print("🔍 DEBUG: Performing similarity search...")
            results = self.vector_store.similarity_search_with_score(
                query, k=max_results
            )
            
            print(f"📊 DEBUG: Raw results count: {len(results)}")
            for i, (doc, score) in enumerate(results):
                print(f"  Result {i}: score={score}, content_preview='{doc.page_content[:100]}...'")
            
            # Filter by threshold and convert to DocumentChunk objects
            chunks = []
            for doc, score in results:
                # Convert score to similarity (FAISS returns distance, lower is better)
                # For L2 distance, we can use 1/(1+distance) or similar normalization
                similarity = 1 / (1 + score)  # This ensures similarity is between 0 and 1
                print(f"🔢 DEBUG: score={score}, similarity={similarity}, threshold={threshold}")
                
                if similarity >= threshold:
                    print(f"✅ DEBUG: Result passed threshold")
                    
                    # Convert datetime to string if needed
                    last_modified = doc.metadata.get("last_modified")
                    if last_modified and hasattr(last_modified, 'isoformat'):
                        last_modified = last_modified.isoformat()
                    
                    metadata = DocumentMetadata(
                        key=doc.metadata.get("key", "unknown"),
                        source=doc.metadata.get("source", "unknown"),
                        size=doc.metadata.get("size"),
                        last_modified=last_modified
                    )
                    
                    chunk = DocumentChunk(
                        content=doc.page_content,
                        metadata=metadata,
                        score=round(similarity, 4)
                    )
                    chunks.append(chunk)
                else:
                    pass  # Result filtered out by threshold
            
            return chunks
            
        except Exception as e:
            raise ValueError(f"Search error: {str(e)}")
    
    def get_stats(self) -> EmbeddingStats:
        """Get embedding statistics"""
        try:
            # Count documents from hashes
            hashes = self._load_previous_hashes()
            total_documents = len(hashes)
            
            # Estimate chunks (rough calculation)
            total_chunks = 0
            if self.vector_store:
                total_chunks = self.vector_store.index.ntotal if hasattr(self.vector_store.index, 'ntotal') else 0
            
            # Get last update time
            last_update = None
            if self.hash_file.exists():
                last_update = datetime.fromtimestamp(
                    self.hash_file.stat().st_mtime
                ).isoformat()
            
            # Get vector store size
            vector_store_size = None
            if self.store_dir.exists():
                try:
                    vector_store_size = sum(
                        f.stat().st_size for f in self.store_dir.rglob('*') if f.is_file()
                    )
                except:
                    pass
            
            return EmbeddingStats(
                total_documents=total_documents,
                total_chunks=total_chunks,
                last_update=last_update,
                vector_store_size=vector_store_size
            )
            
        except Exception as e:
            print(f"❌ Error getting stats: {str(e)}")
            return EmbeddingStats(
                total_documents=0,
                total_chunks=0,
                last_update=None,
                vector_store_size=None
            )
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (useful for testing)"""
        cls._instance = None
        cls._initialized = False
    
    def is_initialized(self):
        """Check if the service is initialized"""
        return self._initialized


if __name__ == "__main__":
    # Example usage
    service = EmbeddingService.get_instance()
    print(service.get_stats())
    
    # Process embeddings (force update for demo)
    result = service.process_embeddings(force_update=True)
    print(result)
    
    # Perform a search
    try:
        search_results = service.search("example query", max_results=3, threshold=0.5)
        for chunk in search_results:
            print(chunk)
    except ValueError as e:
        print(f"Search error: {str(e)}")