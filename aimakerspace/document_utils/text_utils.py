"""
Text file loading utilities.

This module provides utilities for loading plain text files (.txt) with enhanced
error handling, encoding detection, and metadata extraction.
"""

from pathlib import Path
from typing import List, Union, Optional, Iterable
import chardet

from .base import FileBasedLoader
from ..models import Document, DocumentType, DocumentProcessingError


class TextFileLoader(FileBasedLoader):
    """
    Load plain-text documents from a single file or an entire directory.
    
    Enhanced version of the original TextFileLoader with better encoding handling,
    error recovery, and metadata extraction.
    """

    def __init__(self, path: Union[str, Path], encoding: str = "utf-8", auto_detect_encoding: bool = True):
        """
        Initialize the text file loader.
        
        Args:
            path: Path to file or directory
            encoding: Default encoding to use for text files
            auto_detect_encoding: Whether to auto-detect encoding if default fails
        """
        super().__init__(path)
        self.encoding = encoding
        self.auto_detect_encoding = auto_detect_encoding

    def can_load(self, source: Union[Path, str]) -> bool:
        """
        Check if this loader can handle the given source.
        
        Args:
            source: File path to check
            
        Returns:
            True if the source is a .txt file or directory, False otherwise
        """
        path = Path(source)
        if path.is_dir():
            return True
        return path.suffix.lower() == ".txt"

    def load_documents(self, source: Union[Path, str]) -> List[Document]:
        """
        Load documents from the given source.
        
        Args:
            source: File path or directory to load from
            
        Returns:
            List of loaded Document objects
            
        Raises:
            DocumentProcessingError: If loading fails
        """
        path = Path(source)
        
        if path.is_dir():
            return self._load_directory_documents(path)
        elif path.is_file() and path.suffix.lower() == ".txt":
            return [self._load_single_file(path)]
        else:
            raise DocumentProcessingError(
                f"Provided path must be a directory or a .txt file: {path}"
            )

    def _load_directory_documents(self, directory: Path) -> List[Document]:
        """
        Load all text files from a directory.
        
        Args:
            directory: Directory to load from
            
        Returns:
            List of Document objects
        """
        documents = []
        for file_path in self._iter_directory_files(directory):
            try:
                document = self._load_single_file(file_path)
                documents.append(document)
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")
                # Continue processing other files
        
        return documents

    def _load_single_file(self, file_path: Path) -> Document:
        """
        Load a single text file and return a Document object.
        
        Args:
            file_path: Path to the file to load
            
        Returns:
            A Document object containing the file content
            
        Raises:
            DocumentProcessingError: If the file cannot be loaded
        """
        # Validate file
        self.validate_file_size(file_path)
        self.validate_file_extension(file_path)
        
        try:
            content = self._read_text_file(file_path)
            
            # Create metadata
            metadata = {
                "encoding_used": self._get_file_encoding(file_path),
                "line_count": len(content.splitlines()),
            }
            
            return self.create_document(
                content=content,
                source_path=file_path,
                document_type=DocumentType.TEXT,
                metadata=metadata
            )
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to load text file {file_path}: {e}")

    def _iter_directory_files(self, directory: Path) -> Iterable[Path]:
        """
        Iterate over text files in a directory.
        
        Args:
            directory: Directory to iterate over
            
        Yields:
            Path objects for .txt files
        """
        for entry in sorted(directory.rglob("*.txt")):
            if entry.is_file():
                yield entry

    def _read_text_file(self, file_path: Path) -> str:
        """
        Read a text file with encoding detection and error handling.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            The file content as a string
            
        Raises:
            DocumentProcessingError: If the file cannot be read
        """
        # Try default encoding first
        try:
            with file_path.open("r", encoding=self.encoding) as file_handle:
                return file_handle.read()
        except UnicodeDecodeError:
            if not self.auto_detect_encoding:
                raise DocumentProcessingError(
                    f"Failed to decode {file_path} with encoding {self.encoding}"
                )
        
        # Try to detect encoding
        try:
            detected_encoding = self._detect_encoding(file_path)
            with file_path.open("r", encoding=detected_encoding) as file_handle:
                return file_handle.read()
        except Exception as e:
            raise DocumentProcessingError(
                f"Failed to read {file_path} with detected encoding: {e}"
            )

    def _detect_encoding(self, file_path: Path) -> str:
        """
        Detect the encoding of a text file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            The detected encoding name
            
        Raises:
            DocumentProcessingError: If encoding cannot be detected
        """
        try:
            with file_path.open("rb") as file_handle:
                raw_data = file_handle.read(10000)  # Read first 10KB for detection
                result = chardet.detect(raw_data)
                
                if result["encoding"] is None:
                    raise DocumentProcessingError(f"Could not detect encoding for {file_path}")
                
                return result["encoding"]
        except Exception as e:
            raise DocumentProcessingError(f"Encoding detection failed for {file_path}: {e}")

    def _get_file_encoding(self, file_path: Path) -> str:
        """
        Get the encoding that was successfully used to read a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            The encoding name that worked
        """
        # Try default encoding first
        try:
            with file_path.open("r", encoding=self.encoding) as file_handle:
                file_handle.read(100)  # Try to read a small amount
                return self.encoding
        except UnicodeDecodeError:
            if self.auto_detect_encoding:
                return self._detect_encoding(file_path)
            else:
                return self.encoding

    # Convenience methods for backward compatibility
    def load(self) -> None:
        """
        Populate self.documents from the configured path.
        
        This method maintains backward compatibility with the original TextFileLoader.
        """
        self.documents = self.load_documents(self.path)

    def load_file(self) -> None:
        """
        Load a single file specified by self.path.
        
        This method maintains backward compatibility with the original TextFileLoader.
        """
        super().load_file()

    def load_directory(self) -> None:
        """
        Load all text files contained within self.path.
        
        This method maintains backward compatibility with the original TextFileLoader.
        """
        super().load_directory()
