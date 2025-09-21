"""
Conversation Mode Manager for handling document mode state and fallback logic.

This module provides the ConversationModeManager class that manages the state
between document mode and general mode, handles confidence scoring, fallback
detection, and multi-document conflict resolution.
"""

from typing import List, Optional, Dict, Any, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
from dataclasses import dataclass, asdict

from ..models import Document, Chunk, SearchResult


class ConversationMode(Enum):
    """Conversation mode enumeration."""
    GENERAL = "general"
    DOCUMENT = "document"


@dataclass
class ConflictResolution:
    """Represents a user's resolution of a multi-document conflict."""
    query: str
    selected_document: str
    timestamp: str
    confidence_scores: Dict[str, float]


@dataclass
class DocumentModeSession:
    """Session data for document mode management."""
    mode: ConversationMode
    session_id: str
    created_at: str
    expires_at: str
    documents: Dict[str, Dict[str, Any]]
    conversation_context: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'mode': self.mode.value,
            'session_id': self.session_id,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'documents': self.documents,
            'conversation_context': self.conversation_context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentModeSession':
        """Create from dictionary."""
        return cls(
            mode=ConversationMode(data['mode']),
            session_id=data['session_id'],
            created_at=data['created_at'],
            expires_at=data['expires_at'],
            documents=data['documents'],
            conversation_context=data['conversation_context']
        )


@dataclass
class FallbackRequest:
    """Represents a request for fallback to general knowledge."""
    query: str
    confidence_score: float
    retrieved_chunks: List[Chunk]
    explanation: str
    timestamp: str


@dataclass
class ConflictDetection:
    """Represents detected conflicts between multiple documents."""
    query: str
    conflicting_documents: Dict[str, List[Chunk]]
    confidence_scores: Dict[str, float]
    explanation: str


class ConversationModeManager:
    """
    Manages conversation mode state, fallback logic, and multi-document conflicts.
    
    This class handles:
    - Session-based document mode management
    - Confidence scoring and threshold management
    - Fallback detection and user confirmation workflow
    - Multi-document conflict resolution
    - Session persistence and recovery
    """
    
    def __init__(
        self,
        confidence_threshold: float = 0.7,
        session_duration_hours: int = 24,
        max_documents_per_session: int = 10,
        smoothing_factor: float = 0.3
    ):
        """
        Initialize the conversation mode manager.
        
        Args:
            confidence_threshold: Default confidence threshold for fallback
            session_duration_hours: Session expiration time in hours
            max_documents_per_session: Maximum documents per session
            smoothing_factor: Factor for confidence score smoothing
        """
        self.confidence_threshold = confidence_threshold
        self.session_duration_hours = session_duration_hours
        self.max_documents_per_session = max_documents_per_session
        self.smoothing_factor = smoothing_factor
        
        # Current session state
        self.current_session: Optional[DocumentModeSession] = None
        
        # Confidence score history for smoothing
        self.confidence_history: List[float] = []
        
        # Statistics
        self.stats = {
            'sessions_created': 0,
            'documents_added': 0,
            'fallback_requests': 0,
            'conflicts_detected': 0,
            'mode_switches': 0,
            'last_activity': None
        }
    
    def create_session(self) -> DocumentModeSession:
        """
        Create a new document mode session.
        
        Returns:
            New DocumentModeSession
        """
        now = datetime.now()
        expires_at = now + timedelta(hours=self.session_duration_hours)
        
        session = DocumentModeSession(
            mode=ConversationMode.GENERAL,
            session_id=str(uuid.uuid4()),
            created_at=now.isoformat(),
            expires_at=expires_at.isoformat(),
            documents={},
            conversation_context={
                'last_document_query': '',
                'last_confidence_score': 0.0,
                'fallback_history': [],
                'conflict_resolutions': []
            }
        )
        
        self.current_session = session
        self.stats['sessions_created'] += 1
        self.stats['last_activity'] = now.isoformat()
        
        return session
    
    def load_session(self, session_data: Dict[str, Any]) -> bool:
        """
        Load an existing session from stored data.
        
        Args:
            session_data: Session data dictionary
            
        Returns:
            True if session loaded successfully, False if expired/invalid
        """
        try:
            session = DocumentModeSession.from_dict(session_data)
            
            # Check if session is expired
            expires_at = datetime.fromisoformat(session.expires_at)
            if datetime.now() > expires_at:
                return False
            
            self.current_session = session
            return True
            
        except Exception:
            return False
    
    def enter_document_mode(self, documents: List[Document]) -> DocumentModeSession:
        """
        Enter document mode with the provided documents.
        
        Args:
            documents: List of documents to activate
            
        Returns:
            Updated session
            
        Raises:
            ValueError: If too many documents or session issues
        """
        if len(documents) > self.max_documents_per_session:
            raise ValueError(f"Too many documents. Maximum: {self.max_documents_per_session}")
        
        if not self.current_session:
            self.create_session()
        
        # Add documents to session
        for doc in documents:
            doc_info = {
                'name': doc.metadata.get('filename', 'unknown'),
                'size': len(doc.content),
                'upload_time': datetime.now().isoformat(),
                'chunk_count': 0,  # Will be updated when chunks are processed
                'vector_ids': [],  # Will be updated when stored in vector DB
                'confidence_history': []
            }
            self.current_session.documents[doc.document_id] = doc_info
        
        # Switch to document mode
        self.current_session.mode = ConversationMode.DOCUMENT
        
        self.stats['documents_added'] += len(documents)
        self.stats['mode_switches'] += 1
        self.stats['last_activity'] = datetime.now().isoformat()
        
        return self.current_session
    
    def exit_document_mode(self) -> DocumentModeSession:
        """
        Exit document mode and return to general mode.
        
        Returns:
            Updated session
        """
        if self.current_session:
            self.current_session.mode = ConversationMode.GENERAL
            self.current_session.documents.clear()
            self.current_session.conversation_context = {
                'last_document_query': '',
                'last_confidence_score': 0.0,
                'fallback_history': [],
                'conflict_resolutions': []
            }
            
            self.stats['mode_switches'] += 1
            self.stats['last_activity'] = datetime.now().isoformat()
        
        return self.current_session
    
    def query_with_fallback(
        self,
        query: str,
        search_result: SearchResult,
        context_aware_threshold: Optional[float] = None
    ) -> Tuple[bool, Optional[FallbackRequest]]:
        """
        Analyze search results and determine if fallback is needed.
        
        Args:
            query: User's query
            search_result: Results from vector search
            context_aware_threshold: Optional custom threshold for this query
            
        Returns:
            Tuple of (needs_fallback, fallback_request)
        """
        if not self.current_session or self.current_session.mode != ConversationMode.DOCUMENT:
            return False, None
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(search_result)
        
        # Apply smoothing
        smoothed_confidence = self._apply_confidence_smoothing(confidence_score)
        
        # Determine threshold (context-aware or default)
        threshold = context_aware_threshold or self._get_context_aware_threshold(query)
        
        # Update session context
        self.current_session.conversation_context['last_document_query'] = query
        self.current_session.conversation_context['last_confidence_score'] = smoothed_confidence
        
        # Check if fallback is needed
        needs_fallback = smoothed_confidence < threshold
        
        if needs_fallback:
            fallback_request = FallbackRequest(
                query=query,
                confidence_score=smoothed_confidence,
                retrieved_chunks=search_result.chunks,
                explanation=self._generate_fallback_explanation(smoothed_confidence, threshold),
                timestamp=datetime.now().isoformat()
            )
            
            # Add to fallback history
            self.current_session.conversation_context['fallback_history'].append({
                'query': query,
                'confidence': smoothed_confidence,
                'timestamp': fallback_request.timestamp
            })
            
            self.stats['fallback_requests'] += 1
            self.stats['last_activity'] = datetime.now().isoformat()
            
            return True, fallback_request
        
        return False, None
    
    def detect_multi_document_conflicts(
        self,
        query: str,
        search_results_by_document: Dict[str, SearchResult]
    ) -> Optional[ConflictDetection]:
        """
        Detect conflicts between multiple documents for the same query.
        
        Args:
            query: User's query
            search_results_by_document: Search results grouped by document
            
        Returns:
            ConflictDetection if conflicts found, None otherwise
        """
        if len(search_results_by_document) < 2:
            return None
        
        # Calculate confidence scores for each document
        confidence_scores = {}
        conflicting_docs = {}
        
        for doc_id, search_result in search_results_by_document.items():
            confidence = self._calculate_confidence_score(search_result)
            confidence_scores[doc_id] = confidence
            
            # Consider it conflicting if confidence is above a lower threshold
            if confidence > 0.5:  # Lower threshold for conflict detection
                conflicting_docs[doc_id] = search_result.chunks
        
        # Check if we have actual conflicts (multiple docs with decent confidence)
        if len(conflicting_docs) > 1:
            conflict = ConflictDetection(
                query=query,
                conflicting_documents=conflicting_docs,
                confidence_scores=confidence_scores,
                explanation=self._generate_conflict_explanation(confidence_scores)
            )
            
            self.stats['conflicts_detected'] += 1
            self.stats['last_activity'] = datetime.now().isoformat()
            
            return conflict
        
        return None
    
    def resolve_conflict(
        self,
        query: str,
        selected_document_id: str,
        confidence_scores: Dict[str, float]
    ) -> ConflictResolution:
        """
        Record a user's resolution of a multi-document conflict.
        
        Args:
            query: The query that caused the conflict
            selected_document_id: Document ID the user selected
            confidence_scores: Confidence scores for all documents
            
        Returns:
            ConflictResolution record
        """
        resolution = ConflictResolution(
            query=query,
            selected_document=selected_document_id,
            timestamp=datetime.now().isoformat(),
            confidence_scores=confidence_scores
        )
        
        # Add to session context
        if self.current_session:
            self.current_session.conversation_context['conflict_resolutions'].append(
                asdict(resolution)
            )
        
        return resolution
    
    def update_document_chunks(self, document_id: str, chunk_count: int, vector_ids: List[str]) -> None:
        """
        Update document information after chunks are processed.
        
        Args:
            document_id: Document ID
            chunk_count: Number of chunks created
            vector_ids: List of vector database IDs
        """
        if (self.current_session and 
            document_id in self.current_session.documents):
            
            doc_info = self.current_session.documents[document_id]
            doc_info['chunk_count'] = chunk_count
            doc_info['vector_ids'] = vector_ids
    
    def remove_document(self, document_id: str) -> bool:
        """
        Remove a document from the current session.
        
        Args:
            document_id: Document ID to remove
            
        Returns:
            True if document was removed, False if not found
        """
        if (self.current_session and 
            document_id in self.current_session.documents):
            
            del self.current_session.documents[document_id]
            
            # If no documents left, exit document mode
            if not self.current_session.documents:
                self.exit_document_mode()
            
            return True
        
        return False
    
    def get_session_status(self) -> Dict[str, Any]:
        """
        Get current session status and information.
        
        Returns:
            Session status dictionary
        """
        if not self.current_session:
            return {
                'mode': ConversationMode.GENERAL.value,
                'session_active': False,
                'documents': [],
                'session_id': None
            }
        
        return {
            'mode': self.current_session.mode.value,
            'session_active': True,
            'session_id': self.current_session.session_id,
            'documents': [
                {
                    'id': doc_id,
                    'name': doc_info['name'],
                    'chunk_count': doc_info['chunk_count'],
                    'upload_time': doc_info['upload_time']
                }
                for doc_id, doc_info in self.current_session.documents.items()
            ],
            'expires_at': self.current_session.expires_at,
            'last_confidence_score': self.current_session.conversation_context.get('last_confidence_score', 0.0),
            'fallback_count': len(self.current_session.conversation_context.get('fallback_history', [])),
            'conflict_count': len(self.current_session.conversation_context.get('conflict_resolutions', []))
        }
    
    def _calculate_confidence_score(self, search_result: SearchResult) -> float:
        """
        Calculate confidence score based on search results.
        
        Args:
            search_result: Search results to analyze
            
        Returns:
            Confidence score between 0 and 1
        """
        if not search_result.chunks or not search_result.scores:
            return 0.0
        
        # Use weighted average of top scores
        scores = search_result.scores[:3]  # Top 3 results
        weights = [0.5, 0.3, 0.2]  # Decreasing weights
        
        weighted_score = sum(
            score * weight 
            for score, weight in zip(scores, weights[:len(scores)])
        )
        
        # Normalize to 0-1 range (assuming scores are similarity scores 0-1)
        return min(1.0, max(0.0, weighted_score))
    
    def _apply_confidence_smoothing(self, current_score: float) -> float:
        """
        Apply smoothing to confidence scores to avoid flip-flopping.
        
        Args:
            current_score: Current confidence score
            
        Returns:
            Smoothed confidence score
        """
        self.confidence_history.append(current_score)
        
        # Keep only recent history (last 5 scores)
        if len(self.confidence_history) > 5:
            self.confidence_history = self.confidence_history[-5:]
        
        # Apply exponential smoothing
        if len(self.confidence_history) == 1:
            return current_score
        
        # Weighted average with more weight on recent scores
        weights = [0.4, 0.3, 0.2, 0.1]  # Most recent to oldest
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for i, score in enumerate(reversed(self.confidence_history)):
            if i < len(weights):
                weighted_sum += score * weights[i]
                weight_sum += weights[i]
        
        return weighted_sum / weight_sum if weight_sum > 0 else current_score
    
    def _get_context_aware_threshold(self, query: str) -> float:
        """
        Get context-aware confidence threshold based on query characteristics.
        
        Args:
            query: User's query
            
        Returns:
            Adjusted confidence threshold
        """
        base_threshold = self.confidence_threshold
        
        # Adjust threshold based on query characteristics
        query_lower = query.lower()
        
        # Lower threshold for specific/detailed questions
        specific_indicators = ['how', 'what', 'when', 'where', 'why', 'which', 'specific', 'detail']
        if any(indicator in query_lower for indicator in specific_indicators):
            base_threshold -= 0.1
        
        # Higher threshold for general/broad questions
        general_indicators = ['general', 'overall', 'summary', 'about', 'tell me']
        if any(indicator in query_lower for indicator in general_indicators):
            base_threshold += 0.1
        
        # Adjust for question length (longer questions often more specific)
        if len(query.split()) > 10:
            base_threshold -= 0.05
        elif len(query.split()) < 5:
            base_threshold += 0.05
        
        # Ensure threshold stays within reasonable bounds
        return max(0.3, min(0.9, base_threshold))
    
    def _generate_fallback_explanation(self, confidence_score: float, threshold: float) -> str:
        """
        Generate explanation for why fallback is needed.
        
        Args:
            confidence_score: Calculated confidence score
            threshold: Threshold that wasn't met
            
        Returns:
            Human-readable explanation
        """
        if confidence_score < 0.3:
            return "I couldn't find relevant information in your uploaded documents for this question."
        elif confidence_score < 0.5:
            return "The information in your documents doesn't seem to directly address this question."
        elif confidence_score < threshold:
            return "I found some related content in your documents, but it may not fully answer your question."
        else:
            return "The confidence score was below the threshold for this type of query."
    
    def _generate_conflict_explanation(self, confidence_scores: Dict[str, float]) -> str:
        """
        Generate explanation for detected conflicts between documents.
        
        Args:
            confidence_scores: Confidence scores for each document
            
        Returns:
            Human-readable explanation
        """
        sorted_docs = sorted(confidence_scores.items(), key=lambda x: x[1], reverse=True)
        top_docs = sorted_docs[:2]
        
        if len(top_docs) >= 2:
            doc1_name = self._get_document_name(top_docs[0][0])
            doc2_name = self._get_document_name(top_docs[1][0])
            
            return (f"I found relevant information in multiple documents: "
                   f"{doc1_name} (confidence: {top_docs[0][1]:.2f}) and "
                   f"{doc2_name} (confidence: {top_docs[1][1]:.2f}). "
                   f"Which document would you like me to prioritize?")
        
        return "Multiple documents contain relevant information for your query."
    
    def _get_document_name(self, document_id: str) -> str:
        """
        Get display name for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document display name
        """
        if (self.current_session and 
            document_id in self.current_session.documents):
            return self.current_session.documents[document_id]['name']
        return f"Document {document_id[:8]}..."
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get conversation mode manager statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            **self.stats,
            'current_mode': self.current_session.mode.value if self.current_session else 'general',
            'active_documents': len(self.current_session.documents) if self.current_session else 0,
            'session_active': self.current_session is not None,
            'confidence_threshold': self.confidence_threshold,
            'max_documents_per_session': self.max_documents_per_session
        }
    
    def cleanup_expired_sessions(self) -> bool:
        """
        Clean up expired sessions.
        
        Returns:
            True if current session was expired and cleaned up
        """
        if not self.current_session:
            return False
        
        expires_at = datetime.fromisoformat(self.current_session.expires_at)
        if datetime.now() > expires_at:
            self.current_session = None
            return True
        
        return False
