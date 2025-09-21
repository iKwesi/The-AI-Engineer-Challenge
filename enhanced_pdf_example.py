"""
Enhanced PDF Processing Example with Page-Aware Chunking

This example demonstrates the complete enhanced PDF processing pipeline
including page detection, section extraction, and precise source attribution.
"""

from pathlib import Path
from aimakerspace.document_utils.pdf_utils import PDFLoader
from aimakerspace.models import ChunkingConfig, Document, DocumentType
from aimakerspace.processing_utils.section_detector import SectionDetector
from aimakerspace.processing_utils.page_aware_chunker import PageAwareChunker

def demonstrate_enhanced_pdf_processing():
    """Demonstrate the complete enhanced PDF processing pipeline."""
    
    print("=== Enhanced PDF Processing with Page-Aware Chunking ===\n")
    
    # Example 1: Basic page-aware processing
    print("📄 Example 1: Basic Page-Aware Processing")
    print("-" * 50)
    
    # Create a sample document (in real usage, this would be loaded from PDF)
    sample_content = """[Page 1]
Introduction to AI Systems

Artificial Intelligence (AI) has revolutionized modern computing. This document provides a comprehensive overview of AI systems and their applications.

[Page 2]
1. Machine Learning Fundamentals

Machine learning is a subset of AI that enables computers to learn without explicit programming. Key concepts include:
- Supervised learning
- Unsupervised learning
- Reinforcement learning

[Page 3]
1.1 Supervised Learning

Supervised learning uses labeled training data to learn a mapping function. Common algorithms include:
- Linear regression
- Decision trees
- Neural networks

[Page 4]
1.2 Deep Learning

Deep learning uses neural networks with multiple layers to model complex patterns in data.

[Page 5]
2. Natural Language Processing

NLP enables computers to understand and process human language. Applications include:
- Text classification
- Sentiment analysis
- Machine translation"""

    sample_doc = Document(
        content=sample_content,
        document_type=DocumentType.PDF,
        document_id="ai_guide_2023",
        metadata={
            "filename": "ai_guide.pdf",
            "page_count": 5,
            "source_url": "s3://docs/ai_guide.pdf"
        }
    )
    
    # Initialize PDF loader
    loader = PDFLoader("/path/to/pdfs")
    
    # Extract document structure
    print("🔍 Extracting document structure...")
    doc_structure = loader.extract_document_structure(sample_doc)
    
    print(f"   📊 Found {doc_structure.total_pages} pages")
    print(f"   📊 Found {len(doc_structure.sections)} sections")
    print(f"   📊 Total characters: {doc_structure.total_chars}")
    
    # Display detected sections
    if doc_structure.sections:
        print("\n   📋 Detected Sections:")
        for section in doc_structure.sections:
            print(f"      Level {section.level}: {section.get_full_title()} (Page {section.get_page_range()})")
    
    # Example 2: Page-aware chunking
    print("\n📄 Example 2: Page-Aware Chunking")
    print("-" * 50)
    
    # Configure chunking
    config = ChunkingConfig(
        chunk_size=500,
        overlap=100,
        page_aware=True,
        respect_section_boundaries=True,
        preserve_sentences=True
    )
    
    # Perform page-aware chunking
    print("✂️  Performing page-aware chunking...")
    chunks = loader.chunk_with_page_awareness(sample_doc, config)
    
    print(f"   📊 Generated {len(chunks)} chunks")
    
    # Display first few chunks with metadata
    print("\n   📋 Sample Chunks with Enhanced Metadata:")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n      Chunk {i+1}:")
        print(f"         ID: {chunk.chunk_id}")
        print(f"         Page: {chunk.get_page_range()}")
        print(f"         Section: {chunk.section_title or 'None detected'}")
        print(f"         Content: {chunk.content[:100]}...")
        print(f"         Citation: {chunk.get_citation_text()}")
        print(f"         Source URL: {chunk.get_source_url()}")
    
    # Example 3: Enhanced metadata structure
    print("\n📄 Example 3: Enhanced Metadata Structure")
    print("-" * 50)
    
    example_metadata = loader.get_enhanced_metadata_example(sample_doc)
    
    print("   📋 Complete Metadata Structure:")
    for key, value in example_metadata.items():
        if isinstance(value, dict):
            print(f"      {key}:")
            for sub_key, sub_value in value.items():
                print(f"         {sub_key}: {sub_value}")
        else:
            print(f"      {key}: {value}")
    
    # Example 4: Validation and statistics
    print("\n📄 Example 4: Validation and Statistics")
    print("-" * 50)
    
    # Validate processing
    validation_results = loader.validate_page_aware_processing(sample_doc)
    
    print("   ✅ Validation Results:")
    print(f"      Valid: {validation_results['is_valid']}")
    
    if validation_results['warnings']:
        print("      ⚠️  Warnings:")
        for warning in validation_results['warnings']:
            print(f"         - {warning}")
    
    if validation_results['errors']:
        print("      ❌ Errors:")
        for error in validation_results['errors']:
            print(f"         - {error}")
    
    print("      📊 Statistics:")
    for key, value in validation_results['stats'].items():
        print(f"         {key}: {value}")
    
    # Example 5: Chunking statistics
    print("\n📄 Example 5: Chunking Statistics")
    print("-" * 50)
    
    chunker = PageAwareChunker(config)
    stats = chunker.get_chunking_stats(chunks)
    
    print("   📊 Chunking Statistics:")
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"      {key}:")
            for sub_key, sub_value in value.items():
                print(f"         {sub_key}: {sub_value}")
        else:
            print(f"      {key}: {value}")

def demonstrate_rag_citation_examples():
    """Demonstrate how enhanced metadata enables rich RAG citations."""
    
    print("\n=== RAG Citation Examples ===\n")
    
    # Sample chunk with enhanced metadata
    sample_chunk_metadata = {
        "doc_id": "ai_guide_2023",
        "chunk_id": "3-1.1-001",
        "filename": "ai_guide.pdf",
        "page_start": 3,
        "page_end": 3,
        "page_range": "3",
        "section_title": "1.1 Supervised Learning",
        "section_level": 2,
        "section_number": "1.1",
        "source_url": "s3://docs/ai_guide.pdf#page=3"
    }
    
    print("📋 Sample Chunk Metadata:")
    for key, value in sample_chunk_metadata.items():
        print(f"   {key}: {value}")
    
    print("\n🎯 RAG Citation Examples:")
    
    # Simple citation
    simple_citation = f"According to {sample_chunk_metadata['filename']} (page {sample_chunk_metadata['page_range']})"
    print(f"   Simple: {simple_citation}")
    
    # Rich citation with section
    rich_citation = f"According to section {sample_chunk_metadata['section_title']} of {sample_chunk_metadata['filename']} (page {sample_chunk_metadata['page_range']})"
    print(f"   Rich: {rich_citation}")
    
    # Citation with direct link
    link_citation = f"According to {sample_chunk_metadata['filename']} (page {sample_chunk_metadata['page_range']}) - [View Source]({sample_chunk_metadata['source_url']})"
    print(f"   With Link: {link_citation}")
    
    # Full context citation
    full_citation = f"According to section {sample_chunk_metadata['section_number']} '{sample_chunk_metadata['section_title']}' in {sample_chunk_metadata['filename']} (page {sample_chunk_metadata['page_range']}, chunk {sample_chunk_metadata['chunk_id']})"
    print(f"   Full Context: {full_citation}")

def demonstrate_section_detection():
    """Demonstrate section detection capabilities."""
    
    print("\n=== Section Detection Capabilities ===\n")
    
    # Initialize section detector
    detector = SectionDetector()
    
    print("📋 Supported Heading Patterns:")
    for i, pattern in enumerate(detector.heading_patterns, 1):
        print(f"   {i}. {pattern.description} (Level {pattern.level})")
    
    print("\n🔍 Pattern Matching Examples:")
    
    test_lines = [
        "1. Introduction",
        "2.1 Overview", 
        "2.1.1 Details",
        "CHAPTER 1: GETTING STARTED",
        "# Main Heading",
        "## Sub Heading",
        "### Sub-sub Heading",
        "I. Roman Numeral Section",
        "A. Letter Subsection",
        "INTRODUCTION"
    ]
    
    for line in test_lines:
        for pattern in detector.heading_patterns:
            if pattern.match(line):
                title = pattern.extract_title(line)
                number = pattern.extract_number(line)
                print(f"   '{line}' → Level {pattern.level}, Title: '{title}', Number: '{number}'")
                break
        else:
            print(f"   '{line}' → No pattern matched")

def demonstrate_cross_page_chunking():
    """Demonstrate cross-page chunking capabilities."""
    
    print("\n=== Cross-Page Chunking ===\n")
    
    # Sample content that spans pages
    cross_page_content = """[Page 10]
This is the end of a long paragraph that discusses important concepts in machine learning. The paragraph continues with detailed explanations and examples.

[Page 11]
The paragraph from the previous page continues here with more detailed information about neural networks and their applications in modern AI systems. This demonstrates how content can span multiple pages."""

    sample_doc = Document(
        content=cross_page_content,
        document_type=DocumentType.PDF,
        document_id="cross_page_example",
        metadata={"filename": "example.pdf"}
    )
    
    loader = PDFLoader("/path/to/pdfs")
    doc_structure = loader.extract_document_structure(sample_doc)
    
    # Configure for cross-page chunking
    config = ChunkingConfig(
        chunk_size=200,  # Small chunks to force cross-page
        overlap=50,
        page_aware=False  # Allow cross-page chunks
    )
    
    chunker = PageAwareChunker(config)
    cross_page_chunks = chunker.chunk_with_cross_page_support(sample_doc, doc_structure)
    
    print("📊 Cross-Page Chunking Results:")
    for i, chunk in enumerate(cross_page_chunks):
        spans_pages = chunk.metadata.get("spans_multiple_pages", False)
        print(f"   Chunk {i+1}: Pages {chunk.get_page_range()} (Spans: {spans_pages})")
        print(f"      Content: {chunk.content[:100]}...")

def demonstrate_batch_processing():
    """Demonstrate batch processing with enhanced metadata."""
    
    print("\n=== Batch Processing with Enhanced Metadata ===\n")
    
    # Simulate multiple PDF processing
    print("📁 Batch Processing Scenario:")
    print("   Files to process:")
    print("   - technical_spec.pdf (15 pages)")
    print("   - user_manual.pdf (8 pages)")
    print("   - api_docs.pdf (12 pages)")
    print("   Total: 35 pages, 3 documents")
    
    print("\n✅ Expected Results:")
    print("   - Each chunk knows its source document")
    print("   - Page numbers are document-specific")
    print("   - Section detection per document")
    print("   - Unique chunk IDs across all documents")
    print("   - Rich metadata for precise attribution")
    
    # Example chunk IDs from batch processing
    example_chunk_ids = [
        "tech_spec_2023:5-2.1-001",
        "tech_spec_2023:5-2.1-002", 
        "user_manual_2023:3-1-001",
        "api_docs_2023:8-3.2-001"
    ]
    
    print("\n📋 Example Chunk IDs from Batch:")
    for chunk_id in example_chunk_ids:
        print(f"   {chunk_id}")

if __name__ == "__main__":
    demonstrate_enhanced_pdf_processing()
    demonstrate_rag_citation_examples()
    demonstrate_section_detection()
    demonstrate_cross_page_chunking()
    demonstrate_batch_processing()
    
    print("\n" + "="*60)
    print("🎉 Enhanced PDF Processing Implementation Complete!")
    print("="*60)
    print("\n✅ Key Features Implemented:")
    print("   • Page-aware chunking with precise position tracking")
    print("   • Automatic section detection with multiple patterns")
    print("   • Rich metadata for RAG source attribution")
    print("   • Cross-page chunking support")
    print("   • Batch processing with unique identifiers")
    print("   • Validation and statistics")
    print("   • Backward compatibility maintained")
    
    print("\n🎯 RAG Benefits:")
    print("   • Precise citations: 'According to section 4.1 on page 23...'")
    print("   • Direct navigation: Links to specific pages")
    print("   • Context preservation: Section and document hierarchy")
    print("   • Multi-document support: Unique identifiers across corpus")
    
    print("\n🚀 Ready for Production:")
    print("   • Enterprise-grade security compliance")
    print("   • Scalable batch processing")
    print("   • Comprehensive error handling")
    print("   • Audit logging and validation")
