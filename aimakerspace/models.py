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
    Enhanced with page-aware metadata for precise source attribution.
    """
    content: str
    chunk_index: int
    source_document_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    
    # Enhanced page-aware fields
    chunk_id: Optional[str] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    section_title: Optional[str] = None
    section_level: Optional[int] = None
    
    def get_word_count(self) -> int:
        """Return the word count of the chunk content."""
        return len(self.content.split())
    
    def get_char_count(self) -> int:
        """Return the character count of the chunk content."""
        return len(self.content)
    
    def get_page_range(self) -> str:
        """Return human-readable page range."""
        if self.page_start is None:
            return "Unknown"
        if self.page_end is None or self.page_start == self.page_end:
            return str(self.page_start)
        return f"{self.page_start}-{self.page_end}"
    
    def get_citation_text(self, include_section: bool = True) -> str:
        """Generate citation text for RAG responses."""
        filename = self.metadata.get("filename", "document")
        page_range = self.get_page_range()
        
        if include_section and self.section_title:
            return f"section {self.section_title} of {filename} (page {page_range})"
        else:
            return f"{filename} (page {page_range})"
    
    def get_source_url(self) -> Optional[str]:
        """Get direct URL to source with page anchor."""
        base_url = self.metadata.get("source_url")
        if base_url and self.page_start:
            return f"{base_url}#page={self.page_start}"
        return base_url


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
class PageData:
    """
    Represents a single page from a document with position tracking.
    
    Used for page-aware chunking and character position mapping.
    """
    page_number: int
    text: str
    start_char_global: int
    end_char_global: int
    word_count: int = field(init=False)
    char_count: int = field(init=False)
    
    def __post_init__(self):
        """Calculate derived fields."""
        self.word_count = len(self.text.split())
        self.char_count = len(self.text)
    
    def get_char_range(self) -> tuple[int, int]:
        """Return the global character range for this page."""
        return (self.start_char_global, self.end_char_global)


@dataclass
class SectionData:
    """
    Represents a document section with hierarchical information.
    
    Used for semantic chunking and rich source attribution.
    """
    title: str
    level: int  # 1=chapter, 2=section, 3=subsection, etc.
    page_start: int
    page_end: Optional[int] = None
    start_char_global: int = 0
    end_char_global: Optional[int] = None
    section_number: Optional[str] = None  # e.g., "4.1", "3.2.1"
    parent_section: Optional[str] = None
    
    def get_page_range(self) -> str:
        """Return human-readable page range for this section."""
        if self.page_end is None or self.page_start == self.page_end:
            return str(self.page_start)
        return f"{self.page_start}-{self.page_end}"
    
    def get_full_title(self) -> str:
        """Return full section title with number if available."""
        if self.section_number:
            return f"{self.section_number} {self.title}"
        return self.title


@dataclass
class DocumentStructure:
    """
    Represents the hierarchical structure of a document.
    
    Contains pages and sections for enhanced processing.
    """
    pages: List[PageData]
    sections: List[SectionData] = field(default_factory=list)
    total_pages: int = field(init=False)
    total_chars: int = field(init=False)
    
    def __post_init__(self):
        """Calculate derived fields."""
        self.total_pages = len(self.pages)
        self.total_chars = sum(page.char_count for page in self.pages)
    
    def get_page_by_number(self, page_number: int) -> Optional[PageData]:
        """Get page data by page number."""
        for page in self.pages:
            if page.page_number == page_number:
                return page
        return None
    
    def get_section_for_page(self, page_number: int) -> Optional[SectionData]:
        """Get the section that contains the given page."""
        for section in self.sections:
            if section.page_start <= page_number <= (section.page_end or section.page_start):
                return section
        return None
    
    def get_char_to_page_mapping(self) -> Dict[int, int]:
        """Create a mapping from character position to page number."""
        char_to_page = {}
        for page in self.pages:
            for char_pos in range(page.start_char_global, page.end_char_global + 1):
                char_to_page[char_pos] = page.page_number
        return char_to_page


@dataclass
class ChunkingConfig:
    """
    Configuration for text chunking operations.
    
    Defines how documents should be split into chunks.
    Enhanced with page-aware chunking options.
    """
    chunk_size: int = 1000
    overlap: int = 200
    preserve_sentences: bool = True
    min_chunk_size: int = 100
    page_aware: bool = True  # Enable page-aware chunking
    respect_section_boundaries: bool = True  # Don't split across sections
    include_page_context: bool = True  # Include page metadata in chunks
    
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


class PasswordProtectedFileError(DocumentProcessingError):
    """Raised when a file is password-protected and no password is provided."""
    pass


class InvalidPasswordError(DocumentProcessingError):
    """Raised when the provided password is incorrect."""
    pass


class VectorDatabaseError(AimakerspaceError):
    """Raised when vector database operations fail."""
    pass


class EmbeddingError(AimakerspaceError):
    """Raised when embedding generation fails."""
    pass
