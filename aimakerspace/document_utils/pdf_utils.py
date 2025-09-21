"""
PDF file loading utilities.

This module provides utilities for loading PDF documents with enhanced
error handling, metadata extraction, and password protection support.
"""

from pathlib import Path
from typing import List, Union, Optional, Iterable
import PyPDF2
import logging
from datetime import datetime

from .base import FileBasedLoader
from ..models import (
    Document, 
    DocumentType, 
    DocumentProcessingError,
    PasswordProtectedFileError,
    InvalidPasswordError,
    PageData,
    SectionData,
    DocumentStructure,
    ChunkingConfig,
    Chunk
)
from ..processing_utils.section_detector import SectionDetector
from ..processing_utils.page_aware_chunker import PageAwareChunker


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

    def check_encryption_status(self, file_path: Path) -> dict:
        """
        Check if a PDF is encrypted without attempting to read content.
        
        This method satisfies the "Detect protection upfront" requirement.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary with encryption status and metadata
            
        Raises:
            DocumentProcessingError: If the PDF cannot be opened
        """
        try:
            with file_path.open("rb") as file_handle:
                pdf_reader = PyPDF2.PdfReader(file_handle)
                
                encryption_info = {
                    "is_encrypted": pdf_reader.is_encrypted,
                    "filename": file_path.name,
                    "file_size": file_path.stat().st_size,
                    "page_count": len(pdf_reader.pages) if not pdf_reader.is_encrypted else None,
                    "requires_password": pdf_reader.is_encrypted,
                    "check_timestamp": datetime.now().isoformat(),
                }
                
                # Log the encryption check for audit purposes
                self._log_encryption_check(file_path, encryption_info)
                
                return encryption_info
                
        except Exception as e:
            raise DocumentProcessingError(f"Failed to check encryption status for {file_path}: {e}")

    def load_with_security_compliance(self, source: Union[Path, str], skip_protected: bool = True, validate_batch_size: bool = True) -> tuple[List[Document], List[dict]]:
        """
        Load documents with full security compliance.
        
        This method satisfies all security requirements:
        1. Detect protection upfront
        2. Handle securely if allowed
        3. Skip otherwise
        4. Validate cumulative file size limits
        
        Args:
            source: File path or directory to load from
            skip_protected: If True, skip password-protected files without password
            validate_batch_size: If True, validate total size of all files before processing
            
        Returns:
            Tuple of (loaded_documents, skipped_files_info)
            
        Raises:
            PasswordProtectedFileError: If a protected file is encountered and skip_protected=False
            FileTooLargeError: If batch size exceeds limits
        """
        path = Path(source)
        loaded_documents = []
        skipped_files = []
        
        if path.is_file():
            files_to_process = [path]
        elif path.is_dir():
            files_to_process = list(self._iter_directory_files(path))
        else:
            raise DocumentProcessingError(f"Invalid path: {path}")
        
        # Validate batch size before processing any files
        if validate_batch_size and files_to_process:
            try:
                self.validate_batch_size(files_to_process)
            except FileTooLargeError as e:
                # Add helpful context about which files are too large
                total_size_mb = sum(f.stat().st_size for f in files_to_process if f.exists()) / (1024 * 1024)
                max_size_mb = self.processing_limits.max_file_size_mb
                
                raise FileTooLargeError(
                    f"Batch upload rejected: {len(files_to_process)} PDFs totaling {total_size_mb:.1f}MB "
                    f"exceeds {max_size_mb}MB limit. Consider uploading fewer files or smaller files. "
                    f"Original error: {str(e)}"
                )
        
        for file_path in files_to_process:
            try:
                # Step 1: Detect protection upfront
                encryption_info = self.check_encryption_status(file_path)
                
                if encryption_info["is_encrypted"]:
                    if self.password:
                        # Step 2: Handle securely if allowed
                        try:
                            document = self._load_single_file_secure(file_path)
                            loaded_documents.append(document)
                            self._log_successful_decryption(file_path)
                        except InvalidPasswordError as e:
                            self._log_failed_decryption(file_path, str(e))
                            if skip_protected:
                                skipped_files.append({
                                    **encryption_info,
                                    "skip_reason": "Invalid password provided",
                                    "error": str(e)
                                })
                            else:
                                raise
                    else:
                        # Step 3: Skip otherwise
                        self._log_skipped_protected_file(file_path)
                        if skip_protected:
                            skipped_files.append({
                                **encryption_info,
                                "skip_reason": "No password provided for encrypted file",
                                "user_message": f"This file is protected. Please provide the password to unlock '{file_path.name}' before ingestion."
                            })
                        else:
                            raise PasswordProtectedFileError(
                                f"This file is protected. Please provide the password to unlock '{file_path.name}' before ingestion."
                            )
                else:
                    # Regular unencrypted file
                    document = self._load_single_file(file_path)
                    loaded_documents.append(document)
                    
            except (DocumentProcessingError, PasswordProtectedFileError, InvalidPasswordError):
                raise
            except Exception as e:
                error_info = {
                    "filename": file_path.name,
                    "skip_reason": f"Processing error: {str(e)}",
                    "error": str(e)
                }
                skipped_files.append(error_info)
                self._log_processing_error(file_path, str(e))
        
        return loaded_documents, skipped_files

    def _load_single_file_secure(self, file_path: Path) -> Document:
        """
        Load a single encrypted PDF file with security compliance.
        
        Args:
            file_path: Path to the encrypted PDF file
            
        Returns:
            A Document object with encrypted content handled securely
            
        Raises:
            InvalidPasswordError: If the password is incorrect
            DocumentProcessingError: If processing fails
        """
        try:
            with file_path.open("rb") as file_handle:
                pdf_reader = PyPDF2.PdfReader(file_handle)
                
                if pdf_reader.is_encrypted:
                    try:
                        # Attempt decryption
                        decrypt_result = pdf_reader.decrypt(self.password)
                        if not decrypt_result:
                            raise InvalidPasswordError(f"Incorrect password for PDF {file_path}")
                    except Exception as e:
                        if "password" in str(e).lower():
                            raise InvalidPasswordError(f"Invalid password for PDF {file_path}: {e}")
                        else:
                            raise DocumentProcessingError(f"Failed to decrypt PDF {file_path}: {e}")
                
                # Extract text (temporarily decrypted in memory)
                extracted_pages = []
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text() or ""
                        if page_text.strip():
                            extracted_pages.append(f"[Page {page_num + 1}]\n{page_text}")
                    except Exception as e:
                        print(f"Warning: Failed to extract text from page {page_num + 1}: {e}")
                
                content = "\n\n".join(extracted_pages)
                
                # Extract metadata
                metadata = self._extract_pdf_metadata(pdf_reader)
                metadata.update({
                    "page_count": len(pdf_reader.pages),
                    "is_encrypted": True,
                    "decryption_timestamp": datetime.now().isoformat(),
                    "security_handled": True,
                })
                
                # Create document with security metadata
                document = self.create_document(
                    content=content,
                    source_path=file_path,
                    document_type=DocumentType.PDF,
                    metadata=metadata
                )
                
                # Note: In a production system, you would encrypt the content at rest here
                # and implement proper key management
                
                return document
                
        except (InvalidPasswordError, DocumentProcessingError):
            raise
        except Exception as e:
            raise DocumentProcessingError(f"Failed to securely load PDF {file_path}: {e}")

    def _log_encryption_check(self, file_path: Path, encryption_info: dict) -> None:
        """Log encryption check for audit purposes."""
        logging.info(f"PDF encryption check: {file_path.name} - Encrypted: {encryption_info['is_encrypted']}")

    def _log_successful_decryption(self, file_path: Path) -> None:
        """Log successful decryption for audit purposes."""
        logging.info(f"PDF successfully decrypted: {file_path.name} at {datetime.now().isoformat()}")

    def _log_failed_decryption(self, file_path: Path, error: str) -> None:
        """Log failed decryption attempt for audit purposes."""
        logging.warning(f"PDF decryption failed: {file_path.name} - {error} at {datetime.now().isoformat()}")

    def _log_skipped_protected_file(self, file_path: Path) -> None:
        """Log when a protected file is skipped for audit purposes."""
        logging.info(f"PDF skipped (protected): {file_path.name} - No password provided at {datetime.now().isoformat()}")

    def _log_processing_error(self, file_path: Path, error: str) -> None:
        """Log processing errors for audit purposes."""
        logging.error(f"PDF processing error: {file_path.name} - {error} at {datetime.now().isoformat()}")

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

    # Enhanced page-aware processing methods
    def extract_document_structure(self, document: Document) -> DocumentStructure:
        """
        Extract page and section structure from a PDF document.
        
        Args:
            document: Document to analyze
            
        Returns:
            DocumentStructure with pages and detected sections
        """
        pages = self._extract_pages_with_positions(document)
        
        # Detect sections using the section detector
        section_detector = SectionDetector()
        sections = section_detector.detect_sections_in_pages(pages)
        
        return DocumentStructure(pages=pages, sections=sections)
    
    def _extract_pages_with_positions(self, document: Document) -> List[PageData]:
        """
        Extract individual pages with character position tracking.
        
        Args:
            document: Document to extract pages from
            
        Returns:
            List of PageData objects with position information
        """
        pages = []
        content = document.content
        
        # Split content by page markers
        page_sections = content.split('\n\n')
        char_position = 0
        
        for section in page_sections:
            if section.strip().startswith('[Page '):
                # Extract page number and content
                lines = section.split('\n', 1)
                if len(lines) >= 2:
                    page_header = lines[0]
                    page_content = lines[1] if len(lines) > 1 else ""
                    
                    # Extract page number from header like "[Page 5]"
                    import re
                    page_match = re.search(r'\[Page (\d+)\]', page_header)
                    if page_match:
                        page_number = int(page_match.group(1))
                        
                        start_char = char_position
                        end_char = char_position + len(page_content)
                        
                        page_data = PageData(
                            page_number=page_number,
                            text=page_content,
                            start_char_global=start_char,
                            end_char_global=end_char
                        )
                        
                        pages.append(page_data)
                        char_position = end_char + 2  # +2 for page separator
        
        return pages
    
    def chunk_with_page_awareness(
        self, 
        document: Document, 
        config: Optional[ChunkingConfig] = None
    ) -> List[Chunk]:
        """
        Chunk a PDF document with full page and section awareness.
        
        Args:
            document: Document to chunk
            config: Chunking configuration (optional)
            
        Returns:
            List of Chunk objects with enhanced metadata
        """
        # Extract document structure
        doc_structure = self.extract_document_structure(document)
        
        # Create page-aware chunker
        chunker = PageAwareChunker(config)
        
        # Perform page-aware chunking
        chunks = chunker.chunk_document_structure(document, doc_structure)
        
        return chunks
    
    def load_and_chunk_with_page_awareness(
        self, 
        source: Union[Path, str],
        config: Optional[ChunkingConfig] = None
    ) -> List[Chunk]:
        """
        Load PDF(s) and immediately chunk with page awareness.
        
        This is a convenience method that combines loading and chunking.
        
        Args:
            source: File path or directory to load from
            config: Chunking configuration (optional)
            
        Returns:
            List of Chunk objects from all loaded documents
        """
        documents = self.load_documents(source)
        all_chunks = []
        
        for document in documents:
            chunks = self.chunk_with_page_awareness(document, config)
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def get_enhanced_metadata_example(self, document: Document) -> dict:
        """
        Generate an example of the enhanced metadata structure.
        
        This method demonstrates the metadata format that will be available
        for each chunk when using page-aware processing.
        
        Args:
            document: Document to analyze
            
        Returns:
            Example metadata dictionary
        """
        doc_structure = self.extract_document_structure(document)
        
        if not doc_structure.pages:
            return {"error": "No pages found in document"}
        
        # Get first page and section as example
        first_page = doc_structure.pages[0]
        first_section = doc_structure.sections[0] if doc_structure.sections else None
        
        # Generate example chunk metadata
        example_metadata = {
            # Document identification
            "doc_id": document.document_id or "example_doc_2023",
            "filename": document.metadata.get("filename", "example.pdf"),
            "source_url": document.metadata.get("source_url", "s3://bucket/example.pdf"),
            
            # Chunk identification
            "chunk_id": f"{first_page.page_number}-{first_section.section_number if first_section else '1'}-001",
            
            # Page context
            "page_start": first_page.page_number,
            "page_end": first_page.page_number,
            "page_range": str(first_page.page_number),
            
            # Section context (if detected)
            "section_title": first_section.title if first_section else "Introduction",
            "section_level": first_section.level if first_section else 1,
            "section_number": first_section.section_number if first_section else "1",
            
            # Character positions
            "char_start_in_page": 0,
            "char_end_in_page": min(1000, first_page.char_count),
            "char_start_global": first_page.start_char_global,
            "char_end_global": first_page.start_char_global + min(1000, first_page.char_count),
            
            # Content metadata
            "word_count": len("example chunk content".split()),
            "char_count": len("example chunk content"),
            "chunk_index": 0,
            
            # Processing metadata
            "extraction_timestamp": datetime.now().isoformat(),
            "processing_version": "2.0",
            "chunk_method": "page_aware_semantic",
            
            # Document-level metadata
            "document_type": document.document_type.value,
            "total_pages": doc_structure.total_pages,
            "total_document_chars": doc_structure.total_chars,
            "pdf_metadata": {
                "page_count": document.metadata.get("page_count", 0),
                "pdf_title": document.metadata.get("pdf_title", ""),
                "pdf_author": document.metadata.get("pdf_author", ""),
                "is_encrypted": document.metadata.get("is_encrypted", False),
            }
        }
        
        return example_metadata
    
    def validate_page_aware_processing(self, document: Document) -> dict:
        """
        Validate that page-aware processing will work correctly.
        
        Args:
            document: Document to validate
            
        Returns:
            Validation results dictionary
        """
        results = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "stats": {}
        }
        
        try:
            # Extract structure
            doc_structure = self.extract_document_structure(document)
            
            # Validate pages
            if not doc_structure.pages:
                results["errors"].append("No pages detected in document")
                results["is_valid"] = False
            else:
                results["stats"]["total_pages"] = len(doc_structure.pages)
                results["stats"]["total_chars"] = doc_structure.total_chars
                
                # Check for page numbering issues
                page_numbers = [p.page_number for p in doc_structure.pages]
                if page_numbers != list(range(1, len(page_numbers) + 1)):
                    results["warnings"].append("Page numbering is not sequential")
            
            # Validate sections
            if doc_structure.sections:
                results["stats"]["total_sections"] = len(doc_structure.sections)
                
                # Validate section structure
                section_detector = SectionDetector()
                section_warnings = section_detector.validate_section_structure(doc_structure.sections)
                results["warnings"].extend(section_warnings)
            else:
                results["warnings"].append("No sections detected - will use page-only chunking")
            
            # Test chunking
            try:
                chunker = PageAwareChunker()
                test_chunks = chunker.chunk_document_structure(document, doc_structure)
                results["stats"]["test_chunks_generated"] = len(test_chunks)
                
                if test_chunks:
                    results["stats"]["avg_chunk_size"] = sum(c.get_char_count() for c in test_chunks) / len(test_chunks)
                    results["stats"]["chunks_with_page_info"] = sum(1 for c in test_chunks if c.page_start)
                    results["stats"]["chunks_with_section_info"] = sum(1 for c in test_chunks if c.section_title)
                
            except Exception as e:
                results["errors"].append(f"Chunking test failed: {e}")
                results["is_valid"] = False
        
        except Exception as e:
            results["errors"].append(f"Structure extraction failed: {e}")
            results["is_valid"] = False
        
        return results
