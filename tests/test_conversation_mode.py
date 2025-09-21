"""
Tests for conversation mode management functionality.

This module tests the ConversationModeManager class and related RAG service
conversation mode features including fallback detection, conflict resolution,
and session management.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import List, Dict, Any

from aimakerspace.processing_utils.conversation_mode_manager import (
    ConversationModeManager,
    ConversationMode,
    DocumentModeSession,
    FallbackRequest,
    ConflictDetection,
    ConflictResolution
)
from aimakerspace.models import Document, Chunk, SearchResult, SearchQuery, DocumentType


class TestConversationModeManager:
    """Test cases for ConversationModeManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConversationModeManager(
            confidence_threshold=0.7,
            session_duration_hours=24,
            max_documents_per_session=5
        )
        
        # Create mock documents
        self.mock_documents = [
            Document(
                content="This is test document 1 content.",
                document_id="doc1",
                document_type=DocumentType.PDF,
                metadata={"filename": "test1.pdf"}
            ),
            Document(
                content="This is test document 2 content.",
                document_id="doc2",
                document_type=DocumentType.PDF,
                metadata={"filename": "test2.pdf"}
            )
        ]
        
        # Create mock chunks
        self.mock_chunks = [
            Chunk(
                content="Test chunk content 1",
                chunk_index=0,
                source_document_id="doc1",
                chunk_id="chunk1",
                metadata={"filename": "test1.pdf"}
            ),
            Chunk(
                content="Test chunk content 2",
                chunk_index=1,
                source_document_id="doc1",
                chunk_id="chunk2",
                metadata={"filename": "test1.pdf"}
            )
        ]
    
    def test_create_session(self):
        """Test session creation."""
        session = self.manager.create_session()
        
        assert session.mode == ConversationMode.GENERAL
        assert session.session_id is not None
        assert len(session.session_id) > 0
        assert session.documents == {}
        assert self.manager.current_session == session
        assert self.manager.stats['sessions_created'] == 1
    
    def test_enter_document_mode(self):
        """Test entering document mode."""
        session = self.manager.enter_document_mode(self.mock_documents)
        
        assert session.mode == ConversationMode.DOCUMENT
        assert len(session.documents) == 2
        assert "doc1" in session.documents
        assert "doc2" in session.documents
        assert session.documents["doc1"]["name"] == "test1.pdf"
        assert self.manager.stats['documents_added'] == 2
        assert self.manager.stats['mode_switches'] == 1
    
    def test_enter_document_mode_too_many_documents(self):
        """Test entering document mode with too many documents."""
        # Create more documents than allowed
        many_docs = [
            Document(
                content=f"Content {i}",
                document_id=f"doc{i}",
                document_type=DocumentType.PDF,
                metadata={"filename": f"test{i}.pdf"}
            )
            for i in range(10)  # More than max_documents_per_session (5)
        ]
        
        with pytest.raises(ValueError, match="Too many documents"):
            self.manager.enter_document_mode(many_docs)
    
    def test_exit_document_mode(self):
        """Test exiting document mode."""
        # First enter document mode
        self.manager.enter_document_mode(self.mock_documents)
        
        # Then exit
        session = self.manager.exit_document_mode()
        
        assert session.mode == ConversationMode.GENERAL
        assert len(session.documents) == 0
        assert self.manager.stats['mode_switches'] == 2  # Enter + Exit
    
    def test_query_with_fallback_high_confidence(self):
        """Test query with high confidence (no fallback needed)."""
        # Enter document mode
        self.manager.enter_document_mode(self.mock_documents)
        
        # Create high-confidence search result (matching chunks and scores)
        # Using very high scores to ensure weighted average exceeds any threshold
        search_result = SearchResult(
            chunks=self.mock_chunks,
            scores=[0.98, 0.95],  # Very high confidence scores
            query=SearchQuery(query_text="How does this work?", k=5, min_score=0.0, filters={})
        )
        
        # Use a specific question that lowers the threshold
        needs_fallback, fallback_request = self.manager.query_with_fallback(
            "How does this work?", search_result
        )
        
        assert not needs_fallback
        assert fallback_request is None
        # The weighted average should be: 0.98*0.5 + 0.95*0.3 = 0.775
        # And the specific question should lower the threshold below this
        assert self.manager.current_session.conversation_context['last_confidence_score'] > 0.7
    
    def test_query_with_fallback_low_confidence(self):
        """Test query with low confidence (fallback needed)."""
        # Enter document mode
        self.manager.enter_document_mode(self.mock_documents)
        
        # Create low-confidence search result
        search_result = SearchResult(
            chunks=self.mock_chunks,
            scores=[0.3, 0.2],  # Low confidence scores
            query=SearchQuery(query_text="test query", k=5, min_score=0.0, filters={})
        )
        
        needs_fallback, fallback_request = self.manager.query_with_fallback(
            "test query", search_result
        )
        
        assert needs_fallback
        assert fallback_request is not None
        assert fallback_request.query == "test query"
        assert fallback_request.confidence_score < 0.7
        assert len(fallback_request.retrieved_chunks) == 2
        assert self.manager.stats['fallback_requests'] == 1
    
    def test_query_with_fallback_not_in_document_mode(self):
        """Test query fallback when not in document mode."""
        search_result = SearchResult(
            chunks=self.mock_chunks,
            scores=[0.3, 0.2],
            query=SearchQuery(query_text="test query", k=5, min_score=0.0, filters={})
        )
        
        needs_fallback, fallback_request = self.manager.query_with_fallback(
            "test query", search_result
        )
        
        assert not needs_fallback
        assert fallback_request is None
    
    def test_detect_multi_document_conflicts(self):
        """Test multi-document conflict detection."""
        # Enter document mode
        self.manager.enter_document_mode(self.mock_documents)
        
        # Create search results for multiple documents with decent confidence
        # Need to use chunks from different documents and higher scores
        # Since confidence calculation uses weighted average (score * 0.5 for single result)
        # we need scores > 1.0 to get confidence > 0.5, so let's use multiple chunks
        chunk_doc2_1 = Chunk(
            content="Test chunk content from doc2",
            chunk_index=0,
            source_document_id="doc2",
            chunk_id="chunk_doc2_1",
            metadata={"filename": "test2.pdf"}
        )
        chunk_doc2_2 = Chunk(
            content="Another test chunk from doc2",
            chunk_index=1,
            source_document_id="doc2",
            chunk_id="chunk_doc2_2",
            metadata={"filename": "test2.pdf"}
        )
        
        search_results_by_document = {
            "doc1": SearchResult(
                chunks=self.mock_chunks,  # 2 chunks
                scores=[0.9, 0.8],  # High scores: 0.9*0.5 + 0.8*0.3 = 0.69 > 0.5
                query=SearchQuery(query_text="test query", k=5, min_score=0.0, filters={})
            ),
            "doc2": SearchResult(
                chunks=[chunk_doc2_1, chunk_doc2_2],  # 2 chunks
                scores=[0.85, 0.75],  # High scores: 0.85*0.5 + 0.75*0.3 = 0.65 > 0.5
                query=SearchQuery(query_text="test query", k=5, min_score=0.0, filters={})
            )
        }
        
        conflict = self.manager.detect_multi_document_conflicts(
            "test query", search_results_by_document
        )
        
        assert conflict is not None
        assert conflict.query == "test query"
        assert len(conflict.conflicting_documents) == 2
        assert "doc1" in conflict.confidence_scores
        assert "doc2" in conflict.confidence_scores
        assert self.manager.stats['conflicts_detected'] == 1
    
    def test_detect_multi_document_conflicts_no_conflict(self):
        """Test multi-document conflict detection with no conflicts."""
        # Enter document mode
        self.manager.enter_document_mode(self.mock_documents)
        
        # Create search results with only one document having decent confidence
        search_results_by_document = {
            "doc1": SearchResult(
                chunks=[self.mock_chunks[0]],
                scores=[0.8],
                query=SearchQuery(query_text="test query", k=5, min_score=0.0, filters={})
            ),
            "doc2": SearchResult(
                chunks=[self.mock_chunks[1]],
                scores=[0.3],  # Low confidence, won't be considered conflicting
                query=SearchQuery(query_text="test query", k=5, min_score=0.0, filters={})
            )
        }
        
        conflict = self.manager.detect_multi_document_conflicts(
            "test query", search_results_by_document
        )
        
        assert conflict is None
    
    def test_resolve_conflict(self):
        """Test conflict resolution."""
        # Enter document mode
        self.manager.enter_document_mode(self.mock_documents)
        
        confidence_scores = {"doc1": 0.8, "doc2": 0.7}
        
        resolution = self.manager.resolve_conflict(
            "test query", "doc1", confidence_scores
        )
        
        assert resolution.query == "test query"
        assert resolution.selected_document == "doc1"
        assert resolution.confidence_scores == confidence_scores
        
        # Check that resolution was added to session context
        resolutions = self.manager.current_session.conversation_context['conflict_resolutions']
        assert len(resolutions) == 1
        assert resolutions[0]['selected_document'] == "doc1"
    
    def test_update_document_chunks(self):
        """Test updating document chunk information."""
        # Enter document mode
        self.manager.enter_document_mode(self.mock_documents)
        
        # Update chunk information
        self.manager.update_document_chunks("doc1", 5, ["chunk1", "chunk2", "chunk3"])
        
        doc_info = self.manager.current_session.documents["doc1"]
        assert doc_info["chunk_count"] == 5
        assert doc_info["vector_ids"] == ["chunk1", "chunk2", "chunk3"]
    
    def test_remove_document(self):
        """Test removing a document from session."""
        # Enter document mode
        self.manager.enter_document_mode(self.mock_documents)
        
        # Remove one document
        success = self.manager.remove_document("doc1")
        
        assert success
        assert "doc1" not in self.manager.current_session.documents
        assert "doc2" in self.manager.current_session.documents
        assert self.manager.current_session.mode == ConversationMode.DOCUMENT
    
    def test_remove_last_document_exits_mode(self):
        """Test that removing the last document exits document mode."""
        # Enter document mode with one document
        self.manager.enter_document_mode([self.mock_documents[0]])
        
        # Remove the only document
        success = self.manager.remove_document("doc1")
        
        assert success
        assert self.manager.current_session.mode == ConversationMode.GENERAL
        assert len(self.manager.current_session.documents) == 0
    
    def test_remove_nonexistent_document(self):
        """Test removing a document that doesn't exist."""
        # Enter document mode
        self.manager.enter_document_mode(self.mock_documents)
        
        # Try to remove non-existent document
        success = self.manager.remove_document("nonexistent")
        
        assert not success
        assert len(self.manager.current_session.documents) == 2
    
    def test_get_session_status(self):
        """Test getting session status."""
        # Test without session
        status = self.manager.get_session_status()
        assert status['mode'] == 'general'
        assert not status['session_active']
        assert status['documents'] == []
        
        # Test with session
        self.manager.enter_document_mode(self.mock_documents)
        status = self.manager.get_session_status()
        
        assert status['mode'] == 'document'
        assert status['session_active']
        assert len(status['documents']) == 2
        assert status['session_id'] is not None
    
    def test_load_session_valid(self):
        """Test loading a valid session."""
        # Create a session first
        original_session = self.manager.create_session()
        session_data = original_session.to_dict()
        
        # Clear current session
        self.manager.current_session = None
        
        # Load the session
        success = self.manager.load_session(session_data)
        
        assert success
        assert self.manager.current_session is not None
        assert self.manager.current_session.session_id == original_session.session_id
    
    def test_load_session_expired(self):
        """Test loading an expired session."""
        # Create expired session data
        expired_time = datetime.now() - timedelta(hours=25)  # Expired
        session_data = {
            'mode': 'general',
            'session_id': 'test-session',
            'created_at': expired_time.isoformat(),
            'expires_at': expired_time.isoformat(),
            'documents': {},
            'conversation_context': {}
        }
        
        success = self.manager.load_session(session_data)
        
        assert not success
        assert self.manager.current_session is None
    
    def test_load_session_invalid_data(self):
        """Test loading invalid session data."""
        invalid_data = {"invalid": "data"}
        
        success = self.manager.load_session(invalid_data)
        
        assert not success
        assert self.manager.current_session is None
    
    def test_confidence_score_calculation(self):
        """Test confidence score calculation."""
        # Create additional chunk to match scores
        extra_chunk = Chunk(
            content="Test chunk content 3",
            chunk_index=2,
            source_document_id="doc1",
            chunk_id="chunk3",
            metadata={"filename": "test1.pdf"}
        )
        
        search_result = SearchResult(
            chunks=self.mock_chunks + [extra_chunk],
            scores=[0.9, 0.7, 0.5],  # Now matches chunk count
            query=SearchQuery(query_text="test", k=5, min_score=0.0, filters={})
        )
        
        confidence = self.manager._calculate_confidence_score(search_result)
        
        # Should be weighted average: 0.9*0.5 + 0.7*0.3 + 0.5*0.2 = 0.76
        expected = 0.9 * 0.5 + 0.7 * 0.3 + 0.5 * 0.2
        assert abs(confidence - expected) < 0.01
    
    def test_confidence_score_empty_result(self):
        """Test confidence score calculation with empty results."""
        search_result = SearchResult(
            chunks=[],
            scores=[],
            query=SearchQuery(query_text="test", k=5, min_score=0.0, filters={})
        )
        
        confidence = self.manager._calculate_confidence_score(search_result)
        assert confidence == 0.0
    
    def test_confidence_smoothing(self):
        """Test confidence score smoothing."""
        # Add some scores to history
        scores = [0.8, 0.7, 0.6, 0.9]
        
        for score in scores:
            smoothed = self.manager._apply_confidence_smoothing(score)
        
        # The smoothed score should be influenced by recent history
        assert 0.6 < smoothed < 0.9
        assert len(self.manager.confidence_history) == 4
    
    def test_context_aware_threshold_adjustment(self):
        """Test context-aware threshold adjustment."""
        base_threshold = self.manager.confidence_threshold
        
        # Specific question should lower threshold
        specific_threshold = self.manager._get_context_aware_threshold("How does this work?")
        assert specific_threshold < base_threshold
        
        # General question should raise threshold
        general_threshold = self.manager._get_context_aware_threshold("Tell me about this")
        assert general_threshold > base_threshold
        
        # Long question should lower threshold
        long_question = "This is a very long and detailed question about how the system works and what it does"
        long_threshold = self.manager._get_context_aware_threshold(long_question)
        assert long_threshold < base_threshold
    
    def test_fallback_explanation_generation(self):
        """Test fallback explanation generation."""
        # Very low confidence
        explanation = self.manager._generate_fallback_explanation(0.2, 0.7)
        assert "couldn't find relevant information" in explanation
        
        # Medium confidence
        explanation = self.manager._generate_fallback_explanation(0.4, 0.7)
        assert "doesn't seem to directly address" in explanation
        
        # Just below threshold
        explanation = self.manager._generate_fallback_explanation(0.6, 0.7)
        assert "may not fully answer" in explanation
    
    def test_conflict_explanation_generation(self):
        """Test conflict explanation generation."""
        # Enter document mode to set up document names
        self.manager.enter_document_mode(self.mock_documents)
        
        confidence_scores = {"doc1": 0.8, "doc2": 0.7}
        explanation = self.manager._generate_conflict_explanation(confidence_scores)
        
        assert "test1.pdf" in explanation
        assert "test2.pdf" in explanation
        assert "0.80" in explanation
        assert "0.70" in explanation
    
    def test_get_stats(self):
        """Test getting manager statistics."""
        # Initial stats
        stats = self.manager.get_stats()
        assert stats['sessions_created'] == 0
        assert stats['current_mode'] == 'general'
        assert stats['active_documents'] == 0
        
        # After creating session and entering document mode
        self.manager.enter_document_mode(self.mock_documents)
        stats = self.manager.get_stats()
        
        assert stats['sessions_created'] == 1
        assert stats['current_mode'] == 'document'
        assert stats['active_documents'] == 2
        assert stats['documents_added'] == 2
        assert stats['mode_switches'] == 1
    
    def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions."""
        # Create session
        session = self.manager.create_session()
        
        # Manually expire it
        expired_time = datetime.now() - timedelta(hours=1)
        session.expires_at = expired_time.isoformat()
        
        # Cleanup should remove the session
        was_expired = self.manager.cleanup_expired_sessions()
        
        assert was_expired
        assert self.manager.current_session is None
    
    def test_cleanup_valid_sessions(self):
        """Test cleanup with valid sessions."""
        # Create session (should not be expired)
        self.manager.create_session()
        
        # Cleanup should not remove valid session
        was_expired = self.manager.cleanup_expired_sessions()
        
        assert not was_expired
        assert self.manager.current_session is not None


class TestDocumentModeSession:
    """Test cases for DocumentModeSession."""
    
    def test_session_to_dict(self):
        """Test converting session to dictionary."""
        session = DocumentModeSession(
            mode=ConversationMode.DOCUMENT,
            session_id="test-session",
            created_at="2023-01-01T00:00:00",
            expires_at="2023-01-02T00:00:00",
            documents={"doc1": {"name": "test.pdf"}},
            conversation_context={"test": "data"}
        )
        
        data = session.to_dict()
        
        assert data['mode'] == 'document'
        assert data['session_id'] == 'test-session'
        assert data['documents'] == {"doc1": {"name": "test.pdf"}}
        assert data['conversation_context'] == {"test": "data"}
    
    def test_session_from_dict(self):
        """Test creating session from dictionary."""
        data = {
            'mode': 'document',
            'session_id': 'test-session',
            'created_at': '2023-01-01T00:00:00',
            'expires_at': '2023-01-02T00:00:00',
            'documents': {"doc1": {"name": "test.pdf"}},
            'conversation_context': {"test": "data"}
        }
        
        session = DocumentModeSession.from_dict(data)
        
        assert session.mode == ConversationMode.DOCUMENT
        assert session.session_id == 'test-session'
        assert session.documents == {"doc1": {"name": "test.pdf"}}
        assert session.conversation_context == {"test": "data"}


# Integration tests with RAG service would go here
# These would test the full conversation mode workflow
class TestConversationModeIntegration:
    """Integration tests for conversation mode with RAG service."""
    
    @pytest.mark.asyncio
    async def test_conversation_mode_workflow(self):
        """Test complete conversation mode workflow."""
        # This would be an integration test that:
        # 1. Creates a RAG service
        # 2. Processes documents
        # 3. Enters document mode
        # 4. Tests queries with fallback
        # 5. Tests conflict detection
        # 6. Tests conflict resolution
        # 7. Exits document mode
        
        # For now, this is a placeholder for future integration testing
        pass


if __name__ == "__main__":
    pytest.main([__file__])
