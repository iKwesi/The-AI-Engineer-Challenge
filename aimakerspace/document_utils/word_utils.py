"""
Word document loading utilities.

This module provides utilities for loading Microsoft Word documents (.docx, .doc)
with enhanced error handling, metadata extraction, and formatting preservation.
"""

from pathlib import Path
from typing import List, Union, Optional, Iterable
from docx import Document as DocxDocument
from docx.shared import Inches

from .base import FileBasedLoader
from ..models import Document, DocumentType, DocumentProcessingError


class WordDocumentLoader(FileBasedLoader):
    """
    Load Microsoft Word documents (.docx, .doc files).
    
    Extracts text content, handles tables, and preserves basic formatting
    while providing comprehensive metadata extraction.
    """

    def __init__(self, path: Union[str, Path], include_tables: bool = True, include_headers_footers: bool = True):
        """
        Initialize the Word document loader.
        
        Args:
            path: Path to Word file or directory
            include_tables: Whether to extract text from tables
            include_headers_footers: Whether to extract headers and footers
        """
        super().__init__(path)
        self.include_tables = include_tables
        self.include_headers_footers = include_headers_footers

    def can_load(self, source: Union[Path, str]) -> bool:
        """
        Check if this loader can handle the given source.
        
        Args:
            source: File path to check
            
        Returns:
            True if the source is a .docx/.doc file or directory, False otherwise
        """
        path = Path(source)
        if path.is_dir():
            return True
        return path.suffix.lower() in [".docx", ".doc"]

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
        elif path.is_file() and path.suffix.lower() in [".docx", ".doc"]:
            return [self._load_single_file(path)]
        else:
            raise DocumentProcessingError(
                f"Provided path must be a directory or a .docx/.doc file: {path}"
            )

    def _load_directory_documents(self, directory: Path) -> List[Document]:
        """
        Load all Word documents from a directory.
        
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
        Load a single Word document and return a Document object.
        
        Args:
            file_path: Path to the file to load
            
        Returns:
            A Document object containing the Word document content
            
        Raises:
            DocumentProcessingError: If the document cannot be loaded
        """
        # Validate file
        self.validate_file_size(file_path)
        self.validate_file_extension(file_path)
        
        try:
            content, doc_metadata = self._read_word_document(file_path)
            
            # Combine document metadata with standard metadata
            metadata = {
                "paragraph_count": doc_metadata.get("paragraph_count", 0),
                "table_count": doc_metadata.get("table_count", 0),
                "image_count": doc_metadata.get("image_count", 0),
                "doc_title": doc_metadata.get("title", ""),
                "doc_author": doc_metadata.get("author", ""),
                "doc_subject": doc_metadata.get("subject", ""),
                "doc_keywords": doc_metadata.get("keywords", ""),
                "doc_category": doc_metadata.get("category", ""),
                "doc_comments": doc_metadata.get("comments", ""),
                "creation_date": doc_metadata.get("created", ""),
                "modification_date": doc_metadata.get("modified", ""),
                "last_modified_by": doc_metadata.get("last_modified_by", ""),
                "revision": doc_metadata.get("revision", ""),
            }
            
            return self.create_document(
                content=content,
                source_path=file_path,
                document_type=DocumentType.WORD,
                metadata=metadata
            )
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to load Word document {file_path}: {e}")

    def _iter_directory_files(self, directory: Path) -> Iterable[Path]:
        """
        Iterate over Word documents in a directory.
        
        Args:
            directory: Directory to iterate over
            
        Yields:
            Path objects for .docx and .doc files
        """
        for pattern in ["*.docx", "*.doc"]:
            for entry in sorted(directory.rglob(pattern)):
                if entry.is_file():
                    yield entry

    def _read_word_document(self, file_path: Path) -> tuple[str, dict]:
        """
        Read a Word document and extract text content and metadata.
        
        Args:
            file_path: Path to the Word document
            
        Returns:
            A tuple of (extracted_text, metadata_dict)
            
        Raises:
            DocumentProcessingError: If the document cannot be read
        """
        try:
            # Load the document
            doc = DocxDocument(file_path)
            
            content_parts = []
            
            # Extract paragraphs
            paragraph_texts = []
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:  # Only add non-empty paragraphs
                    paragraph_texts.append(text)
            
            if paragraph_texts:
                content_parts.append("=== DOCUMENT CONTENT ===\n" + "\n\n".join(paragraph_texts))
            
            # Extract tables if requested
            if self.include_tables and doc.tables:
                table_texts = []
                for i, table in enumerate(doc.tables):
                    table_text = self._extract_table_text(table)
                    if table_text.strip():
                        table_texts.append(f"[Table {i + 1}]\n{table_text}")
                
                if table_texts:
                    content_parts.append("=== TABLES ===\n" + "\n\n".join(table_texts))
            
            # Extract headers and footers if requested
            if self.include_headers_footers:
                header_footer_text = self._extract_headers_footers(doc)
                if header_footer_text.strip():
                    content_parts.append("=== HEADERS & FOOTERS ===\n" + header_footer_text)
            
            # Combine all content
            content = "\n\n".join(content_parts) if content_parts else ""
            
            # Extract metadata
            metadata = self._extract_word_metadata(doc)
            metadata.update({
                "paragraph_count": len([p for p in doc.paragraphs if p.text.strip()]),
                "table_count": len(doc.tables),
                "image_count": self._count_images(doc),
            })
            
            return content, metadata
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to read Word document {file_path}: {e}")

    def _extract_table_text(self, table) -> str:
        """
        Extract text from a Word table.
        
        Args:
            table: python-docx Table object
            
        Returns:
            Formatted table text
        """
        try:
            table_data = []
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    cell_text = cell.text.strip().replace('\n', ' ')
                    row_data.append(cell_text)
                table_data.append(" | ".join(row_data))
            
            return "\n".join(table_data)
        except Exception as e:
            print(f"Warning: Failed to extract table text: {e}")
            return ""

    def _extract_headers_footers(self, doc) -> str:
        """
        Extract text from headers and footers.
        
        Args:
            doc: python-docx Document object
            
        Returns:
            Combined header and footer text
        """
        try:
            header_footer_parts = []
            
            # Extract headers
            for section in doc.sections:
                if section.header:
                    header_text = "\n".join([p.text for p in section.header.paragraphs if p.text.strip()])
                    if header_text.strip():
                        header_footer_parts.append(f"[Header]\n{header_text}")
                
                if section.footer:
                    footer_text = "\n".join([p.text for p in section.footer.paragraphs if p.text.strip()])
                    if footer_text.strip():
                        header_footer_parts.append(f"[Footer]\n{footer_text}")
            
            return "\n\n".join(header_footer_parts)
        except Exception as e:
            print(f"Warning: Failed to extract headers/footers: {e}")
            return ""

    def _count_images(self, doc) -> int:
        """
        Count the number of images in the document.
        
        Args:
            doc: python-docx Document object
            
        Returns:
            Number of images found
        """
        try:
            image_count = 0
            for rel in doc.part.rels.values():
                if "image" in rel.target_ref:
                    image_count += 1
            return image_count
        except Exception as e:
            print(f"Warning: Failed to count images: {e}")
            return 0

    def _extract_word_metadata(self, doc) -> dict:
        """
        Extract metadata from a Word document.
        
        Args:
            doc: python-docx Document object
            
        Returns:
            Dictionary containing document metadata
        """
        metadata = {}
        
        try:
            core_props = doc.core_properties
            
            # Extract core properties
            metadata_fields = {
                "title": core_props.title,
                "author": core_props.author,
                "subject": core_props.subject,
                "keywords": core_props.keywords,
                "category": core_props.category,
                "comments": core_props.comments,
                "created": core_props.created,
                "modified": core_props.modified,
                "last_modified_by": core_props.last_modified_by,
                "revision": core_props.revision,
            }
            
            for key, value in metadata_fields.items():
                if value is not None:
                    # Convert datetime objects to strings
                    if hasattr(value, 'isoformat'):
                        metadata[key] = value.isoformat()
                    else:
                        metadata[key] = str(value).strip()
                else:
                    metadata[key] = ""
                    
        except Exception as e:
            print(f"Warning: Failed to extract Word metadata: {e}")
            # Continue without metadata
        
        return metadata

    # Convenience methods for backward compatibility
    def load(self) -> None:
        """
        Populate self.documents from the configured path.
        """
        self.documents = self.load_documents(self.path)

    def load_file(self) -> None:
        """
        Load a single file specified by self.path.
        """
        super().load_file()

    def load_directory(self) -> None:
        """
        Load all Word documents contained within self.path.
        """
        super().load_directory()
