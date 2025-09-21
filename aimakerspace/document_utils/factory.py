"""
Document loader factory for automatic loader selection.

This module provides a factory class that automatically selects the appropriate
document loader based on file extension or URL pattern matching.
"""

from pathlib import Path
from typing import List, Union, Optional, Type
import re

from .base import DocumentLoader
from .text_utils import TextFileLoader
from .pdf_utils import PDFLoader
from .word_utils import WordDocumentLoader
from .excel_utils import ExcelLoader
from .youtube_utils import YouTubeLoader
from ..models import (
    Document, 
    ProcessingLimits, 
    UnsupportedFileTypeError, 
    DocumentProcessingError
)


class DocumentLoaderFactory:
    """
    Factory class for automatically selecting and creating appropriate document loaders.
    
    This factory examines the source (file path or URL) and returns the most suitable
    loader for processing that type of content.
    """
    
    def __init__(self, processing_limits: Optional[ProcessingLimits] = None):
        """
        Initialize the document loader factory.
        
        Args:
            processing_limits: Optional processing limits configuration
        """
        self.processing_limits = processing_limits or ProcessingLimits()
        
        # Register available loaders with their capabilities
        self._loaders = {
            'text': TextFileLoader,
            'pdf': PDFLoader,
            'word': WordDocumentLoader,
            'excel': ExcelLoader,
            'youtube': YouTubeLoader,
        }
        
        # File extension mappings
        self._extension_mappings = {
            '.txt': 'text',
            '.pdf': 'pdf',
            '.docx': 'word',
            '.doc': 'word',
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.csv': 'excel',
        }
    
    def create_loader(self, source: Union[Path, str], **kwargs) -> DocumentLoader:
        """
        Create the appropriate document loader for the given source.
        
        Args:
            source: File path or URL to create loader for
            **kwargs: Additional arguments to pass to the loader constructor
            
        Returns:
            Appropriate DocumentLoader instance
            
        Raises:
            UnsupportedFileTypeError: If no suitable loader is found
        """
        loader_type = self._determine_loader_type(source)
        loader_class = self._loaders[loader_type]
        
        # Create loader with appropriate arguments
        if loader_type == 'youtube':
            # YouTube loader doesn't take a path argument
            return loader_class(**kwargs)
        else:
            # File-based loaders take a path argument
            return loader_class(source, **kwargs)
    
    def load_documents(self, source: Union[Path, str], **kwargs) -> List[Document]:
        """
        Load documents from the given source using the appropriate loader.
        
        Args:
            source: File path or URL to load from
            **kwargs: Additional arguments to pass to the loader
            
        Returns:
            List of loaded Document objects
            
        Raises:
            UnsupportedFileTypeError: If no suitable loader is found
            DocumentProcessingError: If loading fails
        """
        loader = self.create_loader(source, **kwargs)
        return loader.load_documents(source)
    
    def can_load(self, source: Union[Path, str]) -> bool:
        """
        Check if any loader can handle the given source.
        
        Args:
            source: File path or URL to check
            
        Returns:
            True if a suitable loader exists, False otherwise
        """
        try:
            self._determine_loader_type(source)
            return True
        except UnsupportedFileTypeError:
            return False
    
    def _determine_loader_type(self, source: Union[Path, str]) -> str:
        """
        Determine the appropriate loader type for the given source.
        
        Args:
            source: File path or URL to analyze
            
        Returns:
            Loader type string
            
        Raises:
            UnsupportedFileTypeError: If no suitable loader is found
        """
        # Handle empty or None source
        if not source or str(source).strip() == "":
            raise UnsupportedFileTypeError("Empty source provided")
        
        # Check if it's a YouTube URL
        if self._is_youtube_url(str(source)):
            return 'youtube'
        
        # Check if it's a file path
        path = Path(source)
        
        # For directories, we'll use text loader as default
        # (individual loaders will handle their own file filtering)
        if path.is_dir():
            return 'text'  # Default for directory scanning
        
        # Check file extension
        extension = path.suffix.lower()
        if extension in self._extension_mappings:
            return self._extension_mappings[extension]
        
        # If no extension or unknown extension, try to guess from content
        if path.exists() and path.is_file():
            guessed_type = self._guess_file_type(path)
            if guessed_type:
                return guessed_type
        
        # No suitable loader found
        supported_formats = list(self._extension_mappings.keys()) + ['YouTube URLs']
        raise UnsupportedFileTypeError(
            f"No suitable loader found for: {source}. "
            f"Supported formats: {', '.join(supported_formats)}"
        )
    
    def _is_youtube_url(self, url: str) -> bool:
        """
        Check if a URL is a YouTube URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if it's a YouTube URL, False otherwise
        """
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]+)',
        ]
        
        for pattern in youtube_patterns:
            if re.search(pattern, url):
                return True
        
        return False
    
    def _guess_file_type(self, file_path: Path) -> Optional[str]:
        """
        Attempt to guess file type from content when extension is missing or unknown.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Guessed loader type or None if unable to determine
        """
        try:
            # Read first few bytes to check file signature
            with file_path.open('rb') as f:
                header = f.read(8)
            
            # PDF signature
            if header.startswith(b'%PDF'):
                return 'pdf'
            
            # ZIP-based formats (DOCX, XLSX) start with PK
            if header.startswith(b'PK'):
                # Try to read more to distinguish between DOCX and XLSX
                try:
                    with file_path.open('rb') as f:
                        content = f.read(1024)
                    
                    if b'word/' in content:
                        return 'word'
                    elif b'xl/' in content:
                        return 'excel'
                except:
                    pass
                
                # Default to word for ZIP files
                return 'word'
            
            # Try to read as text
            try:
                with file_path.open('r', encoding='utf-8') as f:
                    f.read(100)  # Try to read some text
                return 'text'
            except UnicodeDecodeError:
                pass
            
        except Exception:
            pass
        
        return None
    
    def get_supported_formats(self) -> dict:
        """
        Get information about supported formats and their loaders.
        
        Returns:
            Dictionary mapping formats to loader information
        """
        format_info = {}
        
        for ext, loader_type in self._extension_mappings.items():
            if loader_type not in format_info:
                format_info[loader_type] = {
                    'extensions': [],
                    'description': '',
                    'loader_class': self._loaders[loader_type].__name__
                }
            format_info[loader_type]['extensions'].append(ext)
        
        # Add descriptions
        descriptions = {
            'text': 'Plain text files',
            'pdf': 'PDF documents with text extraction',
            'word': 'Microsoft Word documents',
            'excel': 'Excel spreadsheets and CSV files',
            'youtube': 'YouTube video transcripts',
        }
        
        for loader_type, info in format_info.items():
            info['description'] = descriptions.get(loader_type, 'Unknown format')
        
        # Add YouTube separately since it doesn't have file extensions
        format_info['youtube'] = {
            'extensions': ['YouTube URLs'],
            'description': descriptions['youtube'],
            'loader_class': self._loaders['youtube'].__name__
        }
        
        return format_info
    
    def load_multiple_sources(self, sources: List[Union[Path, str]], **kwargs) -> List[Document]:
        """
        Load documents from multiple sources using appropriate loaders.
        
        Args:
            sources: List of file paths or URLs to load from
            **kwargs: Additional arguments to pass to loaders
            
        Returns:
            List of all loaded Document objects
        """
        all_documents = []
        
        for source in sources:
            try:
                documents = self.load_documents(source, **kwargs)
                all_documents.extend(documents)
            except Exception as e:
                print(f"Warning: Failed to load {source}: {e}")
                continue
        
        return all_documents
    
    def validate_sources(self, sources: List[Union[Path, str]]) -> dict:
        """
        Validate multiple sources and return detailed information.
        
        Args:
            sources: List of sources to validate
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': [],
            'invalid': [],
            'by_type': {},
            'total_size': 0,
            'warnings': []
        }
        
        for source in sources:
            try:
                if self.can_load(source):
                    loader_type = self._determine_loader_type(source)
                    
                    # Check file size for file-based sources
                    if isinstance(source, (str, Path)) and Path(source).exists():
                        path = Path(source)
                        if path.is_file():
                            file_size = path.stat().st_size
                            results['total_size'] += file_size
                            
                            # Check individual file size
                            max_size = self.processing_limits.get_max_file_size_bytes()
                            if file_size > max_size:
                                results['warnings'].append(
                                    f"File {path.name} ({file_size} bytes) exceeds size limit"
                                )
                    
                    results['valid'].append({
                        'source': str(source),
                        'type': loader_type,
                        'loader': self._loaders[loader_type].__name__
                    })
                    
                    # Count by type
                    if loader_type not in results['by_type']:
                        results['by_type'][loader_type] = 0
                    results['by_type'][loader_type] += 1
                    
                else:
                    results['invalid'].append({
                        'source': str(source),
                        'reason': 'No suitable loader found'
                    })
                    
            except Exception as e:
                results['invalid'].append({
                    'source': str(source),
                    'reason': str(e)
                })
        
        return results


# Convenience function for quick document loading
def load_documents(source: Union[Path, str], **kwargs) -> List[Document]:
    """
    Convenience function to load documents using the factory.
    
    Args:
        source: File path or URL to load from
        **kwargs: Additional arguments to pass to the loader
        
    Returns:
        List of loaded Document objects
    """
    factory = DocumentLoaderFactory()
    return factory.load_documents(source, **kwargs)


# Convenience function to check if a source can be loaded
def can_load(source: Union[Path, str]) -> bool:
    """
    Convenience function to check if a source can be loaded.
    
    Args:
        source: File path or URL to check
        
    Returns:
        True if the source can be loaded, False otherwise
    """
    factory = DocumentLoaderFactory()
    return factory.can_load(source)
