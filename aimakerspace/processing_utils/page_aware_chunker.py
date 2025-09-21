"""
Page-aware chunking utilities for document processing.

This module provides utilities for chunking documents while preserving
page context and section boundaries for enhanced RAG source attribution.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import re

from ..models import (
    Chunk, 
    PageData, 
    SectionData, 
    DocumentStructure, 
    ChunkingConfig,
    Document
)
from .section_detector import SectionDetector


class PageAwareChunker:
    """
    Chunks documents while preserving page and section context.
    
    This chunker ensures that every chunk knows exactly which page(s) and
    section it came from, enabling precise source attribution in RAG systems.
    """
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        """
        Initialize the page-aware chunker.
        
        Args:
            config: Chunking configuration (uses defaults if None)
        """
        self.config = config or ChunkingConfig()
        self.section_detector = SectionDetector()
    
    def chunk_document_structure(
        self, 
        document: Document, 
        doc_structure: DocumentStructure
    ) -> List[Chunk]:
        """
        Chunk a document using its detected structure.
        
        Args:
            document: Original document
            doc_structure: Detected document structure with pages and sections
            
        Returns:
            List of Chunk objects with enhanced metadata
        """
        chunks = []
        
        if self.config.page_aware:
            chunks = self._chunk_page_aware(document, doc_structure)
        else:
            # Fallback to regular chunking
            chunks = self._chunk_regular(document, doc_structure)
        
        # Add global metadata to all chunks
        for chunk in chunks:
            self._add_global_metadata(chunk, document, doc_structure)
        
        return chunks
    
    def _chunk_page_aware(
        self, 
        document: Document, 
        doc_structure: DocumentStructure
    ) -> List[Chunk]:
        """
        Perform page-aware chunking that respects page and section boundaries.
        
        Args:
            document: Original document
            doc_structure: Document structure
            
        Returns:
            List of chunks with page context
        """
        chunks = []
        chunk_index = 0
        
        for page in doc_structure.pages:
            page_chunks = self._chunk_single_page(
                page, 
                doc_structure, 
                document.document_id,
                chunk_index
            )
            chunks.extend(page_chunks)
            chunk_index += len(page_chunks)
        
        return chunks
    
    def _chunk_single_page(
        self, 
        page: PageData, 
        doc_structure: DocumentStructure,
        document_id: str,
        start_chunk_index: int
    ) -> List[Chunk]:
        """
        Chunk a single page while preserving context.
        
        Args:
            page: Page data to chunk
            doc_structure: Full document structure
            document_id: Document identifier
            start_chunk_index: Starting index for chunks
            
        Returns:
            List of chunks for this page
        """
        chunks = []
        page_text = page.text
        
        # Get section for this page
        current_section = doc_structure.get_section_for_page(page.page_number)
        
        # Split page into chunks
        text_chunks = self._split_text_into_chunks(page_text)
        
        char_position_in_page = 0
        
        for i, chunk_text in enumerate(text_chunks):
            chunk_index = start_chunk_index + i
            
            # Calculate character positions
            start_char_in_page = char_position_in_page
            end_char_in_page = start_char_in_page + len(chunk_text)
            start_char_global = page.start_char_global + start_char_in_page
            end_char_global = page.start_char_global + end_char_in_page
            
            # Generate semantic chunk ID
            chunk_id = self.section_detector.generate_semantic_chunk_id(
                page.page_number, 
                current_section, 
                i + 1
            )
            
            # Create chunk with enhanced metadata
            chunk = Chunk(
                content=chunk_text.strip(),
                chunk_index=chunk_index,
                source_document_id=document_id,
                start_char=start_char_global,
                end_char=end_char_global,
                chunk_id=chunk_id,
                page_start=page.page_number,
                page_end=page.page_number,
                section_title=current_section.title if current_section else None,
                section_level=current_section.level if current_section else None,
                metadata={
                    "char_start_in_page": start_char_in_page,
                    "char_end_in_page": end_char_in_page,
                    "page_word_count": page.word_count,
                    "page_char_count": page.char_count,
                    "section_number": current_section.section_number if current_section else None,
                    "chunk_method": "page_aware",
                    "processing_timestamp": datetime.now().isoformat()
                }
            )
            
            chunks.append(chunk)
            char_position_in_page = end_char_in_page
        
        return chunks
    
    def _chunk_regular(
        self, 
        document: Document, 
        doc_structure: DocumentStructure
    ) -> List[Chunk]:
        """
        Fallback to regular chunking without page awareness.
        
        Args:
            document: Original document
            doc_structure: Document structure
            
        Returns:
            List of chunks with basic metadata
        """
        chunks = []
        text_chunks = self._split_text_into_chunks(document.content)
        char_position = 0
        
        for i, chunk_text in enumerate(text_chunks):
            start_char = char_position
            end_char = start_char + len(chunk_text)
            
            # Try to map to page using character position
            page_number = self._find_page_for_char_position(end_char, doc_structure)
            
            chunk = Chunk(
                content=chunk_text.strip(),
                chunk_index=i,
                source_document_id=document.document_id,
                start_char=start_char,
                end_char=end_char,
                chunk_id=f"chunk-{i:03d}",
                page_start=page_number,
                page_end=page_number,
                metadata={
                    "chunk_method": "regular",
                    "processing_timestamp": datetime.now().isoformat()
                }
            )
            
            chunks.append(chunk)
            char_position = end_char
        
        return chunks
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """
        Split text into chunks based on configuration.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        if self.config.preserve_sentences:
            return self._split_preserving_sentences(text)
        else:
            return self._split_by_character_count(text)
    
    def _split_preserving_sentences(self, text: str) -> List[str]:
        """
        Split text while preserving sentence boundaries.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks that don't break sentences
        """
        # Simple sentence splitting (can be enhanced with more sophisticated NLP)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) + 1 > self.config.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # Single sentence is too long, split it
                    chunks.extend(self._split_by_character_count(sentence))
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_by_character_count(self, text: str) -> List[str]:
        """
        Split text by character count with overlap.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.config.chunk_size
            
            # If this is not the last chunk, try to break at word boundary
            if end < len(text):
                # Look for the last space within the chunk
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk = text[start:end].strip()
            if len(chunk) >= self.config.min_chunk_size:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.config.overlap
            if start <= 0:
                start = end
        
        return chunks
    
    def _find_page_for_char_position(
        self, 
        char_position: int, 
        doc_structure: DocumentStructure
    ) -> Optional[int]:
        """
        Find which page contains the given character position.
        
        Args:
            char_position: Global character position
            doc_structure: Document structure
            
        Returns:
            Page number or None if not found
        """
        for page in doc_structure.pages:
            if page.start_char_global <= char_position <= page.end_char_global:
                return page.page_number
        return None
    
    def _add_global_metadata(
        self, 
        chunk: Chunk, 
        document: Document, 
        doc_structure: DocumentStructure
    ) -> None:
        """
        Add global metadata to a chunk.
        
        Args:
            chunk: Chunk to enhance
            document: Original document
            doc_structure: Document structure
        """
        # Add document-level metadata
        chunk.metadata.update({
            "filename": document.metadata.get("filename", "unknown"),
            "document_type": document.document_type.value,
            "total_pages": doc_structure.total_pages,
            "total_document_chars": doc_structure.total_chars,
            "page_range": chunk.get_page_range(),
        })
        
        # Add source URL if available
        if "source_url" in document.metadata:
            chunk.metadata["source_url"] = document.metadata["source_url"]
    
    def chunk_with_cross_page_support(
        self, 
        document: Document, 
        doc_structure: DocumentStructure
    ) -> List[Chunk]:
        """
        Advanced chunking that can span multiple pages when beneficial.
        
        This method creates chunks that can cross page boundaries while
        still maintaining accurate page range metadata.
        
        Args:
            document: Original document
            doc_structure: Document structure
            
        Returns:
            List of chunks that may span multiple pages
        """
        chunks = []
        all_text = document.content
        text_chunks = self._split_text_into_chunks(all_text)
        
        char_position = 0
        
        for i, chunk_text in enumerate(text_chunks):
            start_char = char_position
            end_char = start_char + len(chunk_text)
            
            # Find page range for this chunk
            start_page = self._find_page_for_char_position(start_char, doc_structure)
            end_page = self._find_page_for_char_position(end_char, doc_structure)
            
            # Find section for this chunk (use start position)
            current_section = None
            if start_page:
                current_section = doc_structure.get_section_for_page(start_page)
            
            # Generate chunk ID
            chunk_id = self.section_detector.generate_semantic_chunk_id(
                start_page or 1, 
                current_section, 
                i + 1
            )
            
            chunk = Chunk(
                content=chunk_text.strip(),
                chunk_index=i,
                source_document_id=document.document_id,
                start_char=start_char,
                end_char=end_char,
                chunk_id=chunk_id,
                page_start=start_page,
                page_end=end_page,
                section_title=current_section.title if current_section else None,
                section_level=current_section.level if current_section else None,
                metadata={
                    "spans_multiple_pages": start_page != end_page,
                    "chunk_method": "cross_page_aware",
                    "processing_timestamp": datetime.now().isoformat()
                }
            )
            
            chunks.append(chunk)
            self._add_global_metadata(chunk, document, doc_structure)
            char_position = end_char
        
        return chunks
    
    def get_chunking_stats(self, chunks: List[Chunk]) -> Dict[str, Any]:
        """
        Generate statistics about the chunking results.
        
        Args:
            chunks: List of chunks to analyze
            
        Returns:
            Dictionary with chunking statistics
        """
        if not chunks:
            return {"total_chunks": 0}
        
        total_chunks = len(chunks)
        total_chars = sum(chunk.get_char_count() for chunk in chunks)
        total_words = sum(chunk.get_word_count() for chunk in chunks)
        
        # Page distribution
        page_distribution = {}
        cross_page_chunks = 0
        
        for chunk in chunks:
            if chunk.page_start:
                page_range = chunk.get_page_range()
                page_distribution[page_range] = page_distribution.get(page_range, 0) + 1
                
                if chunk.page_start != chunk.page_end:
                    cross_page_chunks += 1
        
        # Section distribution
        section_distribution = {}
        for chunk in chunks:
            if chunk.section_title:
                section_distribution[chunk.section_title] = section_distribution.get(chunk.section_title, 0) + 1
        
        return {
            "total_chunks": total_chunks,
            "total_characters": total_chars,
            "total_words": total_words,
            "avg_chunk_size": total_chars / total_chunks,
            "avg_words_per_chunk": total_words / total_chunks,
            "cross_page_chunks": cross_page_chunks,
            "pages_covered": len(page_distribution),
            "sections_covered": len(section_distribution),
            "page_distribution": page_distribution,
            "section_distribution": section_distribution,
            "chunking_method": chunks[0].metadata.get("chunk_method", "unknown") if chunks else "unknown"
        }
