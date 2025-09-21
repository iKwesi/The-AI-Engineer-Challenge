"""
Section detection utilities for document processing.

This module provides utilities for detecting headings, sections, and document
structure to enable semantic chunking and rich source attribution.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Pattern
from enum import Enum

from ..models import PageData, SectionData


class HeadingType(Enum):
    """Types of headings that can be detected."""
    NUMBERED = "numbered"  # 1. Introduction, 2.1 Overview
    CAPITALIZED = "capitalized"  # CHAPTER 1, SECTION A
    TITLE_CASE = "title_case"  # Introduction to AI
    MARKDOWN = "markdown"  # # Heading, ## Subheading
    OUTLINE = "outline"  # I. Roman numerals, A. Letters


@dataclass
class HeadingPattern:
    """
    Represents a pattern for detecting headings in text.
    """
    pattern: Pattern[str]
    heading_type: HeadingType
    level: int  # 1=chapter, 2=section, 3=subsection, etc.
    description: str
    
    def match(self, line: str) -> Optional[re.Match]:
        """Check if a line matches this heading pattern."""
        return self.pattern.match(line.strip())
    
    def extract_title(self, line: str) -> str:
        """Extract the title from a matched line."""
        match = self.match(line)
        if match:
            # Try to get the title from named group, otherwise use the whole match
            try:
                return match.group('title').strip()
            except (IndexError, AttributeError):
                # Remove the numbering/formatting and return the title
                return re.sub(r'^[0-9IVXivx]+[\.\)]*\s*', '', line.strip())
        return line.strip()
    
    def extract_number(self, line: str) -> Optional[str]:
        """Extract the section number from a matched line."""
        match = self.match(line)
        if match:
            try:
                return match.group('number').strip()
            except (IndexError, AttributeError):
                # Try to extract number from the beginning
                number_match = re.match(r'^([0-9IVXivx]+[\.\)]*)', line.strip())
                if number_match:
                    return number_match.group(1).rstrip('.)')
        return None


class SectionDetector:
    """
    Detects sections and headings in document text.
    
    Uses pattern matching and heuristics to identify document structure.
    """
    
    def __init__(self):
        """Initialize the section detector with default patterns."""
        self.heading_patterns = self._create_default_patterns()
    
    def _create_default_patterns(self) -> List[HeadingPattern]:
        """Create default heading detection patterns."""
        patterns = []
        
        # Level 1: Chapters (numbered)
        patterns.append(HeadingPattern(
            pattern=re.compile(r'^(?P<number>\d+)\.?\s+(?P<title>.+)$', re.IGNORECASE),
            heading_type=HeadingType.NUMBERED,
            level=1,
            description="Numbered chapters (1. Introduction)"
        ))
        
        # Level 1: Chapters (capitalized)
        patterns.append(HeadingPattern(
            pattern=re.compile(r'^(CHAPTER|SECTION|PART)\s+(?P<number>[IVXivx0-9]+)[\.\:\s]*(?P<title>.*)$', re.IGNORECASE),
            heading_type=HeadingType.CAPITALIZED,
            level=1,
            description="Capitalized chapters (CHAPTER 1)"
        ))
        
        # Level 2: Sections (numbered)
        patterns.append(HeadingPattern(
            pattern=re.compile(r'^(?P<number>\d+\.\d+)\.?\s+(?P<title>.+)$'),
            heading_type=HeadingType.NUMBERED,
            level=2,
            description="Numbered sections (2.1 Overview)"
        ))
        
        # Level 3: Subsections (numbered)
        patterns.append(HeadingPattern(
            pattern=re.compile(r'^(?P<number>\d+\.\d+\.\d+)\.?\s+(?P<title>.+)$'),
            heading_type=HeadingType.NUMBERED,
            level=3,
            description="Numbered subsections (2.1.1 Details)"
        ))
        
        # Level 1-3: Markdown style
        patterns.append(HeadingPattern(
            pattern=re.compile(r'^#{1}\s+(?P<title>.+)$'),
            heading_type=HeadingType.MARKDOWN,
            level=1,
            description="Markdown H1 (# Heading)"
        ))
        
        patterns.append(HeadingPattern(
            pattern=re.compile(r'^#{2}\s+(?P<title>.+)$'),
            heading_type=HeadingType.MARKDOWN,
            level=2,
            description="Markdown H2 (## Heading)"
        ))
        
        patterns.append(HeadingPattern(
            pattern=re.compile(r'^#{3}\s+(?P<title>.+)$'),
            heading_type=HeadingType.MARKDOWN,
            level=3,
            description="Markdown H3 (### Heading)"
        ))
        
        # Level 1: Roman numerals
        patterns.append(HeadingPattern(
            pattern=re.compile(r'^(?P<number>[IVX]+)\.?\s+(?P<title>.+)$'),
            heading_type=HeadingType.OUTLINE,
            level=1,
            description="Roman numeral sections (I. Introduction)"
        ))
        
        # Level 2: Letters
        patterns.append(HeadingPattern(
            pattern=re.compile(r'^(?P<number>[A-Z])\.?\s+(?P<title>.+)$'),
            heading_type=HeadingType.OUTLINE,
            level=2,
            description="Letter subsections (A. Overview)"
        ))
        
        # All caps headings (heuristic)
        patterns.append(HeadingPattern(
            pattern=re.compile(r'^(?P<title>[A-Z\s]{3,})$'),
            heading_type=HeadingType.CAPITALIZED,
            level=2,
            description="All caps headings (INTRODUCTION)"
        ))
        
        return patterns
    
    def detect_sections_in_pages(self, pages: List[PageData]) -> List[SectionData]:
        """
        Detect sections across multiple pages.
        
        Args:
            pages: List of PageData objects
            
        Returns:
            List of detected SectionData objects
        """
        sections = []
        current_section = None
        
        for page in pages:
            page_sections = self.detect_sections_in_page(page)
            
            for section in page_sections:
                # Close previous section if we found a new one at same or higher level
                if current_section and section.level <= current_section.level:
                    current_section.page_end = page.page_number - 1
                    sections.append(current_section)
                
                current_section = section
        
        # Close the last section
        if current_section:
            current_section.page_end = pages[-1].page_number
            sections.append(current_section)
        
        return sections
    
    def detect_sections_in_page(self, page: PageData) -> List[SectionData]:
        """
        Detect sections within a single page.
        
        Args:
            page: PageData object
            
        Returns:
            List of SectionData objects found on this page
        """
        sections = []
        lines = page.text.split('\n')
        char_position = page.start_char_global
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                char_position += len(lines[line_num]) + 1  # +1 for newline
                continue
            
            # Check each pattern
            for pattern in self.heading_patterns:
                match = pattern.match(line)
                if match:
                    title = pattern.extract_title(line)
                    number = pattern.extract_number(line)
                    
                    # Additional validation for all-caps pattern
                    if pattern.heading_type == HeadingType.CAPITALIZED and pattern.level == 2:
                        # Skip if it's too short or contains common non-heading words
                        if len(title) < 3 or any(word in title.lower() for word in ['the', 'and', 'or', 'but', 'in', 'on', 'at']):
                            char_position += len(lines[line_num]) + 1
                            continue
                    
                    section = SectionData(
                        title=title,
                        level=pattern.level,
                        page_start=page.page_number,
                        start_char_global=char_position,
                        section_number=number
                    )
                    
                    sections.append(section)
                    break  # Found a match, don't check other patterns
            
            char_position += len(lines[line_num]) + 1  # +1 for newline
        
        return sections
    
    def add_custom_pattern(self, pattern: HeadingPattern) -> None:
        """Add a custom heading pattern."""
        self.heading_patterns.append(pattern)
    
    def get_section_hierarchy(self, sections: List[SectionData]) -> Dict[str, List[SectionData]]:
        """
        Build a hierarchical structure of sections.
        
        Args:
            sections: List of SectionData objects
            
        Returns:
            Dictionary mapping parent sections to their children
        """
        hierarchy = {}
        section_stack = []
        
        for section in sections:
            # Pop sections from stack that are at same or lower level
            while section_stack and section_stack[-1].level >= section.level:
                section_stack.pop()
            
            # Set parent if there's a section in the stack
            if section_stack:
                parent = section_stack[-1]
                section.parent_section = parent.title
                
                if parent.title not in hierarchy:
                    hierarchy[parent.title] = []
                hierarchy[parent.title].append(section)
            
            section_stack.append(section)
        
        return hierarchy
    
    def generate_semantic_chunk_id(self, page_num: int, section: Optional[SectionData], chunk_index: int) -> str:
        """
        Generate semantic chunk IDs like '23-4.1-002'.
        
        Args:
            page_num: Page number
            section: Section data (optional)
            chunk_index: Index of chunk within the section/page
            
        Returns:
            Semantic chunk ID string
        """
        if section and section.section_number:
            return f"{page_num}-{section.section_number}-{chunk_index:03d}"
        else:
            return f"{page_num}-{chunk_index:03d}"
    
    def validate_section_structure(self, sections: List[SectionData]) -> List[str]:
        """
        Validate the detected section structure and return warnings.
        
        Args:
            sections: List of detected sections
            
        Returns:
            List of validation warnings
        """
        warnings = []
        
        if not sections:
            warnings.append("No sections detected in document")
            return warnings
        
        # Check for level jumps (e.g., level 1 directly to level 3)
        for i in range(1, len(sections)):
            prev_level = sections[i-1].level
            curr_level = sections[i].level
            
            if curr_level > prev_level + 1:
                warnings.append(
                    f"Section level jump detected: '{sections[i-1].title}' (level {prev_level}) "
                    f"to '{sections[i].title}' (level {curr_level})"
                )
        
        # Check for very short sections (might be false positives)
        for section in sections:
            if section.page_start == section.page_end and len(section.title) < 5:
                warnings.append(f"Very short section detected: '{section.title}' on page {section.page_start}")
        
        return warnings
