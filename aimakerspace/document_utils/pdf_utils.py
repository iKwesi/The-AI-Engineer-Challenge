"""
PDF file loading utilities.

This module provides utilities for loading PDF documents with enhanced
error handling, metadata extraction, and password protection support.
"""

from pathlib import Path
from typing import List, Union, Optional, Iterable
import PyPDF2

from .base import FileBasedLoader
from ..models import Document, DocumentType, DocumentProcessingError


class PDFLoader(FileBasedLoader):
    """
    Extract text from PDF files stored at a path.
    
    Enhanced version of the original PDFLoader with better error handling,
    metadata extraction, and password protection support.
    """

    def __init__(self, path: Union[str, Path], password: Optional[str] = None):
        """
        Initialize the PDF loader.
        
        Args:
            path: Path to PDF file or directory
            password: Optional password for encrypted PDFs
        """
        super().__init__(path)
        self.password = password

    def can_load(self, source: Union[Path, str]) -> bool:
        """
        Check if this loader can handle the given source.
        
        Args:
            source: File path to check
            
        Returns:
            True if the source is a .pdf file or directory, False otherwise
        """
        path = Path(source)
        if path.is_dir():
            return True
        return path.suffix.lower() == ".pdf"

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
        elif path.is_file() and path.suffix.lower() == ".pdf":
            return [self._load_single_file(path)]
        else:
            raise DocumentProcessingError(
                f"Provided path must be a directory or a .pdf file: {path}"
            )

    def _load_directory_documents(self, directory: Path) -> List[Document]:
        """
        Load all PDF files from a directory.
        
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
        Load a single PDF file and return a Document object.
        
        Args:
            file_path: Path to the file to load
            
        Returns:
            A Document object containing the PDF content
            
        Raises:
            DocumentProcessingError: If the PDF cannot be loaded
        """
        # Validate file
        self.validate_file_size(file_path)
        self.validate_file_extension(file_path)
        
        try:
            content, pdf_metadata = self._read_pdf(file_path)
            
            # Combine PDF metadata with standard metadata
            metadata = {
                "page_count": pdf_metadata.get("page_count", 0),
                "pdf_title": pdf_metadata.get("title", ""),
                "pdf_author": pdf_metadata.get("author", ""),
                "pdf_subject": pdf_metadata.get("subject", ""),
                "pdf_creator": pdf_metadata.get("creator", ""),
                "pdf_producer": pdf_metadata.get("producer", ""),
                "creation_date": pdf_metadata.get("creation_date", ""),
                "modification_date": pdf_metadata.get("modification_date", ""),
                "is_encrypted": pdf_metadata.get("is_encrypted", False),
            }
            
            return self.create_document(
                content=content,
                source_path=file_path,
                document_type=DocumentType.PDF,
                metadata=metadata
            )
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to load PDF file {file_path}: {e}")

    def _iter_directory_files(self, directory: Path) -> Iterable[Path]:
        """
        Iterate over PDF files in a directory.
        
        Args:
            directory: Directory to iterate over
            
        Yields:
            Path objects for .pdf files
        """
        for entry in sorted(directory.rglob("*.pdf")):
            if entry.is_file():
                yield entry

    def _read_pdf(self, file_path: Path) -> tuple[str, dict]:
        """
        Read a PDF file and extract text content and metadata.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            A tuple of (extracted_text, metadata_dict)
            
        Raises:
            DocumentProcessingError: If the PDF cannot be read
        """
        try:
            with file_path.open("rb") as file_handle:
                pdf_reader = PyPDF2.PdfReader(file_handle)
                
                # Handle encrypted PDFs
                if pdf_reader.is_encrypted:
                    if self.password:
                        try:
                            pdf_reader.decrypt(self.password)
                        except Exception as e:
                            raise DocumentProcessingError(
                                f"Failed to decrypt PDF {file_path} with provided password: {e}"
                            )
                    else:
                        raise DocumentProcessingError(
                            f"PDF {file_path} is encrypted but no password provided"
                        )
                
                # Extract text from all pages
                extracted_pages = []
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text() or ""
                        if page_text.strip():  # Only add non-empty pages
                            extracted_pages.append(f"[Page {page_num + 1}]\n{page_text}")
                    except Exception as e:
                        print(f"Warning: Failed to extract text from page {page_num + 1}: {e}")
                        # Continue with other pages
                
                content = "\n\n".join(extracted_pages)
                
                # Extract metadata
                metadata = self._extract_pdf_metadata(pdf_reader)
                metadata["page_count"] = len(pdf_reader.pages)
                metadata["is_encrypted"] = pdf_reader.is_encrypted
                
                return content, metadata
                
        except Exception as e:
            raise DocumentProcessingError(f"Failed to read PDF {file_path}: {e}")

    def _extract_pdf_metadata(self, pdf_reader: PyPDF2.PdfReader) -> dict:
        """
        Extract metadata from a PDF reader object.
        
        Args:
            pdf_reader: PyPDF2 PdfReader object
            
        Returns:
            Dictionary containing PDF metadata
        """
        metadata = {}
        
        try:
            if pdf_reader.metadata:
                # Extract common metadata fields
                metadata_fields = {
                    "title": "/Title",
                    "author": "/Author", 
                    "subject": "/Subject",
                    "creator": "/Creator",
                    "producer": "/Producer",
                    "creation_date": "/CreationDate",
                    "modification_date": "/ModDate",
                }
                
                for key, pdf_key in metadata_fields.items():
                    if pdf_key in pdf_reader.metadata:
                        value = pdf_reader.metadata[pdf_key]
                        # Convert to string and clean up
                        metadata[key] = str(value).strip() if value else ""
                        
        except Exception as e:
            print(f"Warning: Failed to extract PDF metadata: {e}")
            # Continue without metadata
        
        return metadata

    def set_password(self, password: str) -> None:
        """
        Set the password for encrypted PDFs.
        
        Args:
            password: Password to use for decryption
        """
        self.password = password

    # Convenience methods for backward compatibility
    def load(self) -> None:
        """
        Populate self.documents from the configured path.
        
        This method maintains backward compatibility with the original PDFLoader.
        """
        self.documents = self.load_documents(self.path)

    def load_file(self) -> None:
        """
        Load a single file specified by self.path.
        
        This method maintains backward compatibility with the original PDFLoader.
        """
        super().load_file()

    def load_directory(self) -> None:
        """
        Load all PDF files contained within self.path.
        
        This method maintains backward compatibility with the original PDFLoader.
        """
        super().load_directory()
