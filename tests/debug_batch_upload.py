"""
Debug script for batch upload functionality.
"""

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

def create_test_file(content: str, filename: str) -> tuple:
    """Create a temporary test file and return file data for upload."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=Path(filename).suffix)
    temp_file.write(content)
    temp_file.close()
    
    with open(temp_file.name, 'rb') as f:
        file_content = f.read()
    
    os.unlink(temp_file.name)
    return file_content, filename

def test_debug():
    """Debug the batch upload functionality."""
    with patch('api.app.get_rag_service') as mock_get_rag:
        mock_rag = MagicMock()
        mock_rag.processed_documents = {'doc1': MagicMock(), 'doc2': MagicMock()}
        
        # Mock the process_document method to return a proper mock
        mock_processed_doc = MagicMock()
        mock_processed_doc.chunks = [MagicMock() for _ in range(5)]
        mock_rag.process_document.return_value = mock_processed_doc
        
        # Mock document mode methods
        mock_session = MagicMock()
        mock_session.mode.value = 'document'
        mock_session.session_id = 'test-session-123'
        mock_session.documents = []
        mock_rag.enter_document_mode.return_value = mock_session
        mock_rag.update_document_chunks_in_session.return_value = None
        
        mock_get_rag.return_value = mock_rag
        
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
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Check if the mock was called
        print(f"Mock called: {mock_get_rag.called}")
        print(f"Process document called: {mock_rag.process_document.called}")

if __name__ == "__main__":
    test_debug()
