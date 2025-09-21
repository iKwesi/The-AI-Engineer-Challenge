"""
Unit tests for document loaders in the aimakerspace package.

Tests cover all document loader implementations including:
- Base DocumentLoader functionality
- Text file loading
- PDF loading
- Word document loading
- Excel/CSV loading
- YouTube transcript loading
- Document factory functionality
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from aimakerspace.document_utils.base import DocumentLoader
from aimakerspace.document_utils.text_utils import TextFileLoader
from aimakerspace.document_utils.pdf_utils import PDFLoader
from aimakerspace.document_utils.word_utils import WordDocumentLoader
from aimakerspace.document_utils.excel_utils import ExcelLoader
from aimakerspace.document_utils.youtube_utils import YouTubeLoader
from aimakerspace.document_utils.factory import DocumentLoaderFactory
from aimakerspace.models import Document, DocumentType, DocumentProcessingError


class TestDocumentLoader:
    """Test the base DocumentLoader abstract class."""
    
    def test_abstract_class_cannot_be_instantiated(self):
        """Test that DocumentLoader cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DocumentLoader()
    
    def test_generate_document_id(self):
        """Test document ID generation."""
        # Create a concrete implementation for testing
        class TestLoader(DocumentLoader):
            def can_load(self, source):
                return True
            def load_documents(self, source):
                return []
        
        loader = TestLoader()
        doc_id = loader.generate_document_id()
        assert isinstance(doc_id, str)
        assert len(doc_id) > 0
        
        # Test that IDs are unique
        doc_id2 = loader.generate_document_id()
        assert doc_id != doc_id2


class TestTextFileLoader:
    """Test the TextFileLoader implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.loader = TextFileLoader()
    
    def test_can_load_text_files(self):
        """Test that loader can identify text files."""
        assert self.loader.can_load(Path("test.txt"))
        assert self.loader.can_load(Path("document.text"))
        assert not self.loader.can_load(Path("document.pdf"))
        assert not self.loader.can_load(Path("document.docx"))
    
    def test_load_simple_text_file(self):
        """Test loading a simple text file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            test_content = "This is a test document.\nIt has multiple lines.\nAnd some content."
            f.write(test_content)
            f.flush()
            
            try:
                documents = self.loader.load_documents(Path(f.name))
                
                assert len(documents) == 1
                doc = documents[0]
                assert isinstance(doc, Document)
                assert doc.content == test_content
                assert doc.document_type == DocumentType.TEXT
                assert doc.source_path == Path(f.name)
                assert "encoding" in doc.metadata
                assert "file_size" in doc.metadata
                assert "line_count" in doc.metadata
                
            finally:
                os.unlink(f.name)
    
    def test_load_utf8_text_file(self):
        """Test loading a UTF-8 text file with special characters."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            test_content = "Test with émojis 🚀 and special chars: àáâãäå"
            f.write(test_content)
            f.flush()
            
            try:
                documents = self.loader.load_documents(Path(f.name))
                
                assert len(documents) == 1
                doc = documents[0]
                assert doc.content == test_content
                assert doc.metadata["encoding"] == "utf-8"
                
            finally:
                os.unlink(f.name)
    
    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist."""
        with pytest.raises(DocumentProcessingError):
            self.loader.load_documents(Path("nonexistent.txt"))
    
    def test_load_empty_file(self):
        """Test loading an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("")
            f.flush()
            
            try:
                documents = self.loader.load_documents(Path(f.name))
                
                assert len(documents) == 1
                doc = documents[0]
                assert doc.content == ""
                assert doc.metadata["line_count"] == 0
                
            finally:
                os.unlink(f.name)


class TestPDFLoader:
    """Test the PDFLoader implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.loader = PDFLoader()
    
    def test_can_load_pdf_files(self):
        """Test that loader can identify PDF files."""
        assert self.loader.can_load(Path("test.pdf"))
        assert self.loader.can_load(Path("document.PDF"))
        assert not self.loader.can_load(Path("document.txt"))
        assert not self.loader.can_load(Path("document.docx"))
    
    @patch('aimakerspace.document_utils.pdf_utils.PdfReader')
    def test_load_simple_pdf(self, mock_pdf_reader):
        """Test loading a simple PDF file."""
        # Mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "Page 1 content"
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_reader.metadata = {
            '/Title': 'Test PDF',
            '/Author': 'Test Author',
            '/CreationDate': 'D:20240101120000'
        }
        mock_pdf_reader.return_value = mock_reader
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            try:
                documents = self.loader.load_documents(Path(f.name))
                
                assert len(documents) == 1
                doc = documents[0]
                assert isinstance(doc, Document)
                assert "Page 1 content" in doc.content
                assert doc.document_type == DocumentType.PDF
                assert doc.source_path == Path(f.name)
                assert "page_count" in doc.metadata
                assert "title" in doc.metadata
                
            finally:
                os.unlink(f.name)
    
    @patch('aimakerspace.document_utils.pdf_utils.PdfReader')
    def test_load_multipage_pdf(self, mock_pdf_reader):
        """Test loading a multi-page PDF."""
        # Mock multiple pages
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 content"
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_reader.metadata = {}
        mock_pdf_reader.return_value = mock_reader
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            try:
                documents = self.loader.load_documents(Path(f.name))
                
                assert len(documents) == 1
                doc = documents[0]
                assert "Page 1 content" in doc.content
                assert "Page 2 content" in doc.content
                assert doc.metadata["page_count"] == 2
                
            finally:
                os.unlink(f.name)
    
    @patch('aimakerspace.document_utils.pdf_utils.PdfReader')
    def test_load_corrupted_pdf(self, mock_pdf_reader):
        """Test handling of corrupted PDF files."""
        mock_pdf_reader.side_effect = Exception("Corrupted PDF")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            try:
                with pytest.raises(DocumentProcessingError):
                    self.loader.load_documents(Path(f.name))
                    
            finally:
                os.unlink(f.name)


class TestWordDocumentLoader:
    """Test the WordDocumentLoader implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.loader = WordDocumentLoader()
    
    def test_can_load_word_files(self):
        """Test that loader can identify Word files."""
        assert self.loader.can_load(Path("test.docx"))
        assert self.loader.can_load(Path("document.doc"))
        assert self.loader.can_load(Path("file.DOCX"))
        assert not self.loader.can_load(Path("document.txt"))
        assert not self.loader.can_load(Path("document.pdf"))
    
    @patch('aimakerspace.document_utils.word_utils.Document')
    def test_load_simple_docx(self, mock_document):
        """Test loading a simple DOCX file."""
        # Mock document with paragraphs
        mock_para1 = Mock()
        mock_para1.text = "First paragraph"
        mock_para2 = Mock()
        mock_para2.text = "Second paragraph"
        
        mock_doc = Mock()
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_doc.tables = []
        mock_doc.core_properties.title = "Test Document"
        mock_doc.core_properties.author = "Test Author"
        mock_doc.core_properties.created = None
        mock_document.return_value = mock_doc
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            try:
                documents = self.loader.load_documents(Path(f.name))
                
                assert len(documents) == 1
                doc = documents[0]
                assert isinstance(doc, Document)
                assert "First paragraph" in doc.content
                assert "Second paragraph" in doc.content
                assert doc.document_type == DocumentType.WORD
                assert "paragraph_count" in doc.metadata
                assert "title" in doc.metadata
                
            finally:
                os.unlink(f.name)
    
    @patch('aimakerspace.document_utils.word_utils.Document')
    def test_load_docx_with_tables(self, mock_document):
        """Test loading a DOCX file with tables."""
        # Mock document with table
        mock_cell1 = Mock()
        mock_cell1.text = "Cell 1"
        mock_cell2 = Mock()
        mock_cell2.text = "Cell 2"
        
        mock_row = Mock()
        mock_row.cells = [mock_cell1, mock_cell2]
        
        mock_table = Mock()
        mock_table.rows = [mock_row]
        
        mock_doc = Mock()
        mock_doc.paragraphs = []
        mock_doc.tables = [mock_table]
        mock_doc.core_properties.title = None
        mock_doc.core_properties.author = None
        mock_doc.core_properties.created = None
        mock_document.return_value = mock_doc
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            try:
                documents = self.loader.load_documents(Path(f.name))
                
                assert len(documents) == 1
                doc = documents[0]
                assert "Cell 1" in doc.content
                assert "Cell 2" in doc.content
                assert doc.metadata["table_count"] == 1
                
            finally:
                os.unlink(f.name)


class TestExcelLoader:
    """Test the ExcelLoader implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.loader = ExcelLoader()
    
    def test_can_load_excel_files(self):
        """Test that loader can identify Excel files."""
        assert self.loader.can_load(Path("test.xlsx"))
        assert self.loader.can_load(Path("data.xls"))
        assert self.loader.can_load(Path("file.csv"))
        assert self.loader.can_load(Path("FILE.XLSX"))
        assert not self.loader.can_load(Path("document.txt"))
        assert not self.loader.can_load(Path("document.pdf"))
    
    @patch('aimakerspace.document_utils.excel_utils.pd.read_excel')
    def test_load_simple_xlsx(self, mock_read_excel):
        """Test loading a simple Excel file."""
        # Mock pandas DataFrame
        import pandas as pd
        mock_df = pd.DataFrame({
            'Name': ['John', 'Jane'],
            'Age': [30, 25],
            'City': ['New York', 'Boston']
        })
        mock_read_excel.return_value = mock_df
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            try:
                documents = self.loader.load_documents(Path(f.name))
                
                assert len(documents) == 1
                doc = documents[0]
                assert isinstance(doc, Document)
                assert "John" in doc.content
                assert "Jane" in doc.content
                assert "New York" in doc.content
                assert doc.document_type == DocumentType.EXCEL
                assert "sheet_count" in doc.metadata
                assert "row_count" in doc.metadata
                
            finally:
                os.unlink(f.name)
    
    @patch('aimakerspace.document_utils.excel_utils.pd.read_csv')
    def test_load_csv_file(self, mock_read_csv):
        """Test loading a CSV file."""
        import pandas as pd
        mock_df = pd.DataFrame({
            'Product': ['Apple', 'Banana'],
            'Price': [1.50, 0.75]
        })
        mock_read_csv.return_value = mock_df
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            try:
                documents = self.loader.load_documents(Path(f.name))
                
                assert len(documents) == 1
                doc = documents[0]
                assert "Apple" in doc.content
                assert "Banana" in doc.content
                assert doc.document_type == DocumentType.EXCEL
                
            finally:
                os.unlink(f.name)


class TestYouTubeLoader:
    """Test the YouTubeLoader implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.loader = YouTubeLoader()
    
    def test_can_load_youtube_urls(self):
        """Test that loader can identify YouTube URLs."""
        assert self.loader.can_load("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert self.loader.can_load("https://youtu.be/dQw4w9WgXcQ")
        assert self.loader.can_load("https://youtube.com/embed/dQw4w9WgXcQ")
        assert not self.loader.can_load("https://vimeo.com/123456")
        assert not self.loader.can_load(Path("video.mp4"))
    
    def test_extract_video_id(self):
        """Test extracting video ID from various YouTube URL formats."""
        test_cases = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://www.youtube.com/v/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ]
        
        for url, expected_id in test_cases:
            video_id = self.loader._extract_video_id(url)
            assert video_id == expected_id
    
    def test_extract_video_id_invalid_url(self):
        """Test extracting video ID from invalid URLs."""
        from aimakerspace.models import YouTubeProcessingError
        
        with pytest.raises(YouTubeProcessingError):
            self.loader._extract_video_id("https://vimeo.com/123456")
    
    @patch('aimakerspace.document_utils.youtube_utils.YouTubeTranscriptApi')
    @patch('aimakerspace.document_utils.youtube_utils.pytube.YouTube')
    def test_load_youtube_video(self, mock_youtube, mock_transcript_api):
        """Test loading a YouTube video with transcript."""
        # Mock transcript
        mock_transcript_list = Mock()
        mock_transcript = Mock()
        mock_transcript.fetch.return_value = [
            {'text': 'Hello world', 'start': 0.0, 'duration': 2.0},
            {'text': 'This is a test', 'start': 2.0, 'duration': 3.0}
        ]
        mock_transcript_list.find_manually_created_transcript.return_value = mock_transcript
        mock_transcript_api.list_transcripts.return_value = mock_transcript_list
        
        # Mock YouTube metadata
        mock_yt = Mock()
        mock_yt.title = "Test Video"
        mock_yt.author = "Test Channel"
        mock_yt.length = 300
        mock_yt.views = 1000
        mock_yt.publish_date = None
        mock_yt.description = "Test description"
        mock_yt.keywords = ["test", "video"]
        mock_youtube.return_value = mock_yt
        
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        documents = self.loader.load_documents(url)
        
        assert len(documents) == 1
        doc = documents[0]
        assert isinstance(doc, Document)
        assert "Test Video" in doc.content
        assert "Hello world" in doc.content
        assert "This is a test" in doc.content
        assert doc.document_type == DocumentType.YOUTUBE
        assert doc.metadata["video_title"] == "Test Video"
        assert doc.metadata["channel_name"] == "Test Channel"
    
    def test_detect_youtube_urls(self):
        """Test detecting YouTube URLs in text."""
        text = """
        Check out this video: https://www.youtube.com/watch?v=dQw4w9WgXcQ
        And this one too: https://youtu.be/abc123
        Also visit https://example.com (not YouTube)
        """
        
        urls = self.loader.detect_youtube_urls(text)
        assert len(urls) == 2
        assert "https://www.youtube.com/watch?v=dQw4w9WgXcQ" in urls
        assert "https://youtu.be/abc123" in urls


class TestDocumentLoaderFactory:
    """Test the DocumentLoaderFactory implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = DocumentLoaderFactory()
    
    def test_get_supported_formats(self):
        """Test getting supported file formats."""
        formats = self.factory.get_supported_formats()
        
        assert isinstance(formats, dict)
        assert "text" in formats
        assert "pdf" in formats
        assert "word" in formats
        assert "excel" in formats
        assert "youtube" in formats
    
    def test_can_load_various_formats(self):
        """Test format detection for various file types."""
        test_cases = [
            ("document.txt", True),
            ("file.pdf", True),
            ("presentation.docx", True),
            ("data.xlsx", True),
            ("https://www.youtube.com/watch?v=abc123", True),
            ("unknown.xyz", False),
            ("", False),
        ]
        
        for source, expected in test_cases:
            result = self.factory.can_load(source)
            assert result == expected, f"Failed for {source}"
    
    def test_get_loader_for_text_file(self):
        """Test getting the correct loader for text files."""
        loader = self.factory.get_loader(Path("test.txt"))
        assert isinstance(loader, TextFileLoader)
    
    def test_get_loader_for_pdf_file(self):
        """Test getting the correct loader for PDF files."""
        loader = self.factory.get_loader(Path("test.pdf"))
        assert isinstance(loader, PDFLoader)
    
    def test_get_loader_for_word_file(self):
        """Test getting the correct loader for Word files."""
        loader = self.factory.get_loader(Path("test.docx"))
        assert isinstance(loader, WordDocumentLoader)
    
    def test_get_loader_for_excel_file(self):
        """Test getting the correct loader for Excel files."""
        loader = self.factory.get_loader(Path("test.xlsx"))
        assert isinstance(loader, ExcelLoader)
    
    def test_get_loader_for_youtube_url(self):
        """Test getting the correct loader for YouTube URLs."""
        loader = self.factory.get_loader("https://www.youtube.com/watch?v=abc123")
        assert isinstance(loader, YouTubeLoader)
    
    def test_get_loader_for_unsupported_format(self):
        """Test handling of unsupported file formats."""
        with pytest.raises(DocumentProcessingError):
            self.factory.get_loader(Path("unknown.xyz"))
    
    @patch('aimakerspace.document_utils.text_utils.TextFileLoader.load_documents')
    def test_load_documents_text_file(self, mock_load):
        """Test loading documents through the factory."""
        mock_doc = Document(
            content="Test content",
            metadata={},
            source_path=Path("test.txt"),
            document_type=DocumentType.TEXT,
            document_id="test-id"
        )
        mock_load.return_value = [mock_doc]
        
        documents = self.factory.load_documents(Path("test.txt"))
        
        assert len(documents) == 1
        assert documents[0] == mock_doc
        mock_load.assert_called_once()
    
    def test_load_multiple_documents(self):
        """Test loading multiple documents with different formats."""
        sources = [
            Path("test1.txt"),
            Path("test2.pdf"),
            "https://www.youtube.com/watch?v=abc123"
        ]
        
        with patch.object(self.factory, 'load_documents') as mock_load:
            mock_load.return_value = [Mock(spec=Document)]
            
            all_documents = []
            for source in sources:
                docs = self.factory.load_documents(source)
                all_documents.extend(docs)
            
            assert len(all_documents) == 3
            assert mock_load.call_count == 3


# Integration tests
class TestDocumentLoadersIntegration:
    """Integration tests for document loaders."""
    
    def test_factory_with_real_text_file(self):
        """Test factory with a real text file."""
        factory = DocumentLoaderFactory()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            test_content = "This is integration test content.\nMultiple lines here."
            f.write(test_content)
            f.flush()
            
            try:
                documents = factory.load_documents(Path(f.name))
                
                assert len(documents) == 1
                doc = documents[0]
                assert doc.content == test_content
                assert doc.document_type == DocumentType.TEXT
                
            finally:
                os.unlink(f.name)
    
    def test_error_handling_chain(self):
        """Test error handling through the entire chain."""
        factory = DocumentLoaderFactory()
        
        # Test with non-existent file
        with pytest.raises(DocumentProcessingError):
            factory.load_documents(Path("nonexistent.txt"))
        
        # Test with unsupported format
        with pytest.raises(DocumentProcessingError):
            factory.load_documents(Path("unsupported.xyz"))


if __name__ == "__main__":
    pytest.main([__file__])
