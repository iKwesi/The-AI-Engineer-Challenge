"""
RAG Enhancement utilities for improved retrieval capabilities.

This module provides enhancement utilities that can be used with the existing
RAGService to improve retrieval accuracy and handle edge cases better.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

# Set up logging
logger = logging.getLogger(__name__)


class TextNormalizer:
    """Handles text normalization for queries and chunks."""
    
    def __init__(self):
        """Initialize the text normalizer."""
        # Common synonyms and aliases for better matching
        self.synonym_map = {
            'quantum bit': 'qubit',
            'quantum bits': 'qubits',
            'quantum computer': 'quantum computing',
            'quantum computers': 'quantum computing',
            'machine learning': 'ML',
            'artificial intelligence': 'AI',
            'neural network': 'neural net',
            'neural networks': 'neural nets',
            'deep learning': 'DL',
            'natural language processing': 'NLP',
            'large language model': 'LLM',
            'large language models': 'LLMs',
        }
        
        # Compile regex patterns for efficiency
        self.whitespace_pattern = re.compile(r'\s+')
        self.punctuation_pattern = re.compile(r'[^\w\s]')
        
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for better matching.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower()
        
        # Apply synonym mapping
        for original, replacement in self.synonym_map.items():
            normalized = normalized.replace(original.lower(), replacement.lower())
        
        # Remove extra whitespace
        normalized = self.whitespace_pattern.sub(' ', normalized)
        
        # Strip leading/trailing whitespace
        normalized = normalized.strip()
        
        return normalized
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text for enhanced matching.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
