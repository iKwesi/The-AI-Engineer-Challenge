"""
Text splitting utilities for document processing.

This module provides utilities for splitting text into chunks with various strategies,
moved from the original text_utils.py to follow Single Responsibility Principle.
"""

from typing import List, Optional
import re

from ..models import ChunkingConfig


class CharacterTextSplitter:
    """
    Split text into chunks based on character count with overlap.
    
    Enhanced version of the original CharacterTextSplitter with sentence-aware
    splitting and configurable strategies.
    """
    
    def __init__(
        self, 
        chunk_size: int = 1000, 
        chunk_overlap: int = 200,
        preserve_sentences: bool = True,
        min_chunk_size: int = 100
    ):
        """
        Initialize the text splitter.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            preserve_sentences: Whether to avoid breaking sentences when possible
            min_chunk_size: Minimum size for a chunk to be included
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.preserve_sentences = preserve_sentences
        self.min_chunk_size = min_chunk_size
        
        # Validate parameters
        if chunk_size <= chunk_overlap:
            raise ValueError("Chunk size must be greater than chunk overlap")
        if min_chunk_size <= 0:
            raise ValueError("Minimum chunk size must be positive")
        if chunk_overlap < 0:
            raise ValueError("Chunk overlap cannot be negative")
    
    @classmethod
    def from_config(cls, config: ChunkingConfig) -> 'CharacterTextSplitter':
        """
        Create a CharacterTextSplitter from a ChunkingConfig.
        
        Args:
            config: ChunkingConfig object
            
        Returns:
            CharacterTextSplitter instance
        """
        return cls(
            chunk_size=config.chunk_size,
            chunk_overlap=config.overlap,
            preserve_sentences=config.preserve_sentences,
            min_chunk_size=config.min_chunk_size
        )
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        if not text.strip():
            return []
        
        if self.preserve_sentences:
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
        # Enhanced sentence splitting with better patterns
        sentence_patterns = [
            r'(?<=[.!?])\s+(?=[A-Z])',  # Period/exclamation/question followed by space and capital
            r'(?<=[.!?])\s*\n+\s*',     # Period/exclamation/question followed by newlines
            r'(?<=\.)\s+(?=\d+\.)',     # Numbered lists (1. 2. etc.)
        ]
        
        # Split into sentences using multiple patterns
        sentences = [text]
        for pattern in sentence_patterns:
            new_sentences = []
            for sentence in sentences:
                new_sentences.extend(re.split(pattern, sentence))
            sentences = new_sentences
        
        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Check if adding this sentence would exceed chunk size
            potential_chunk = current_chunk + (" " if current_chunk else "") + sentence
            
            if len(potential_chunk) <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                # Current chunk is ready, start a new one
                if current_chunk and len(current_chunk) >= self.min_chunk_size:
                    chunks.append(current_chunk.strip())
                
                # If single sentence is too long, split it by character count
                if len(sentence) > self.chunk_size:
                    sentence_chunks = self._split_by_character_count(sentence)
                    chunks.extend(sentence_chunks)
                    current_chunk = ""
                else:
                    current_chunk = sentence
        
        # Add the last chunk
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append(current_chunk.strip())
        
        return self._apply_overlap(chunks)
    
    def _split_by_character_count(self, text: str) -> List[str]:
        """
        Split text by character count with word boundary awareness.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # If this is not the last chunk, try to break at word boundary
            if end < len(text):
                # Look for the last space within the chunk
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
                
                # If no space found, look for other word boundaries
                if end == start + self.chunk_size:
                    for boundary in ['\n', '\t', '-', '—']:
                        last_boundary = text.rfind(boundary, start, end)
                        if last_boundary > start:
                            end = last_boundary
                            break
            
            chunk = text[start:end].strip()
            if len(chunk) >= self.min_chunk_size:
                chunks.append(chunk)
            
            # Move start position
            start = end
        
        return self._apply_overlap(chunks)
    
    def _apply_overlap(self, chunks: List[str]) -> List[str]:
        """
        Apply overlap between chunks.
        
        Args:
            chunks: List of chunks without overlap
            
        Returns:
            List of chunks with overlap applied
        """
        if len(chunks) <= 1 or self.chunk_overlap == 0:
            return chunks
        
        overlapped_chunks = [chunks[0]]  # First chunk stays the same
        
        for i in range(1, len(chunks)):
            current_chunk = chunks[i]
            previous_chunk = chunks[i - 1]
            
            # Get overlap from previous chunk
            if len(previous_chunk) > self.chunk_overlap:
                overlap_text = previous_chunk[-self.chunk_overlap:]
                
                # Try to find a good break point in the overlap
                space_pos = overlap_text.find(' ')
                if space_pos > 0:
                    overlap_text = overlap_text[space_pos + 1:]
                
                # Combine overlap with current chunk
                combined_chunk = overlap_text + " " + current_chunk
                overlapped_chunks.append(combined_chunk)
            else:
                overlapped_chunks.append(current_chunk)
        
        return overlapped_chunks
    
    def get_chunk_metadata(self, text: str, chunks: List[str]) -> List[dict]:
        """
        Generate metadata for each chunk.
        
        Args:
            text: Original text
            chunks: List of chunks
            
        Returns:
            List of metadata dictionaries for each chunk
        """
        metadata_list = []
        char_position = 0
        
        for i, chunk in enumerate(chunks):
            # Find the position of this chunk in the original text
            chunk_start = text.find(chunk, char_position)
            if chunk_start == -1:
                # Fallback if exact match not found (due to overlap modifications)
                chunk_start = char_position
            
            chunk_end = chunk_start + len(chunk)
            
            metadata = {
                'chunk_index': i,
                'start_char': chunk_start,
                'end_char': chunk_end,
                'chunk_size': len(chunk),
                'word_count': len(chunk.split()),
                'splitter_type': 'sentence_aware' if self.preserve_sentences else 'character_based',
                'chunk_overlap_used': self.chunk_overlap if i > 0 else 0,
            }
            
            metadata_list.append(metadata)
            char_position = chunk_end
        
        return metadata_list
    
    def split_documents(self, documents: List[str]) -> List[List[str]]:
        """
        Split multiple documents into chunks.
        
        Args:
            documents: List of document texts
            
        Returns:
            List of chunk lists, one for each document
        """
        return [self.split_text(doc) for doc in documents]
    
    def get_stats(self, text: str) -> dict:
        """
        Get statistics about how the text would be split.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with splitting statistics
        """
        chunks = self.split_text(text)
        
        if not chunks:
            return {
                'total_chunks': 0,
                'total_characters': 0,
                'total_words': 0,
                'avg_chunk_size': 0,
                'avg_words_per_chunk': 0,
                'min_chunk_size': 0,
                'max_chunk_size': 0,
            }
        
        chunk_sizes = [len(chunk) for chunk in chunks]
        chunk_word_counts = [len(chunk.split()) for chunk in chunks]
        
        return {
            'total_chunks': len(chunks),
            'total_characters': sum(chunk_sizes),
            'total_words': sum(chunk_word_counts),
            'avg_chunk_size': sum(chunk_sizes) / len(chunks),
            'avg_words_per_chunk': sum(chunk_word_counts) / len(chunks),
            'min_chunk_size': min(chunk_sizes),
            'max_chunk_size': max(chunk_sizes),
            'chunk_size_distribution': {
                'small': len([s for s in chunk_sizes if s < self.chunk_size * 0.5]),
                'medium': len([s for s in chunk_sizes if self.chunk_size * 0.5 <= s < self.chunk_size * 0.8]),
                'large': len([s for s in chunk_sizes if s >= self.chunk_size * 0.8]),
            }
        }


class SemanticTextSplitter:
    """
    Split text based on semantic boundaries like paragraphs and sections.
    
    This splitter attempts to maintain semantic coherence by splitting at
    natural document boundaries.
    """
    
    def __init__(
        self,
        max_chunk_size: int = 1000,
        min_chunk_size: int = 100,
        prefer_paragraphs: bool = True
    ):
        """
        Initialize the semantic text splitter.
        
        Args:
            max_chunk_size: Maximum size of chunks
            min_chunk_size: Minimum size of chunks
            prefer_paragraphs: Whether to prefer paragraph boundaries
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.prefer_paragraphs = prefer_paragraphs
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text at semantic boundaries.
        
        Args:
            text: Text to split
            
        Returns:
            List of semantically coherent chunks
        """
        if not text.strip():
            return []
        
        # Split into paragraphs first
        paragraphs = self._split_into_paragraphs(text)
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If paragraph alone is too big, split it further
            if len(paragraph) > self.max_chunk_size:
                # Add current chunk if it exists
                if current_chunk and len(current_chunk) >= self.min_chunk_size:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # Split the large paragraph
                para_chunks = self._split_large_paragraph(paragraph)
                chunks.extend(para_chunks)
            else:
                # Check if adding this paragraph would exceed max size
                potential_chunk = current_chunk + ("\n\n" if current_chunk else "") + paragraph
                
                if len(potential_chunk) <= self.max_chunk_size:
                    current_chunk = potential_chunk
                else:
                    # Current chunk is ready
                    if current_chunk and len(current_chunk) >= self.min_chunk_size:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph
        
        # Add the last chunk
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs.
        
        Args:
            text: Text to split
            
        Returns:
            List of paragraphs
        """
        # Split on double newlines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Clean up paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def _split_large_paragraph(self, paragraph: str) -> List[str]:
        """
        Split a large paragraph into smaller chunks.
        
        Args:
            paragraph: Large paragraph to split
            
        Returns:
            List of smaller chunks
        """
        # Use sentence-based splitting for large paragraphs
        splitter = CharacterTextSplitter(
            chunk_size=self.max_chunk_size,
            chunk_overlap=100,
            preserve_sentences=True,
            min_chunk_size=self.min_chunk_size
        )
        
        return splitter.split_text(paragraph)


# Backward compatibility - maintain the original interface
def split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Convenience function for backward compatibility.
    
    Args:
        text: Text to split
        chunk_size: Maximum size of each chunk
        chunk_overlap: Number of characters to overlap
        
    Returns:
        List of text chunks
    """
    splitter = CharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_text(text)
