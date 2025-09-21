"""
Unit tests for API endpoints in the FastAPI application.

Tests cover:
- Document upload endpoints
- RAG chat endpoints
- Document management endpoints
- Error handling and validation
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import UploadFile
import io

# Import the FastAPI app
from api.app import app
from aimakerspace.models import ProcessedDocument, Document, DocumentType, Chunk, ProcessingStatus


class TestAPIEndpoints:
    """Test the FastAPI endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.test_api_key = "test-api-key-12345"
    
    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = self.client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    @patch('api.app.get_rag_service')
    def test_upload_document_success(self, mock_get_rag_service):
        """Test successful document upload."""
        # Mock RAG service
        mock_rag = Mock()
        # Create a mock document first
        mock_document = Document(
            content="Test document content",
            metadata={},
            source_path=Path("test.txt"),
            document_type=DocumentType.TEXT,
            document_id="test-doc"
        )
        
        # Create mock chunks
        mock_chunks = [
            Chunk(content=f"Chunk {i}", chunk_index=i, source_document_id="test-doc")
            for i in range(5)
        ]
        
        mock_processed_doc = ProcessedDocument(
            original_document=mock_document,
            chunks=mock_chunks,
            processing_metadata={},
            status=ProcessingStatus.COMPLETED
        )
        mock_rag.process_document = AsyncMock(return_value=mock_processed_doc)
        mock_get_rag_service.return_value = mock_rag
        
        # Create test file
        test_content = "This is test document content."
        test_file = io.BytesIO(test_content.encode())
        
        response = self.client.post(
            "/api/upload-document",
            files={"file": ("test.txt", test_file, "text/plain")},
            data={"api_key": self.test_api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["filename"] == "test.txt"
        assert data["chunks_processed"] == 5
    
    @patch('api.app.get_rag_service')
    def test_upload_document_invalid_file_type(self, mock_get_rag_service):
        """Test upload with invalid file type."""
        # Mock RAG service to raise error
        mock_rag = Mock()
        mock_rag.process_document = AsyncMock(side_effect=Exception("Unsupported file type"))
        mock_get_rag_service.return_value = mock_rag
        
        # Create test file with unsupported extension
        test_file = io.BytesIO(b"invalid content")
        
        response = self.client.post(
            "/api/upload-document",
            files={"file": ("test.xyz", test_file, "application/octet-stream")},
            data={"api_key": self.test_api_key}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert "Unsupported file type" in data["message"]
    
    def test_upload_document_missing_api_key(self):
        """Test upload without API key."""
        test_file = io.BytesIO(b"test content")
        
        response = self.client.post(
            "/api/upload-document",
            files={"file": ("test.txt", test_file, "text/plain")}
            # Missing api_key in data
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch('api.app.get_rag_service')
    def test_process_youtube_success(self, mock_get_rag_service):
        """Test successful YouTube video processing."""
        # Mock RAG service
        mock_rag = Mock()
        # Create a mock YouTube document
        mock_document = Document(
            content="YouTube video transcript content",
            metadata={"video_title": "Test Video", "channel": "Test Channel"},
            source_path=None,
            document_type=DocumentType.YOUTUBE,
            document_id="youtube-test"
        )
        
        # Create mock chunks
        mock_chunks = [
            Chunk(content=f"Transcript chunk {i}", chunk_index=i, source_document_id="youtube-test")
            for i in range(8)
        ]
        
        mock_processed_doc = ProcessedDocument(
            original_document=mock_document,
            chunks=mock_chunks,
            processing_metadata={"video_title": "Test Video", "channel": "Test Channel"},
            status=ProcessingStatus.COMPLETED
        )
        mock_rag.process_document = AsyncMock(return_value=mock_processed_doc)
        mock_get_rag_service.return_value = mock_rag
        
        response = self.client.post(
            "/api/process-youtube",
            json={
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "api_key": self.test_api_key
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["video_title"] == "Test Video"
        assert data["chunks_processed"] == 8
    
    @patch('api.app.get_rag_service')
    def test_process_youtube_invalid_url(self, mock_get_rag_service):
        """Test YouTube processing with invalid URL."""
        # Mock RAG service to raise error
        mock_rag = Mock()
        mock_rag.process_document = AsyncMock(side_effect=Exception("Invalid YouTube URL"))
        mock_get_rag_service.return_value = mock_rag
        
        response = self.client.post(
            "/api/process-youtube",
            json={
                "youtube_url": "https://vimeo.com/123456",
                "api_key": self.test_api_key
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert "Invalid YouTube URL" in data["message"]
    
    @patch('api.app.get_rag_service')
    def test_rag_chat_with_context(self, mock_get_rag_service):
        """Test RAG chat with document context."""
        # Mock RAG service
        mock_rag = Mock()
        mock_rag.chat_with_context = AsyncMock(return_value="AI response with context from documents")
        mock_rag.processed_documents = {"doc1": Mock()}  # Mock non-empty processed documents
        mock_get_rag_service.return_value = mock_rag
        
        response = self.client.post(
            "/api/rag-chat",
            json={
                "user_message": "What is machine learning?",
                "model": "gpt-4o-mini",
                "api_key": self.test_api_key,
                "use_context": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "AI response with context from documents"
        assert data["used_context"] is True
    
    @patch('api.app.get_rag_service')
    @patch('api.app.OpenAI')
    def test_rag_chat_without_context(self, mock_openai, mock_get_rag_service):
        """Test RAG chat without document context."""
        # Mock RAG service
        mock_rag = Mock()
        mock_rag.processed_documents = {}  # Empty processed documents
        mock_get_rag_service.return_value = mock_rag
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "AI response without context"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        response = self.client.post(
            "/api/rag-chat",
            json={
                "user_message": "Hello, how are you?",
                "model": "gpt-4o-mini",
                "api_key": self.test_api_key,
                "use_context": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "AI response without context"
        assert data["used_context"] is False
    
    @patch('api.app.get_rag_service')
    def test_list_documents(self, mock_get_rag_service):
        """Test listing processed documents."""
        # Mock RAG service
        mock_rag = Mock()
        mock_documents = [
            {
                "document_id": "doc1",
                "filename": "test1.pdf",
                "document_type": "pdf",
                "chunk_count": 10,
                "word_count": 500,
                "processing_metadata": {"title": "Test Document 1"},
                "status": "completed"
            },
            {
                "document_id": "doc2",
                "filename": "test2.txt",
                "document_type": "text",
                "chunk_count": 5,
                "word_count": 200,
                "processing_metadata": {},
                "status": "completed"
            }
        ]
        mock_rag.list_documents.return_value = mock_documents
        mock_get_rag_service.return_value = mock_rag
        
        response = self.client.get(f"/api/documents?api_key={self.test_api_key}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 2
        assert data["documents"][0]["document_id"] == "doc1"
        assert data["documents"][1]["document_id"] == "doc2"
    
    @patch('api.app.get_rag_service')
    def test_remove_document(self, mock_get_rag_service):
        """Test removing a document."""
        # Mock RAG service
        mock_rag = Mock()
        mock_rag.remove_document = Mock(return_value=True)
        mock_get_rag_service.return_value = mock_rag
        
        response = self.client.delete(f"/api/documents/test-doc?api_key={self.test_api_key}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Document 'test-doc' removed successfully"
    
    @patch('api.app.get_rag_service')
    def test_remove_nonexistent_document(self, mock_get_rag_service):
        """Test removing a document that doesn't exist."""
        # Mock RAG service
        mock_rag = Mock()
        mock_rag.remove_document = Mock(return_value=False)
        mock_get_rag_service.return_value = mock_rag
        
        response = self.client.delete(f"/api/documents/nonexistent?api_key={self.test_api_key}")
        
        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "error"
        assert "not found" in data["message"]
    
    @patch('api.app.get_rag_service')
    def test_rag_stats(self, mock_get_rag_service):
        """Test getting RAG service statistics."""
        # Mock RAG service
        mock_rag = Mock()
        mock_stats = {
            "documents_processed": 5,
            "chunks_created": 50,
            "embeddings_generated": 50,
            "queries_processed": 20,
            "active_documents": 5,
            "vector_db_size": 50,
            "last_activity": "2024-01-15T10:30:00"
        }
        mock_rag.get_stats.return_value = mock_stats
        mock_get_rag_service.return_value = mock_rag
        
        response = self.client.get(f"/api/rag-stats?api_key={self.test_api_key}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["stats"]["documents_processed"] == 5
        assert data["stats"]["chunks_created"] == 50
        assert data["stats"]["active_documents"] == 5
    
    def test_missing_api_key_endpoints(self):
        """Test endpoints that require API key without providing one."""
        endpoints_to_test = [
            ("GET", "/api/documents"),
            ("DELETE", "/api/documents/test-doc"),
            ("GET", "/api/rag-stats"),
        ]
        
        for method, endpoint in endpoints_to_test:
            if method == "GET":
                response = self.client.get(endpoint)
            elif method == "DELETE":
                response = self.client.delete(endpoint)
            
            assert response.status_code == 422  # Validation error for missing query parameter
    
    @patch('api.app.get_rag_service')
    def test_api_error_handling(self, mock_get_rag_service):
        """Test API error handling for internal errors."""
        # Mock RAG service to raise unexpected error
        mock_rag = Mock()
        mock_rag.list_documents.side_effect = Exception("Internal server error")
        mock_get_rag_service.return_value = mock_rag
        
        response = self.client.get(f"/api/documents?api_key={self.test_api_key}")
        
        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "error"
        assert "Internal server error" in data["message"]


class TestRAGServiceIntegration:
    """Integration tests for RAG service with API."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.test_api_key = "test-api-key-12345"
    
    @patch('api.app.RAGService')
    def test_rag_service_initialization(self, mock_rag_service_class):
        """Test that RAG service is properly initialized."""
        mock_rag_instance = Mock()
        mock_rag_service_class.return_value = mock_rag_instance
        
        # Import the function that creates RAG service
        from api.app import get_rag_service
        
        rag_service = get_rag_service(self.test_api_key)
        
        # Verify RAG service was created with correct API key
        mock_rag_service_class.assert_called_once()
        call_args = mock_rag_service_class.call_args
        assert call_args[1]["api_key"] == self.test_api_key
    
    @patch('api.app.get_rag_service')
    def test_end_to_end_document_processing(self, mock_get_rag_service):
        """Test end-to-end document processing workflow."""
        # Mock RAG service for upload
        mock_rag = Mock()
        # Create a mock document for end-to-end test
        mock_document = Document(
            content="This is test content for end-to-end testing.",
            metadata={},
            source_path=Path("test.txt"),
            document_type=DocumentType.TEXT,
            document_id="e2e-test"
        )
        
        # Create mock chunks
        mock_chunks = [
            Chunk(content=f"E2E chunk {i}", chunk_index=i, source_document_id="e2e-test")
            for i in range(3)
        ]
        
        mock_processed_doc = ProcessedDocument(
            original_document=mock_document,
            chunks=mock_chunks,
            processing_metadata={},
            status=ProcessingStatus.COMPLETED
        )
        mock_rag.process_document = AsyncMock(return_value=mock_processed_doc)
        
        # Mock for listing documents
        mock_rag.list_documents.return_value = [
            {
                "document_id": "e2e-test",
                "filename": "test.txt",
                "document_type": "text",
                "chunk_count": 3,
                "word_count": 50,
                "processing_metadata": {},
                "status": "completed"
            }
        ]
        
        # Mock for chat
        mock_rag.chat_with_context = AsyncMock(return_value="Response based on uploaded document")
        mock_rag.processed_documents = {"e2e-test": mock_processed_doc}  # Mock processed documents for chat
        
        # Mock for removal
        mock_rag.remove_document = Mock(return_value=True)
        
        mock_get_rag_service.return_value = mock_rag
        
        # Step 1: Upload document
        test_file = io.BytesIO(b"This is test content for end-to-end testing.")
        
        upload_response = self.client.post(
            "/api/upload-document",
            files={"file": ("test.txt", test_file, "text/plain")},
            data={"api_key": self.test_api_key}
        )
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data["status"] == "success"
        
        # Step 2: List documents
        list_response = self.client.get(f"/api/documents?api_key={self.test_api_key}")
        
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert len(list_data["documents"]) == 1
        assert list_data["documents"][0]["document_id"] == "e2e-test"
        
        # Step 3: Chat with context
        chat_response = self.client.post(
            "/api/rag-chat",
            json={
                "user_message": "What is this document about?",
                "model": "gpt-4o-mini",
                "api_key": self.test_api_key,
                "use_context": True
            }
        )
        
        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        assert chat_data["response"] == "Response based on uploaded document"
        
        # Step 4: Remove document
        remove_response = self.client.delete(f"/api/documents/e2e-test?api_key={self.test_api_key}")
        
        assert remove_response.status_code == 200
        remove_data = remove_response.json()
        assert remove_data["status"] == "success"


if __name__ == "__main__":
    pytest.main([__file__])
