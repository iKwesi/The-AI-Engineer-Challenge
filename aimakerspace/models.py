"""
Domain models for the aimakerspace library.

This module contains the core data structures used throughout the aimakerspace
library for document processing, text chunking, and RAG operations.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path
from enum import Enum


class DocumentType(Enum):
    """Enumeration of supported document types."""
    TEXT = "text"
    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    YOUTUBE = "youtube"


class ProcessingStatus(Enum):
    """Enumeration of document processing statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Document:
    """
    Represents a document with its content and metadata.
    
    This is the core document model used throughout the aimakerspace library.
    """
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_path: Optional[Path] = None
    document_type: DocumentType = DocumentType.TEXT
    document_id: Optional[str] = None
    
    def get_word_count(self) -> int:
        """Return the word count of the document content."""
        return len(self.content.split())
    
    def is_empty(self) -> bool:
        """Check if the document content is empty."""
        return not self.content.strip()
    
    def get_char_count(self) -> int:
        """Return the character count of the document content."""
        return len(self.content)


@dataclass
class Chunk:
    """
    Represents a text chunk with its metadata and optional embedding.
    
    Used for storing processed text chunks in the vector database.
    """
    content: str
    chunk_index: int
    source_document_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    
    def get_word_count(self) -> int:
        """Return the word count of the chunk content."""
        return len(self.content.split())
    
    def get_char_count(self) -> int:
        """Return the character count of the chunk content."""
        return len(self.content)


@dataclass
class ProcessedDocument:
    """
    Represents a document that has been processed into chunks.
    
    Contains the original document and its resulting chunks.
    """
    original_document: Document
    chunks: List[Chunk]
    processing_metadata: Dict[str, Any] = field(default_factory=dict)
    status: ProcessingStatus = ProcessingStatus.COMPLETED
    
    def get_total_chunks(self) -> int:
        """Return the total number of chunks."""
        return len(self.chunks)
    
    def get_total_words(self) -> int:
        """Return the total word count across all chunks."""
        return sum(chunk.get_word_count() for chunk in self.chunks)


@dataclass
class YouTubeVideo:
    """
    Represents a YouTube video with its metadata and transcript.
    
    Used specifically for YouTube video processing.
    """
    video_id: str
    title: str
    duration: int  # in seconds
    channel: str
    transcript: str
    url: str
    language: str = "en"
    view_count: Optional[int] = None
    upload_date: Optional[str] = None
    
    def get_duration_formatted(self) -> str:
        """Return formatted duration as MM:SS or HH:MM:SS."""
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"


@dataclass
class SearchQuery:
    """
    Represents a search query for the vector database.
    
    Used for RAG retrieval operations.
    """
    query_text: str
    k: int = 5  # number of results to return
    filters: Dict[str, Any] = field(default_factory=dict)
    min_score: float = 0.0
    
    def __post_init__(self):
        """Validate query parameters."""
        if self.k <= 0:
            raise ValueError("k must be positive")
        if self.min_score < 0.0 or self.min_score > 1.0:
            raise ValueError("min_score must be between 0.0 and 1.0")


@dataclass
class SearchResult:
    """
    Represents the result of a vector database search.
    
    Contains the retrieved chunks and their similarity scores.
    """
    chunks: List[Chunk]
    scores: List[float]
    query: SearchQuery
    total_results: int = 0
    
    def __post_init__(self):
        """Validate search result consistency."""
        if len(self.chunks) != len(self.scores):
            raise ValueError("Number of chunks must match number of scores")
        self.total_results = len(self.chunks)
    
    def get_top_chunk(self) -> Optional[Chunk]:
        """Return the highest scoring chunk, if any."""
        return self.chunks[0] if self.chunks else None
    
    def get_combined_content(self, separator: str = "\n\n") -> str:
        """Return all chunk contents combined with the specified separator."""
        return separator.join(chunk.content for chunk in self.chunks)


@dataclass
class ChunkingConfig:
    """
    Configuration for text chunking operations.
    
    Defines how documents should be split into chunks.
    """
    chunk_size: int = 1000
    overlap: int = 200
    preserve_sentences: bool = True
    min_chunk_size: int = 100
    
    def __post_init__(self):
        """Validate chunking configuration."""
        if self.chunk_size <= self.overlap:
            raise ValueError("Chunk size must be greater than overlap")
        if self.min_chunk_size <= 0:
            raise ValueError("Minimum chunk size must be positive")
        if self.overlap < 0:
            raise ValueError("Overlap cannot be negative")


@dataclass
class ProcessingLimits:
    """
    Configuration for processing limits and constraints.
    
    Defines system limits for document processing.
    """
    max_file_size_mb: int = 50
    max_chunks_per_document: int = 500
    max_documents_per_session: int = 100
    supported_formats: List[str] = field(default_factory=lambda: [
        ".txt", ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".csv"
    ])
    
    def get_max_file_size_bytes(self) -> int:
        """Return maximum file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024
    
    def is_format_supported(self, file_extension: str) -> bool:
        """Check if a file format is supported."""
        return file_extension.lower() in self.supported_formats


# Custom exceptions for the aimakerspace library
class AimakerspaceError(Exception):
    """Base exception for aimakerspace library errors."""
    pass


class DocumentProcessingError(AimakerspaceError):
    """Raised when document processing fails."""
    pass


class FileTooLargeError(DocumentProcessingError):
    """Raised when a file exceeds size limits."""
    pass


class UnsupportedFileTypeError(DocumentProcessingError):
    """Raised when a file type is not supported."""
    pass


class YouTubeProcessingError(DocumentProcessingError):
    """Raised when YouTube video processing fails."""
    pass


class VectorDatabaseError(AimakerspaceError):
    """Raised when vector database operations fail."""
    pass


class EmbeddingError(AimakerspaceError):
    """Raised when embedding generation fails."""
    pass
