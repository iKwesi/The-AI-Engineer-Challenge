"""
Test cases for the batch upload functionality (Section 4.6).
"""

import pytest
import tempfile
import os
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys

# Add the parent directory to the path to import the API
sys.path.append(str(Path(__file__).parent.parent))

from api.app import app

client = TestClient(app)

# Mock API key for testing
TEST_API_KEY = "test-api-key-12345"

@pytest.fixture
def mock_rag_service():
    """Mock RAG service for testing."""
    with patch('api.app.get_rag_service') as mock_get_rag:
        mock_rag = MagicMock()
        mock_rag.processed_documents = {'doc1': MagicMock(), 'doc2': MagicMock()}
        
        # Mock the process_document method to return a proper mock (async compatible)
        mock_processed_doc = MagicMock()
        mock_processed_doc.chunks = [MagicMock() for _ in range(5)]
        
        # Create an async mock for process_document
        async def mock_process_document(*args, **kwargs):
            return mock_processed_doc
        
        mock_rag.process_document = mock_process_document
        
        # Mock document mode methods
        mock_session = MagicMock()
        mock_session.mode.value = 'document'
        mock_session.session_id = 'test-session-123'
        mock_session.documents = []
        mock_rag.enter_document_mode.return_value = mock_session
        mock_rag.update_document_chunks_in_session.return_value = None
        
        mock_get_rag.return_value = mock_rag
        yield mock_rag

def create_test_file(content: str, filename: str) -> tuple:
    """Create a temporary test file and return file data for upload."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=Path(filename).suffix)
    temp_file.write(content)
    temp_file.close()
    
    with open(temp_file.name, 'rb') as f:
        file_content = f.read()
    
    os.unlink(temp_file.name)
    return file_content, filename

def test_batch_upload_success(mock_rag_service):
    """Test successful batch upload of multiple files."""
    # Create test files
    file1_content, file1_name = create_test_file("This is test document 1", "test1.txt")
    file2_content, file2_name = create_test_file("This is test document 2", "test2.txt")
    
    # Prepare files for upload
    files = [
        ("files", (file1_name, file1_content, "text/plain")),
        ("files", (file2_name, file2_content, "text/plain"))
    ]
    
    # Make request
    response = client.post(
        "/api/upload-documents",
        files=files,
        data={"api_key": TEST_API_KEY}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert data["total_files"] == 2
    assert data["successful_files"] == 2
    assert data["failed_files"] == 0
    assert len(data["results"]) == 2
    
    # Check individual file results
    for result in data["results"]:
        assert result["status"] == "success"
        assert result["chunks_processed"] == 5  # Mocked to return 5 chunks
        assert result["filename"] in [file1_name, file2_name]

def test_batch_upload_no_files():
    """Test batch upload with no files provided."""
    # FastAPI requires at least one file for List[UploadFile], so this will be a validation error
    response = client.post(
        "/api/upload-documents",
        data={"api_key": TEST_API_KEY}
    )
    
    # FastAPI returns 422 for validation errors
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

def test_batch_upload_file_size_limit():
    """Test batch upload exceeding total file size limit."""
    # Create a large content string (simulate large file)
    large_content = "x" * (30 * 1024 * 1024)  # 30MB
    file1_content, file1_name = create_test_file(large_content, "large1.txt")
    
    # Create another large file to exceed the 50MB limit
    large_content2 = "y" * (25 * 1024 * 1024)  # 25MB (total would be 55MB)
    file2_content, file2_name = create_test_file(large_content2, "large2.txt")
    
    # Prepare files for upload
    files = [
        ("files", (file1_name, file1_content, "text/plain")),
        ("files", (file2_name, file2_content, "text/plain"))
    ]
    
    # Make request
    response = client.post(
        "/api/upload-documents",
        files=files,
        data={"api_key": TEST_API_KEY}
    )
    
    # Verify response
    assert response.status_code == 413
    data = response.json()
    assert data["status"] == "error"
    assert "Combined file size too large" in data["message"]

def test_batch_upload_mixed_success_failure(mock_rag_service):
    """Test batch upload with some successful and some failed files."""
    # Create test files - one valid, one with unsupported extension
    file1_content, file1_name = create_test_file("This is test document 1", "test1.txt")
    file2_content, file2_name = create_test_file("This is test document 2", "test2.xyz")  # Unsupported
    
    # Prepare files for upload
    files = [
        ("files", (file1_name, file1_content, "text/plain")),
        ("files", (file2_name, file2_content, "application/octet-stream"))
    ]
    
    # Make request
    response = client.post(
        "/api/upload-documents",
        files=files,
        data={"api_key": TEST_API_KEY}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "partial_success"
    assert data["total_files"] == 2
    assert data["successful_files"] == 1
    assert data["failed_files"] == 1
    assert len(data["results"]) == 2
    
    # Check individual file results
    success_result = next(r for r in data["results"] if r["status"] == "success")
    failed_result = next(r for r in data["results"] if r["status"] == "failed")
    
    assert success_result["filename"] == file1_name
    assert success_result["chunks_processed"] == 5
    
    assert failed_result["filename"] == file2_name
    assert "Unsupported file type" in failed_result["message"]

if __name__ == "__main__":
    pytest.main([__file__])
