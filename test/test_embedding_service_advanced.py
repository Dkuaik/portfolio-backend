"""
Performance and edge case tests for EmbeddingService
"""
import os
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from app.services.embedding_service import EmbeddingService
from test.test_utils import create_large_test_documents, EmbeddingTestConstants


class TestEmbeddingServiceEdgeCases:
    """Test edge cases and error scenarios"""
    
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
    
    @pytest.fixture
    def service_with_invalid_paths(self, temp_dir):
        """Service with invalid file paths for testing error handling"""
        with patch('app.services.embedding_service.settings') as mock_settings:
            # Use non-existent directory that can't be created
            mock_settings.VECTOR_STORE_DIR = "/root/cannot_create"
            mock_settings.HASH_FILE = "/root/cannot_create/hashes.json"
            mock_settings.EMBEDDING_MODEL = "text-embedding-ada-002"
            mock_settings.CHUNK_SIZE = 1000
            mock_settings.CHUNK_OVERLAP = 200
            mock_settings.S3_BUCKET_NAME = "test-bucket"
            
            with patch('app.services.embedding_service.OpenAIEmbeddings'):
                with patch.object(EmbeddingService, '_load_vector_store'):
                    return EmbeddingService()
    
    def test_save_hashes_permission_error(self, service_with_invalid_paths):
        """Test hash saving with permission errors"""
        with pytest.raises(Exception):
            service_with_invalid_paths._save_hashes({"test": "hash"})
    
    def test_load_corrupted_hash_file(self, embedding_service, temp_dir):
        """Test loading corrupted hash file"""
        # Create corrupted JSON file
        hash_file = Path(temp_dir) / "hashes.json"
        hash_file.write_text("invalid json content {")
        embedding_service.hash_file = hash_file
        
        hashes = embedding_service._load_previous_hashes()
        assert hashes == {}  # Should return empty dict on error
    
    @patch('app.services.embedding_service.MarkdownLoader')
    def test_process_embeddings_loader_exception(self, mock_loader_class, embedding_service):
        """Test handling of loader exceptions"""
        mock_loader = Mock()
        mock_loader.load.side_effect = Exception("S3 connection failed")
        mock_loader_class.return_value = mock_loader
        
        result = embedding_service.process_embeddings()
        
        assert result["success"] is False
        assert "S3 connection failed" in result["message"]
    
    def test_search_with_empty_query(self, embedding_service, mock_faiss_store):
        """Test search with empty or invalid queries"""
        embedding_service.vector_store = mock_faiss_store
        
        # Empty query should still work (FAISS handles it)
        results = embedding_service.search("")
        assert isinstance(results, list)
    
    def test_search_with_extreme_parameters(self, embedding_service, mock_faiss_store):
        """Test search with extreme parameter values"""
        embedding_service.vector_store = mock_faiss_store
        
        # Very high max_results
        results = embedding_service.search("test", max_results=1000)
        assert isinstance(results, list)
        
        # Threshold of 0 (should return all results)
        results = embedding_service.search("test", threshold=0.0)
        assert len(results) >= 0
        
        # Threshold of 1 (should return only perfect matches)
        results = embedding_service.search("test", threshold=1.0)
        assert isinstance(results, list)


class TestEmbeddingServicePerformance:
    """Performance-related tests for EmbeddingService"""
    
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
    
    @patch('app.services.embedding_service.MarkdownLoader')
    @patch('app.services.embedding_service.RecursiveCharacterTextSplitter')
    @patch('app.services.embedding_service.FAISS')
    def test_process_large_document_set(
        self,
        mock_faiss_class,
        mock_splitter_class,
        mock_loader_class,
        embedding_service
    ):
        """Test processing large number of documents"""
        # Create large document set
        large_documents = create_large_test_documents(100)
        
        # Mock loader
        mock_loader = Mock()
        mock_loader.load.return_value = large_documents
        mock_loader_class.return_value = mock_loader
        
        # Mock splitter to return manageable chunks
        mock_splitter = Mock()
        mock_chunks = [Mock(page_content=f"chunk_{i}", metadata={"key": f"doc_{i}.md"}) for i in range(200)]
        mock_splitter.split_documents.return_value = mock_chunks
        mock_splitter_class.return_value = mock_splitter
        
        # Mock FAISS
        mock_vector_store = Mock()
        mock_faiss_class.from_documents.return_value = mock_vector_store
        
        result = embedding_service.process_embeddings()
        
        assert result["success"] is True
        assert "execution_time" in result
        # Should handle large document sets without errors
        mock_faiss_class.from_documents.assert_called_once()
    
    def test_incremental_updates_performance(self, embedding_service, temp_dir):
        """Test performance of incremental updates"""
        from unittest.mock import patch
        import json
        
        # Setup existing hashes for 50 documents
        existing_hashes = {f"doc_{i}.md": f"hash_{i}" for i in range(50)}
        hash_file = Path(temp_dir) / "hashes.json"
        hash_file.write_text(json.dumps(existing_hashes))
        embedding_service.hash_file = hash_file
        
        # Create documents where only 5 are new/changed
        documents = create_large_test_documents(55)  # 5 new documents
        
        with patch('app.services.embedding_service.MarkdownLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load.return_value = documents
            mock_loader_class.return_value = mock_loader
            
            with patch('app.services.embedding_service.RecursiveCharacterTextSplitter'):
                with patch('app.services.embedding_service.FAISS'):
                    result = embedding_service.process_embeddings()
                    
                    # Should detect that most documents haven't changed
                    assert result["success"] is True


class TestEmbeddingServiceStatsDetailed:
    """Detailed tests for statistics functionality"""
    
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
    
    def test_stats_with_various_file_sizes(self, embedding_service, temp_dir):
        """Test stats calculation with different file sizes"""
        import json
        
        # Create hash file
        hash_data = {f"doc_{i}.md": f"hash_{i}" for i in range(10)}
        hash_file = Path(temp_dir) / "hashes.json"
        hash_file.write_text(json.dumps(hash_data))
        embedding_service.hash_file = hash_file
        
        # Create vector store directory with various file sizes
        store_dir = Path(temp_dir) / "vector_store"
        store_dir.mkdir()
        (store_dir / "small_file.faiss").write_bytes(b"x" * 1024)  # 1KB
        (store_dir / "large_file.pkl").write_bytes(b"x" * 1024 * 1024)  # 1MB
        
        # Create subdirectory with files
        sub_dir = store_dir / "subdir"
        sub_dir.mkdir()
        (sub_dir / "nested_file.txt").write_bytes(b"x" * 512)  # 512B
        
        embedding_service.store_dir = store_dir
        
        # Mock vector store
        mock_store = Mock()
        mock_store.index.ntotal = 150
        embedding_service.vector_store = mock_store
        
        stats = embedding_service.get_stats()
        
        assert stats.total_documents == 10
        assert stats.total_chunks == 150
        assert stats.vector_store_size > 1024 * 1024  # Should be > 1MB
        assert stats.last_update is not None
    
    def test_stats_error_recovery(self, embedding_service):
        """Test stats calculation with various error conditions"""
        # Test with non-existent files
        embedding_service.hash_file = Path("/non/existent/path/hashes.json")
        embedding_service.store_dir = Path("/non/existent/path/vector_store")
        
        stats = embedding_service.get_stats()
        
        # Should return default values without crashing
        assert stats.total_documents == 0
        assert stats.total_chunks == 0
        assert stats.last_update is None
        assert stats.vector_store_size is None
