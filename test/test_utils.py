"""
Test utilities for embedding service tests
"""
from typing import List
from langchain.schema import Document


def create_test_document(content: str, key: str, size: int = 100) -> Document:
    """Create a test document with standard metadata"""
    return Document(
        page_content=content,
        metadata={
            "key": key,
            "source": f"s3://test-bucket/{key}",
            "size": size,
            "last_modified": "2024-01-01T00:00:00Z"
        }
    )


def create_large_test_documents(count: int = 5) -> List[Document]:
    """Create multiple test documents for performance testing"""
    documents = []
    for i in range(count):
        content = f"This is test document number {i+1}. " * 20  # Make it longer
        doc = create_test_document(
            content=content,
            key=f"doc_{i+1}.md",
            size=len(content)
        )
        documents.append(doc)
    return documents


def mock_embedding_response(dimensions: int = 1536) -> List[float]:
    """Create a mock embedding vector"""
    return [0.1 * (i % 10) for i in range(dimensions)]


class EmbeddingTestConstants:
    """Constants for embedding tests"""
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200
    DEFAULT_EMBEDDING_DIMENSIONS = 1536
    TEST_BUCKET_NAME = "test-bucket"
    TEST_SIMILARITY_THRESHOLD = 0.7
