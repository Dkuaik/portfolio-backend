"""
Conftest for pytest fixtures
"""
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import pytest
from typing import List

from langchain.schema import Document

# Mock settings for testing
@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    from unittest.mock import Mock
    settings = Mock()
    settings.VECTOR_STORE_DIR = "/tmp/test_vector_store"
    settings.HASH_FILE = "/tmp/test_hashes.json"
    settings.EMBEDDING_MODEL = "text-embedding-ada-002"
    settings.CHUNK_SIZE = 1000
    settings.CHUNK_OVERLAP = 200
    settings.S3_BUCKET_NAME = "test-bucket"
    return settings

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_documents():
    """Sample documents for testing"""
    return [
        Document(
            page_content="This is a test document about machine learning and AI.",
            metadata={
                "key": "doc1.md",
                "source": "s3://test-bucket/doc1.md",
                "size": 100,
                "last_modified": "2024-01-01T00:00:00Z"
            }
        ),
        Document(
            page_content="This is another document about data science and analytics.",
            metadata={
                "key": "doc2.md", 
                "source": "s3://test-bucket/doc2.md",
                "size": 120,
                "last_modified": "2024-01-02T00:00:00Z"
            }
        ),
        Document(
            page_content="Python programming tutorial for beginners.",
            metadata={
                "key": "doc3.md",
                "source": "s3://test-bucket/doc3.md", 
                "size": 80,
                "last_modified": "2024-01-03T00:00:00Z"
            }
        )
    ]

@pytest.fixture
def mock_openai_embeddings():
    """Mock OpenAI embeddings"""
    mock_embeddings = Mock()
    # Mock embedding vectors (simple example)
    mock_embeddings.embed_documents.return_value = [
        [0.1, 0.2, 0.3, 0.4] * 384,  # 1536 dimensions
        [0.2, 0.3, 0.4, 0.5] * 384,
        [0.3, 0.4, 0.5, 0.6] * 384
    ]
    mock_embeddings.embed_query.return_value = [0.15, 0.25, 0.35, 0.45] * 384
    return mock_embeddings

@pytest.fixture
def mock_markdown_loader():
    """Mock markdown loader"""
    mock_loader = Mock()
    return mock_loader

@pytest.fixture
def mock_faiss_store():
    """Mock FAISS vector store"""
    mock_store = Mock()
    mock_store.index.ntotal = 10
    
    # Mock search results
    from langchain.schema import Document
    mock_results = [
        (Document(
            page_content="Test content about machine learning",
            metadata={"key": "doc1.md", "source": "s3://test-bucket/doc1.md"}
        ), 0.2),
        (Document(
            page_content="Test content about data science", 
            metadata={"key": "doc2.md", "source": "s3://test-bucket/doc2.md"}
        ), 0.3)
    ]
    mock_store.similarity_search_with_score.return_value = mock_results
    
    return mock_store
