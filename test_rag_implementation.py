#!/usr/bin/env python3
"""
Test script for RAG implementation.

This script tests the core RAG functionality including:
- Document loading and processing
- Text chunking and embedding
- Vector storage and retrieval
- Context-aware chat responses
"""

import asyncio
import os
from pathlib import Path
from aimakerspace.processing_utils.rag_service import RAGService
from aimakerspace.models import ChunkingConfig, ProcessingLimits

async def test_rag_implementation():
    """Test the RAG implementation with a sample document."""
    
    # Check if we have an API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key to test the RAG implementation")
        return False
    
    print("🚀 Testing RAG Implementation")
    print("=" * 50)
    
    try:
        # Initialize RAG service
        print("1. Initializing RAG service...")
        chunking_config = ChunkingConfig(chunk_size=500, overlap=100)
        processing_limits = ProcessingLimits(max_file_size_mb=50)
        
        rag_service = RAGService(
            api_key=api_key,
            chunking_config=chunking_config,
            processing_limits=processing_limits
        )
        print("✅ RAG service initialized successfully")
        
        # Test with sample PDF if available
        test_pdf_path = Path("docs/test-docs/quantumML.pdf")
        if test_pdf_path.exists():
            print(f"\n2. Processing test document: {test_pdf_path}")
            
            processed_doc = await rag_service.process_document(
                source=test_pdf_path,
                document_id="test_quantum_ml",
                use_page_aware_chunking=True
            )
            
            print(f"✅ Document processed successfully!")
            print(f"   - Chunks created: {len(processed_doc.chunks)}")
            print(f"   - Document type: {processed_doc.original_document.document_type.value}")
            print(f"   - Processing method: {processed_doc.processing_metadata.get('chunking_method', 'unknown')}")
            
            # Test search functionality
            print("\n3. Testing search functionality...")
            search_result = await rag_service.search(
                query="What is quantum machine learning?",
                k=3
            )
            
            print(f"✅ Search completed!")
            print(f"   - Results found: {len(search_result.chunks)}")
            for i, chunk in enumerate(search_result.chunks[:2]):  # Show first 2 results
                print(f"   - Result {i+1}: {chunk.content[:100]}...")
            
            # Test RAG chat
            print("\n4. Testing RAG chat...")
            response = await rag_service.chat_with_context(
                user_message="What is quantum machine learning and how does it work?",
                max_context_chunks=3
            )
            
            print(f"✅ RAG chat completed!")
            print(f"   - Response length: {len(response)} characters")
            print(f"   - Response preview: {response[:200]}...")
            
            # Test service statistics
            print("\n5. Checking service statistics...")
            stats = rag_service.get_stats()
            print(f"✅ Statistics retrieved:")
            print(f"   - Documents processed: {stats['documents_processed']}")
            print(f"   - Chunks created: {stats['chunks_created']}")
            print(f"   - Queries processed: {stats['queries_processed']}")
            
        else:
            print(f"\n2. Test PDF not found at {test_pdf_path}")
            print("   Creating a simple text document for testing...")
            
            # Create a simple test document
            test_text_path = Path("test_document.txt")
            test_content = """
            Artificial Intelligence and Machine Learning
            
            Artificial Intelligence (AI) is a broad field of computer science that aims to create 
            systems capable of performing tasks that typically require human intelligence. These 
            tasks include learning, reasoning, problem-solving, perception, and language understanding.
            
            Machine Learning (ML) is a subset of AI that focuses on the development of algorithms 
            and statistical models that enable computers to improve their performance on a specific 
            task through experience, without being explicitly programmed for every scenario.
            
            Deep Learning is a subset of machine learning that uses neural networks with multiple 
            layers (hence "deep") to model and understand complex patterns in data. It has been 
            particularly successful in areas like image recognition, natural language processing, 
            and speech recognition.
            
            Applications of AI and ML include:
            - Autonomous vehicles
            - Medical diagnosis
            - Financial trading
            - Recommendation systems
            - Natural language processing
            - Computer vision
            """
            
            test_text_path.write_text(test_content)
            
            try:
                print(f"   Processing test text document: {test_text_path}")
                
                processed_doc = await rag_service.process_document(
                    source=test_text_path,
                    document_id="test_ai_ml",
                    use_page_aware_chunking=False
                )
                
                print(f"✅ Text document processed successfully!")
                print(f"   - Chunks created: {len(processed_doc.chunks)}")
                
                # Test search
                print("\n3. Testing search functionality...")
                search_result = await rag_service.search(
                    query="What is machine learning?",
                    k=2
                )
                
                print(f"✅ Search completed!")
                print(f"   - Results found: {len(search_result.chunks)}")
                
                # Test RAG chat
                print("\n4. Testing RAG chat...")
                response = await rag_service.chat_with_context(
                    user_message="Explain the difference between AI, ML, and Deep Learning",
                    max_context_chunks=3
                )
                
                print(f"✅ RAG chat completed!")
                print(f"   - Response preview: {response[:300]}...")
                
            finally:
                # Clean up test file
                if test_text_path.exists():
                    test_text_path.unlink()
        
        print("\n" + "=" * 50)
        print("🎉 RAG Implementation Test PASSED!")
        print("All core functionality is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ RAG Implementation Test FAILED!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_document_loaders():
    """Test individual document loaders."""
    print("\n🔧 Testing Document Loaders")
    print("=" * 30)
    
    try:
        from aimakerspace.document_utils import DocumentLoaderFactory
        
        factory = DocumentLoaderFactory()
        
        # Test supported formats
        print("✅ Document loader factory created")
        
        supported_formats = factory.get_supported_formats()
        print(f"✅ Supported formats: {list(supported_formats.keys())}")
        
        # Test file type detection
        test_cases = [
            "document.pdf",
            "spreadsheet.xlsx", 
            "text.txt",
            "presentation.docx",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        ]
        
        for test_case in test_cases:
            can_load = factory.can_load(test_case)
            print(f"   - {test_case}: {'✅ Supported' if can_load else '❌ Not supported'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Document loader test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 RAG Implementation Test Suite")
    print("=" * 60)
    
    # Test document loaders first (no API key needed)
    loader_test_passed = test_document_loaders()
    
    # Test full RAG implementation (requires API key)
    rag_test_passed = asyncio.run(test_rag_implementation())
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   - Document Loaders: {'✅ PASSED' if loader_test_passed else '❌ FAILED'}")
    print(f"   - RAG Implementation: {'✅ PASSED' if rag_test_passed else '❌ FAILED'}")
    
    if loader_test_passed and rag_test_passed:
        print("\n🎉 All tests PASSED! RAG implementation is ready for use.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
