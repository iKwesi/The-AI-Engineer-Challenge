"""
Base classes for document loading utilities.

This module provides the abstract base class that all document loaders must implement,
ensuring a consistent interface across different document types.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Union, Optional
import uuid

from ..models import Document, DocumentType, ProcessingLimits, UnsupportedFileTypeError, FileTooLargeError


class DocumentLoader(ABC):
    """
    Abstract base class for all document loaders.
    
    This class defines the common interface that all document loaders must implement,
    ensuring consistency across different document types and sources.
    """
    
    def __init__(self, processing_limits: Optional[ProcessingLimits] = None):
        """
        Initialize the document loader.
        
        Args:
            processing_limits: Optional processing limits configuration
        """
        self.processing_limits = processing_limits or ProcessingLimits()
        self.documents: List[Document] = []
    
    @abstractmethod
    def can_load(self, source: Union[Path, str]) -> bool:
        """
        Check if this loader can handle the given source.
        
        Args:
            source: File path or URL to check
            
        Returns:
            True if this loader can handle the source, False otherwise
        """
        pass
    
    @abstractmethod
    def load_documents(self, source: Union[Path, str]) -> List[Document]:
        """
        Load documents from the given source.
        
        Args:
            source: File path or URL to load from
            
        Returns:
            List of loaded Document objects
            
        Raises:
            UnsupportedFileTypeError: If the file type is not supported
            FileTooLargeError: If the file exceeds size limits
            DocumentProcessingError: If processing fails
        """
        pass
    
    def validate_file_size(self, file_path: Path) -> None:
        """
        Validate that a file doesn't exceed size limits.
        
        Args:
            file_path: Path to the file to validate
            
        Raises:
            FileTooLargeError: If the file is too large
        """
        if file_path.exists():
            file_size = file_path.stat().st_size
            max_size = self.processing_limits.get_max_file_size_bytes()
            
            if file_size > max_size:
                raise FileTooLargeError(
                    f"File {file_path.name} ({file_size} bytes) exceeds maximum "
                    f"size limit of {max_size} bytes ({self.processing_limits.max_file_size_mb}MB)"
                )
    
    def validate_file_extension(self, file_path: Path) -> None:
        """
        Validate that a file extension is supported.
        
        Args:
            file_path: Path to the file to validate
            
        Raises:
            UnsupportedFileTypeError: If the file type is not supported
        """
        extension = file_path.suffix.lower()
        if not self.processing_limits.is_format_supported(extension):
            raise UnsupportedFileTypeError(
                f"File type '{extension}' is not supported. "
                f"Supported formats: {', '.join(self.processing_limits.supported_formats)}"
            )
    
    def generate_document_id(self) -> str:
        """
        Generate a unique document ID.
        
        Returns:
            A unique string identifier
        """
        return str(uuid.uuid4())
    
    def create_document(
        self, 
        content: str, 
        source_path: Optional[Path] = None,
        document_type: DocumentType = DocumentType.TEXT,
        metadata: Optional[dict] = None
    ) -> Document:
        """
        Create a Document object with standard metadata.
        
        Args:
            content: The document content
            source_path: Optional path to the source file
            document_type: Type of the document
            metadata: Additional metadata
            
        Returns:
            A Document object with populated metadata
        """
        doc_metadata = metadata or {}
        
        # Add standard metadata
        if source_path:
            doc_metadata.update({
                "filename": source_path.name,
                "file_extension": source_path.suffix.lower(),
                "file_size": source_path.stat().st_size if source_path.exists() else 0,
            })
        
        doc_metadata.update({
            "word_count": len(content.split()),
            "char_count": len(content),
            "loader_class": self.__class__.__name__,
        })
        
        return Document(
            content=content,
            metadata=doc_metadata,
            source_path=source_path,
            document_type=document_type,
            document_id=self.generate_document_id()
        )


class FileBasedLoader(DocumentLoader):
    """
    Base class for file-based document loaders.
    
    Provides common functionality for loaders that work with files on disk.
    """
    
    def __init__(self, path: Union[str, Path], processing_limits: Optional[ProcessingLimits] = None):
        """
        Initialize the file-based loader.
        
        Args:
            path: Path to file or directory
            processing_limits: Optional processing limits configuration
        """
        super().__init__(processing_limits)
        self.path = Path(path)
    
    def load(self) -> None:
        """
        Load documents from the configured path.
        
        Populates self.documents with loaded Document objects.
        """
        self.documents = self.load_documents(self.path)
    
    def load_file(self) -> None:
        """
        Load a single file specified by self.path.
        
        Raises:
            ValueError: If path is not a file
        """
        if not self.path.is_file():
            raise ValueError(f"Path {self.path} is not a file")
        
        self.documents = [self._load_single_file(self.path)]
    
    def load_directory(self) -> None:
        """
        Load all supported files from the directory specified by self.path.
        
        Raises:
            ValueError: If path is not a directory
        """
        if not self.path.is_dir():
            raise ValueError(f"Path {self.path} is not a directory")
        
        self.documents = []
        for file_path in self._iter_directory_files(self.path):
            try:
                document = self._load_single_file(file_path)
                self.documents.append(document)
            except Exception as e:
                # Log error but continue processing other files
                print(f"Warning: Failed to load {file_path}: {e}")
    
    @abstractmethod
    def _load_single_file(self, file_path: Path) -> Document:
        """
        Load a single file and return a Document object.
        
        Args:
            file_path: Path to the file to load
            
        Returns:
            A Document object containing the file content
        """
        pass
    
    @abstractmethod
    def _iter_directory_files(self, directory: Path):
        """
        Iterate over files in a directory that this loader can handle.
        
        Args:
            directory: Directory to iterate over
            
        Yields:
            Path objects for files that can be processed
        """
        pass
