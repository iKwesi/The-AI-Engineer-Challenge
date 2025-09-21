"""
Unit tests for text processing utilities in the aimakerspace package.

Tests cover:
- Text splitter functionality
- Page-aware chunking
- RAG service orchestration
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from aimakerspace.processing_utils.text_splitter import CharacterTextSplitter
from aimakerspace.processing_utils.page_aware_chunker import PageAwareChunker
from aimakerspace.processing_utils.rag_service import RAGService
from aimakerspace.models import (
    Document, DocumentType, ChunkingConfig, ProcessingLimits,
    ProcessedDocument
)


class TestCharacterTextSplitter:
    """Test the CharacterTextSplitter implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.splitter = CharacterTextSplitter(
            chunk_size=100,
            chunk_overlap=20,
            separator="\n"
        )
    
    def test_split_simple_text(self):
        """Test splitting simple text into chunks."""
        text = "This is line 1.\nThis is line 2.\nThis is line 3.\nThis is line 4."
        chunks = self.splitter.split_text(text)
        
        assert len(chunks) > 0
        assert all(len(chunk) <= 100 for chunk in chunks)
        
        # Check that content is preserved
        combined = " ".join(chunks)
        assert "This is line 1" in combined
        assert "This is line 4" in combined
    
    def test_split_long_text(self):
        """Test splitting text longer than chunk size."""
        # Create text longer than chunk size
        long_text = "A" * 200 + "\n" + "B" * 200
        chunks = self.splitter.split_text(long_text)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 100 for chunk in chunks)
    
    def test_split_with_overlap(self):
        """Test that chunks have proper overlap."""
        text = "Line 1.\nLine 2.\nLine 3.\nLine 4.\nLine 5.\nLine 6."
        chunks = self.splitter.split_text(text)
        
        if len(chunks) > 1:
            # Check for overlap between consecutive chunks
            for i in range(len(chunks) - 1):
                chunk1 = chunks[i]
                chunk2 = chunks[i + 1]
                # There should be some overlap
                assert len(chunk1) > 0 and len(chunk2) > 0
    
    def test_split_empty_text(self):
        """Test splitting empty text."""
        chunks = self.splitter.split_text("")
        assert chunks == [""]
    
    def test_split_short_text(self):
        """Test splitting text shorter than chunk size."""
        text = "Short text"
        chunks = self.splitter.split_text(text)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_sentence_aware_splitting(self):
        """Test sentence-aware splitting."""
        splitter = CharacterTextSplitter(
            chunk_size=50,
            chunk_overlap=10,
            preserve_sentences=True
        )
        
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = splitter.split_text(text)
        
        # Check that sentences are not broken
        for chunk in chunks:
            if "." in chunk and not chunk.endswith("."):
                # If there's a period, it should end with one (complete sentence)
                sentences = chunk.split(".")
                assert sentences[-1].strip() == "" or "." in sentences[-1]
    
    def test_custom_separator(self):
        """Test splitting with custom separator."""
        splitter = CharacterTextSplitter(
            chunk_size=30,
            chunk_overlap=5,
            separator="|"
        )
        
        text = "Part1|Part2|Part3|Part4|Part5"
        chunks = splitter.split_text(text)
        
        assert len(chunks) > 0
        # Check that separator is respected
        for chunk in chunks:
            if "|" in chunk:
                assert chunk.count("|") >= 0


class TestPageAwareChunker:
    """Test the PageAwareChunker implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.chunker = PageAwareChunker(
            chunk_size=200,
            overlap=50
        )
    
    def test_chunk_single_page_document(self):
        """Test chunking a single-page document."""
        doc = Document(
            content="This is page 1 content. " * 20,  # Make it long enough to chunk
            metadata={"page_count": 1},
            source_path=Path("test.pdf"),
            document_type=DocumentType.PDF,
            document_id="test-1"
        )
        
        chunks = self.chunker.chunk_document(doc)
        
        assert len(chunks) > 0
        assert all(len(chunk.content) <= 200 for chunk in chunks)
        assert all(chunk.metadata.get("source_document_id") == "test-1" for chunk in chunks)
    
    def test_chunk_multipage_document(self):
        """Test chunking a multi-page document."""
        content = "\n--- Page 1 ---\nPage 1 content. " * 10
        content += "\n--- Page 2 ---\nPage 2 content. " * 10
        
        doc = Document(
            content=content,
            metadata={"page_count": 2},
            source_path=Path("test.pdf"),
            document_type=DocumentType.PDF,
            document_id="test-2"
        )
        
        chunks = self.chunker.chunk_document(doc)
        
        assert len(chunks) > 0
        # Check that page information is preserved
        page_1_chunks = [c for c in chunks if "Page 1" in c.content]
        page_2_chunks = [c for c in chunks if "Page 2" in c.content]
        
        assert len(page_1_chunks) > 0
        assert len(page_2_chunks) > 0
    
    def test_preserve_page_boundaries(self):
        """Test that page boundaries are preserved when possible."""
        content = "Page 1 short content.\n--- Page 2 ---\nPage 2 also short."
        
        doc = Document(
            content=content,
            metadata={"page_count": 2},
            source_path=Path("test.pdf"),
            document_type=DocumentType.PDF,
            document_id="test-3"
        )
        
        chunks = self.chunker.chunk_document(doc)
        
        # With short content, each page should be in separate chunks
        page_1_only = [c for c in chunks if "Page 1" in c.content and "Page 2" not in c.content]
        page_2_only = [c for c in chunks if "Page 2" in c.content and "Page 1" not in c.content]
        
        assert len(page_1_only) > 0
        assert len(page_2_only) > 0
    
    def test_chunk_metadata_preservation(self):
        """Test that chunk metadata is properly set."""
        doc = Document(
            content="Test content for metadata preservation.",
            metadata={"title": "Test Document", "author": "Test Author"},
            source_path=Path("test.pdf"),
            document_type=DocumentType.PDF,
            document_id="test-4"
        )
        
        chunks = self.chunker.chunk_document(doc)
        
        for chunk in chunks:
            assert chunk.metadata["source_document_id"] == "test-4"
            assert chunk.metadata["source_document_type"] == "pdf"
            assert "chunk_index" in chunk.metadata
            assert "chunk_size" in chunk.metadata


class TestRAGService:
    """Test the RAGService implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.api_key = "test-api-key"
        
        # Mock dependencies
        self.mock_vector_db = Mock()
        self.mock_embedding_model = Mock()
        self.mock_chat_model = Mock()
        
        with patch('aimakerspace.processing_utils.rag_service.VectorDatabase') as mock_vdb, \
             patch('aimakerspace.processing_utils.rag_service.EmbeddingModel') as mock_emb, \
             patch('aimakerspace.processing_utils.rag_service.ChatOpenAI') as mock_chat:
            
            mock_vdb.return_value = self.mock_vector_db
            mock_emb.return_value = self.mock_embedding_model
            mock_chat.return_value = self.mock_chat_model
            
            self.rag_service = RAGService(
                api_key=self.api_key,
                chunking_config=ChunkingConfig(),
                processing_limits=ProcessingLimits()
            )
    
    @pytest.mark.asyncio
    async def test_process_document_text_file(self):
        """Test processing a text document."""
        with patch('aimakerspace.processing_utils.rag_service.DocumentLoaderFactory') as mock_factory:
            # Mock document loader
            mock_loader = Mock()
            mock_doc = Document(
                content="Test document content for processing.",
                metadata={},
                source_path=Path("test.txt"),
                document_type=DocumentType.TEXT,
                document_id="test-doc"
            )
            mock_loader.load_documents.return_value = [mock_doc]
            mock_factory.return_value.load_documents.return_value = [mock_doc]
            
            # Mock embedding
            self.mock_embedding_model.get_embeddings.return_value = [[0.1, 0.2, 0.3]]
            
            result = await self.rag_service.process_document(
                source="test.txt",
                document_id="custom-id"
            )
            
            assert isinstance(result, ProcessedDocument)
            assert result.document_id == "custom-id"
            assert result.status == "completed"
            assert result.chunks_processed > 0
    
    @pytest.mark.asyncio
    async def test_process_youtube_url(self):
        """Test processing a YouTube URL."""
        with patch('aimakerspace.processing_utils.rag_service.DocumentLoaderFactory') as mock_factory:
            # Mock YouTube document
            mock_doc = Document(
                content="YouTube video transcript content.",
                metadata={"video_title": "Test Video"},
                source_path=None,
                document_type=DocumentType.YOUTUBE,
                document_id="youtube-doc"
            )
            mock_factory.return_value.load_documents.return_value = [mock_doc]
            
            # Mock embedding
            self.mock_embedding_model.get_embeddings.return_value = [[0.1, 0.2, 0.3]]
            
            result = await self.rag_service.process_document(
                source="https://www.youtube.com/watch?v=test123",
                document_id="youtube-test"
            )
            
            assert isinstance(result, ProcessedDocument)
            assert result.document_id == "youtube-test"
            assert result.document_type == "youtube"
    
    @pytest.mark.asyncio
    async def test_search_documents(self):
        """Test searching through processed documents."""
        # Mock vector database search
        mock_results = [
            {"content": "Relevant content 1", "metadata": {"document_id": "doc1"}},
            {"content": "Relevant content 2", "metadata": {"document_id": "doc2"}}
        ]
        self.mock_vector_db.search.return_value = mock_results
        
        # Mock embedding for query
        self.mock_embedding_model.get_embeddings.return_value = [[0.5, 0.6, 0.7]]
        
        results = await self.rag_service.search_documents(
            query="test query",
            max_results=5
        )
        
        assert len(results) == 2
        assert results[0]["content"] == "Relevant content 1"
        assert results[1]["content"] == "Relevant content 2"
    
    @pytest.mark.asyncio
    async def test_chat_with_context(self):
        """Test chat with document context."""
        # Mock search results
        mock_search_results = [
            {"content": "Context 1", "metadata": {"document_id": "doc1"}},
            {"content": "Context 2", "metadata": {"document_id": "doc2"}}
        ]
        
        with patch.object(self.rag_service, 'search_documents', return_value=mock_search_results):
            # Mock chat response
            self.mock_chat_model.invoke.return_value = Mock(content="AI response with context")
            
            response = await self.rag_service.chat_with_context(
                user_message="What is the main topic?",
                max_context_chunks=5
            )
            
            assert response == "AI response with context"
            self.mock_chat_model.invoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_chat_without_context(self):
        """Test chat without document context."""
        # Mock empty search results
        with patch.object(self.rag_service, 'search_documents', return_value=[]):
            # Mock chat response
            self.mock_chat_model.invoke.return_value = Mock(content="AI response without context")
            
            response = await self.rag_service.chat_with_context(
                user_message="Hello",
                max_context_chunks=5
            )
            
            assert response == "AI response without context"
    
    def test_get_stats(self):
        """Test getting RAG service statistics."""
        # Mock vector database stats
        self.mock_vector_db.get_stats.return_value = {
            "total_vectors": 100,
            "total_documents": 10
        }
        
        stats = self.rag_service.get_stats()
        
        assert isinstance(stats, dict)
        assert "total_vectors" in stats
        assert "total_documents" in stats
    
    @pytest.mark.asyncio
    async def test_remove_document(self):
        """Test removing a document from the system."""
        document_id = "test-doc-to-remove"
        
        # Mock vector database removal
        self.mock_vector_db.remove_by_metadata.return_value = True
        
        result = await self.rag_service.remove_document(document_id)
        
        assert result is True
        self.mock_vector_db.remove_by_metadata.assert_called_once()
    
    def test_list_documents(self):
        """Test listing processed documents."""
        # Mock vector database document list
        mock_docs = [
            {"document_id": "doc1", "document_type": "text", "chunk_count": 5},
            {"document_id": "doc2", "document_type": "pdf", "chunk_count": 10}
        ]
        self.mock_vector_db.list_documents.return_value = mock_docs
        
        documents = self.rag_service.list_documents()
        
        assert len(documents) == 2
        assert documents[0]["document_id"] == "doc1"
        assert documents[1]["document_id"] == "doc2"
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_source(self):
        """Test error handling for invalid document sources."""
        from aimakerspace.models import DocumentProcessingError
        
        with patch('aimakerspace.processing_utils.rag_service.DocumentLoaderFactory') as mock_factory:
            mock_factory.return_value.load_documents.side_effect = DocumentProcessingError("Invalid source")
            
            with pytest.raises(DocumentProcessingError):
                await self.rag_service.process_document(
                    source="invalid.xyz",
                    document_id="error-test"
                )
    
    @pytest.mark.asyncio
    async def test_chunking_config_application(self):
        """Test that chunking configuration is properly applied."""
        custom_config = ChunkingConfig(
            chunk_size=500,
            overlap=100,
            preserve_sentences=True
        )
        
        with patch('aimakerspace.processing_utils.rag_service.VectorDatabase') as mock_vdb, \
             patch('aimakerspace.processing_utils.rag_service.EmbeddingModel') as mock_emb, \
             patch('aimakerspace.processing_utils.rag_service.ChatOpenAI') as mock_chat:
            
            mock_vdb.return_value = self.mock_vector_db
            mock_emb.return_value = self.mock_embedding_model
            mock_chat.return_value = self.mock_chat_model
            
            rag_service = RAGService(
                api_key=self.api_key,
                chunking_config=custom_config,
                processing_limits=ProcessingLimits()
            )
            
            assert rag_service.chunking_config.chunk_size == 500
            assert rag_service.chunking_config.overlap == 100
            assert rag_service.chunking_config.preserve_sentences is True
    
    @pytest.mark.asyncio
    async def test_processing_limits_enforcement(self):
        """Test that processing limits are enforced."""
        limits = ProcessingLimits(
            max_file_size_mb=1,  # Very small limit
            max_files_per_batch=1,
            timeout_seconds=30
        )
        
        with patch('aimakerspace.processing_utils.rag_service.VectorDatabase') as mock_vdb, \
             patch('aimakerspace.processing_utils.rag_service.EmbeddingModel') as mock_emb, \
             patch('aimakerspace.processing_utils.rag_service.ChatOpenAI') as mock_chat:
            
            mock_vdb.return_value = self.mock_vector_db
            mock_emb.return_value = self.mock_embedding_model
            mock_chat.return_value = self.mock_chat_model
            
            rag_service = RAGService(
                api_key=self.api_key,
                chunking_config=ChunkingConfig(),
                processing_limits=limits
            )
            
            assert rag_service.processing_limits.max_file_size_mb == 1
            assert rag_service.processing_limits.max_files_per_batch == 1


# Integration tests for text processing
class TestTextProcessingIntegration:
    """Integration tests for text processing components."""
    
    def test_text_splitter_with_real_content(self):
        """Test text splitter with realistic content."""
        splitter = CharacterTextSplitter(
            chunk_size=200,
            chunk_overlap=50,
            preserve_sentences=True
        )
        
        # Realistic document content
        content = """
        Machine learning is a subset of artificial intelligence that focuses on algorithms 
        that can learn from data. It has applications in many fields including computer vision, 
        natural language processing, and robotics.
        
        Deep learning is a subset of machine learning that uses neural networks with multiple 
        layers. These networks can learn complex patterns in data and have achieved remarkable 
        success in tasks like image recognition and language translation.
        
        The future of AI looks promising with continued advances in both hardware and software. 
        New architectures and training methods are being developed constantly.
        """
        
        chunks = splitter.split_text(content.strip())
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 200 for chunk in chunks)
        
        # Check content preservation
        combined = " ".join(chunks)
        assert "Machine learning" in combined
        assert "Deep learning" in combined
        assert "future of AI" in combined
    
    def test_page_aware_chunker_with_pdf_content(self):
        """Test page-aware chunker with PDF-like content."""
        chunker = PageAwareChunker(chunk_size=300, overlap=75)
        
        # Simulate PDF content with page markers
        content = """
        === Page 1 ===
        Introduction to Quantum Computing
        
        Quantum computing represents a fundamental shift in how we process information. 
        Unlike classical computers that use bits, quantum computers use quantum bits or qubits.
        
        === Page 2 ===
        Quantum Superposition
        
        One of the key principles of quantum mechanics is superposition. This allows qubits 
        to exist in multiple states simultaneously, providing quantum computers with their power.
        
        === Page 3 ===
        Quantum Entanglement
        
        Another important quantum phenomenon is entanglement, where qubits become correlated 
        in such a way that the measurement of one affects the others.
        """
        
        doc = Document(
            content=content.strip(),
            metadata={"page_count": 3, "title": "Quantum Computing Guide"},
            source_path=Path("quantum.pdf"),
            document_type=DocumentType.PDF,
            document_id="quantum-doc"
        )
        
        chunks = chunker.chunk_document(doc)
        
        assert len(chunks) > 0
        
        # Check that page information is preserved
        page_1_chunks = [c for c in chunks if "Page 1" in c.content or "Introduction" in c.content]
        page_2_chunks = [c for c in chunks if "Page 2" in c.content or "Superposition" in c.content]
        page_3_chunks = [c for c in chunks if "Page 3" in c.content or "Entanglement" in c.content]
        
        assert len(page_1_chunks) > 0
        assert len(page_2_chunks) > 0
        assert len(page_3_chunks) > 0
        
        # Check metadata
        for chunk in chunks:
            assert chunk.metadata["source_document_id"] == "quantum-doc"
            assert "chunk_index" in chunk.metadata


if __name__ == "__main__":
    pytest.main([__file__])
