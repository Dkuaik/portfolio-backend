"""
Test for EmbeddingService Singleton Pattern
"""
import pytest
from unittest.mock import patch

from app.services.embedding_service import EmbeddingService


class TestEmbeddingServiceSingleton:
    """Test singleton behavior of EmbeddingService"""
    
    def teardown_method(self):
        """Reset singleton after each test"""
        EmbeddingService.reset_instance()
    
    @patch('app.services.embedding_service.settings')
    @patch('app.services.embedding_service.OpenAIEmbeddings')
    def test_singleton_same_instance(self, mock_embeddings, mock_settings):
        """Test that multiple instantiations return the same instance"""
        mock_settings.VECTOR_STORE_DIR = "/tmp/test"
        mock_settings.HASH_FILE = "/tmp/test.json"
        mock_settings.EMBEDDING_MODEL = "test-model"
        
        with patch.object(EmbeddingService, '_load_vector_store'):
            # Create two instances
            service1 = EmbeddingService()
            service2 = EmbeddingService()
            
            # Should be the same instance
            assert service1 is service2
            assert id(service1) == id(service2)
    
    @patch('app.services.embedding_service.settings')
    @patch('app.services.embedding_service.OpenAIEmbeddings')
    def test_singleton_get_instance(self, mock_embeddings, mock_settings):
        """Test get_instance class method"""
        mock_settings.VECTOR_STORE_DIR = "/tmp/test"
        mock_settings.HASH_FILE = "/tmp/test.json"
        mock_settings.EMBEDDING_MODEL = "test-model"
        
        with patch.object(EmbeddingService, '_load_vector_store'):
            # Get instance using class method
            service1 = EmbeddingService.get_instance()
            service2 = EmbeddingService.get_instance()
            
            # Should be the same instance
            assert service1 is service2
            
            # Should be same as direct instantiation
            service3 = EmbeddingService()
            assert service1 is service3
    
    @patch('app.services.embedding_service.settings')
    @patch('app.services.embedding_service.OpenAIEmbeddings')
    def test_singleton_initialization_once(self, mock_embeddings, mock_settings):
        """Test that initialization happens only once"""
        mock_settings.VECTOR_STORE_DIR = "/tmp/test"
        mock_settings.HASH_FILE = "/tmp/test.json"
        mock_settings.EMBEDDING_MODEL = "test-model"
        
        with patch.object(EmbeddingService, '_load_vector_store') as mock_load:
            # Create multiple instances
            service1 = EmbeddingService()
            service2 = EmbeddingService()
            service3 = EmbeddingService.get_instance()
            
            # _load_vector_store should be called only once
            assert mock_load.call_count == 1
            
            # All should be initialized
            assert service1.is_initialized()
            assert service2.is_initialized()
            assert service3.is_initialized()
    
    @patch('app.services.embedding_service.settings')
    @patch('app.services.embedding_service.OpenAIEmbeddings')
    def test_singleton_reset_instance(self, mock_embeddings, mock_settings):
        """Test reset_instance functionality"""
        mock_settings.VECTOR_STORE_DIR = "/tmp/test"
        mock_settings.HASH_FILE = "/tmp/test.json"
        mock_settings.EMBEDDING_MODEL = "test-model"
        
        with patch.object(EmbeddingService, '_load_vector_store'):
            # Create instance
            service1 = EmbeddingService()
            first_id = id(service1)
            
            # Reset
            EmbeddingService.reset_instance()
            
            # Create new instance
            service2 = EmbeddingService()
            second_id = id(service2)
            
            # Should be different instances
            assert first_id != second_id
            assert service1 is not service2
    
    @patch('app.services.embedding_service.settings')
    @patch('app.services.embedding_service.OpenAIEmbeddings')
    def test_singleton_attributes_shared(self, mock_embeddings, mock_settings):
        """Test that attributes are shared between instances"""
        mock_settings.VECTOR_STORE_DIR = "/tmp/test"
        mock_settings.HASH_FILE = "/tmp/test.json" 
        mock_settings.EMBEDDING_MODEL = "test-model"
        
        with patch.object(EmbeddingService, '_load_vector_store'):
            service1 = EmbeddingService()
            service2 = EmbeddingService()
            
            # Modify attribute in one instance
            service1.custom_attribute = "test_value"
            
            # Should be available in the other instance
            assert hasattr(service2, 'custom_attribute')
            assert service2.custom_attribute == "test_value"
    
    def test_singleton_thread_safety_basic(self):
        """Basic test for thread safety (not comprehensive)"""
        import threading
        
        instances = []
        
        def create_instance():
            with patch('app.services.embedding_service.settings') as mock_settings:
                mock_settings.VECTOR_STORE_DIR = "/tmp/test"
                mock_settings.HASH_FILE = "/tmp/test.json"
                mock_settings.EMBEDDING_MODEL = "test-model"
                
                with patch('app.services.embedding_service.OpenAIEmbeddings'):
                    with patch.object(EmbeddingService, '_load_vector_store'):
                        instance = EmbeddingService()
                        instances.append(instance)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_instance)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All instances should be the same
        first_instance = instances[0]
        for instance in instances[1:]:
            assert instance is first_instance
