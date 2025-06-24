"""
Tests for EmbeddingService
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from app.services.embedding_service import EmbeddingService
from app.models.schemas import DocumentChunk, DocumentMetadata, EmbeddingStats


class TestEmbeddingService:
    """Test cases for EmbeddingService"""
    
    def teardown_method(self):
        """Reset singleton after each test"""
        EmbeddingService.reset_instance()
    
    @pytest.fixture
    def embedding_service(self, mock_settings, temp_dir):
        """Create EmbeddingService instance for testing"""
        with patch('app.services.embedding_service.settings', mock_settings):
            # Update paths to use temp directory
            mock_settings.VECTOR_STORE_DIR = os.path.join(temp_dir, "vector_store")
            mock_settings.HASH_FILE = os.path.join(temp_dir, "hashes.json")
            
            with patch('app.services.embedding_service.OpenAIEmbeddings'):
                with patch.object(EmbeddingService, '_load_vector_store'):
                    service = EmbeddingService()
                    return service
    
    def test_init(self, embedding_service, mock_settings, temp_dir):
        """Test EmbeddingService initialization"""
        assert embedding_service.store_dir == Path(os.path.join(temp_dir, "vector_store"))
        assert embedding_service.hash_file == Path(os.path.join(temp_dir, "hashes.json"))
        assert embedding_service.embeddings is not None
        assert embedding_service.vector_store is None  # Not loaded in test
    
    def test_sha256(self, embedding_service):
        """Test SHA256 hashing"""
        text = "test content"
        hash1 = embedding_service._sha256(text)
        hash2 = embedding_service._sha256(text)
        
        assert hash1 == hash2  # Same input, same hash
        assert len(hash1) == 64  # SHA256 produces 64-char hex string
        assert hash1 != embedding_service._sha256("different content")
    
    def test_load_previous_hashes_empty(self, embedding_service):
        """Test loading hashes when file doesn't exist"""
        hashes = embedding_service._load_previous_hashes()
        assert hashes == {}
    
    def test_load_previous_hashes_with_data(self, embedding_service, temp_dir):
        """Test loading hashes when file exists"""
        # Create hash file with test data
        hash_data = {"doc1.md": "hash1", "doc2.md": "hash2"}
        hash_file = Path(temp_dir) / "hashes.json"
        hash_file.write_text(json.dumps(hash_data))
        
        # Update service hash file path
        embedding_service.hash_file = hash_file
        
        hashes = embedding_service._load_previous_hashes()
        assert hashes == hash_data
    
    def test_save_hashes(self, embedding_service, temp_dir):
        """Test saving hashes"""
        hash_data = {"doc1.md": "hash1", "doc2.md": "hash2"}
        hash_file = Path(temp_dir) / "hashes.json"
        embedding_service.hash_file = hash_file
        
        embedding_service._save_hashes(hash_data)
        
        assert hash_file.exists()
        saved_data = json.loads(hash_file.read_text())
        assert saved_data == hash_data
    
    @patch('app.services.embedding_service.MarkdownLoader')
    def test_process_embeddings_no_documents(self, mock_loader_class, embedding_service):
        """Test processing embeddings when no documents found"""
        # Mock loader to return empty list
        mock_loader = Mock()
        mock_loader.load.return_value = []
        mock_loader_class.return_value = mock_loader
        
        result = embedding_service.process_embeddings()
        
        assert result["success"] is False
        assert "No documents found" in result["message"]
        assert "execution_time" in result
    
    @patch('app.services.embedding_service.MarkdownLoader')
    @patch('app.services.embedding_service.RecursiveCharacterTextSplitter')
    @patch('app.services.embedding_service.FAISS')
    def test_process_embeddings_new_documents(
        self, 
        mock_faiss_class,
        mock_splitter_class, 
        mock_loader_class,
        embedding_service,
        sample_documents,
        mock_faiss_store
    ):
        """Test processing new documents"""
        # Mock loader
        mock_loader = Mock()
        mock_loader.load.return_value = sample_documents
        mock_loader_class.return_value = mock_loader
        
        # Mock text splitter
        mock_splitter = Mock()
        mock_chunks = [
            Mock(page_content="chunk1", metadata={"key": "doc1.md"}),
            Mock(page_content="chunk2", metadata={"key": "doc2.md"})
        ]
        mock_splitter.split_documents.return_value = mock_chunks
        mock_splitter_class.return_value = mock_splitter
        
        # Mock FAISS
        mock_faiss_class.from_documents.return_value = mock_faiss_store
        
        result = embedding_service.process_embeddings()
        
        assert result["success"] is True
        assert "Successfully processed" in result["message"]
        assert "execution_time" in result
        
        # Verify FAISS was called
        mock_faiss_class.from_documents.assert_called_once()
        
        # Verify text splitter was used
        mock_splitter.split_documents.assert_called()
    
    @patch('app.services.embedding_service.MarkdownLoader')
    def test_process_embeddings_no_changes(self, mock_loader_class, embedding_service, sample_documents, temp_dir):
        """Test processing when no documents have changed"""
        # Setup existing hashes
        hash_data = {}
        for doc in sample_documents:
            hash_data[doc.metadata["key"]] = embedding_service._sha256(doc.page_content)
        
        hash_file = Path(temp_dir) / "hashes.json"
        hash_file.write_text(json.dumps(hash_data))
        embedding_service.hash_file = hash_file
        
        # Mock loader
        mock_loader = Mock()
        mock_loader.load.return_value = sample_documents
        mock_loader_class.return_value = mock_loader
        
        result = embedding_service.process_embeddings()
        
        assert result["success"] is True
        assert "No changes detected" in result["message"]
    
    def test_search_no_vector_store(self, embedding_service):
        """Test search when vector store is not available"""
        embedding_service.vector_store = None
        
        with pytest.raises(ValueError, match="Vector store not available"):
            embedding_service.search("test query")
    
    def test_search_with_results(self, embedding_service, mock_faiss_store):
        """Test successful search with results"""
        embedding_service.vector_store = mock_faiss_store
        
        results = embedding_service.search("test query", max_results=2, threshold=0.5)
        
        assert len(results) == 2
        assert all(isinstance(result, DocumentChunk) for result in results)
        assert all(result.score >= 0.5 for result in results)
        
        # Verify search was called on vector store
        mock_faiss_store.similarity_search_with_score.assert_called_once_with("test query", k=2)
    
    def test_search_with_threshold_filtering(self, embedding_service):
        """Test search with threshold filtering"""
        # Mock vector store with mixed scores
        mock_store = Mock()
        from langchain.schema import Document
        mock_results = [
            (Document(page_content="good match", metadata={"key": "doc1.md", "source": "s3://test/doc1.md"}), 0.1),  # High similarity
            (Document(page_content="poor match", metadata={"key": "doc2.md", "source": "s3://test/doc2.md"}), 0.9),  # Low similarity
        ]
        mock_store.similarity_search_with_score.return_value = mock_results
        embedding_service.vector_store = mock_store
        
        results = embedding_service.search("test query", threshold=0.5)
        
        # Only the good match should pass the threshold
        assert len(results) == 1
        assert results[0].score >= 0.5
    
    def test_get_stats_no_data(self, embedding_service):
        """Test getting stats when no data exists"""
        stats = embedding_service.get_stats()
        
        assert isinstance(stats, EmbeddingStats)
        assert stats.total_documents == 0
        assert stats.total_chunks == 0
        assert stats.last_update is None
        assert stats.vector_store_size is None
    
    def test_get_stats_with_data(self, embedding_service, temp_dir, mock_faiss_store):
        """Test getting stats with existing data"""
        # Create hash file
        hash_data = {"doc1.md": "hash1", "doc2.md": "hash2"}
        hash_file = Path(temp_dir) / "hashes.json"
        hash_file.write_text(json.dumps(hash_data))
        embedding_service.hash_file = hash_file
        
        # Create vector store directory with files
        store_dir = Path(temp_dir) / "vector_store"
        store_dir.mkdir()
        (store_dir / "index.faiss").write_bytes(b"fake faiss data")
        (store_dir / "index.pkl").write_bytes(b"fake pickle data")
        embedding_service.store_dir = store_dir
        
        # Set vector store
        embedding_service.vector_store = mock_faiss_store
        
        stats = embedding_service.get_stats()
        
        assert stats.total_documents == 2
        assert stats.total_chunks == 10  # From mock
        assert stats.last_update is not None
        assert stats.vector_store_size > 0
    
    @patch('app.services.embedding_service.MarkdownLoader')
    def test_process_embeddings_force_update(self, mock_loader_class, embedding_service, sample_documents):
        """Test force update functionality"""
        # Setup existing hashes (should be ignored with force_update=True)
        hash_data = {doc.metadata["key"]: "old_hash" for doc in sample_documents}
        
        with patch.object(embedding_service, '_load_previous_hashes', return_value=hash_data):
            with patch.object(embedding_service, '_save_hashes'):
                with patch('app.services.embedding_service.RecursiveCharacterTextSplitter'):
                    with patch('app.services.embedding_service.FAISS') as mock_faiss:
                        mock_loader = Mock()
                        mock_loader.load.return_value = sample_documents
                        mock_loader_class.return_value = mock_loader
                        
                        mock_faiss.from_documents.return_value = Mock()
                        
                        result = embedding_service.process_embeddings(force_update=True)
                        
                        assert result["success"] is True
                        # Should process all documents despite existing hashes
                        mock_faiss.from_documents.assert_called()
    
    def test_search_error_handling(self, embedding_service):
        """Test search error handling"""
        mock_store = Mock()
        mock_store.similarity_search_with_score.side_effect = Exception("Search failed")
        embedding_service.vector_store = mock_store
        
        with pytest.raises(ValueError, match="Search error"):
            embedding_service.search("test query")


class TestEmbeddingServiceIntegration:
    """Integration tests for EmbeddingService"""
    
    def teardown_method(self):
        """Reset singleton after each test"""
        EmbeddingService.reset_instance()
    
    @pytest.fixture
    def integration_service(self, temp_dir):
        """Create service for integration testing"""
        with patch('app.services.embedding_service.settings') as mock_settings:
            mock_settings.VECTOR_STORE_DIR = os.path.join(temp_dir, "vector_store")
            mock_settings.HASH_FILE = os.path.join(temp_dir, "hashes.json")
            mock_settings.EMBEDDING_MODEL = "text-embedding-ada-002"
            mock_settings.CHUNK_SIZE = 100  # Small for testing
            mock_settings.CHUNK_OVERLAP = 20
            mock_settings.S3_BUCKET_NAME = "test-bucket"
            
            with patch('app.services.embedding_service.OpenAIEmbeddings') as mock_embeddings_class:
                mock_embeddings = Mock()
                mock_embeddings.embed_documents.return_value = [[0.1] * 1536, [0.2] * 1536]
                mock_embeddings_class.return_value = mock_embeddings
                
                with patch.object(EmbeddingService, '_load_vector_store'):
                    return EmbeddingService()
    
    @patch('app.services.embedding_service.MarkdownLoader')
    @patch('app.services.embedding_service.FAISS')
    def test_full_process_and_search_workflow(
        self,
        mock_faiss_class,
        mock_loader_class, 
        integration_service,
        sample_documents,
        mock_faiss_store
    ):
        """Test complete workflow: process documents then search"""
        # Mock loader
        mock_loader = Mock()
        mock_loader.load.return_value = sample_documents
        mock_loader_class.return_value = mock_loader
        
        # Mock FAISS
        mock_faiss_class.from_documents.return_value = mock_faiss_store
        
        # Process embeddings
        result = integration_service.process_embeddings()
        assert result["success"] is True
        
        # Set the mock store (simulating successful creation)
        integration_service.vector_store = mock_faiss_store
        
        # Search
        search_results = integration_service.search("machine learning")
        assert len(search_results) > 0
        assert all(isinstance(r, DocumentChunk) for r in search_results)
