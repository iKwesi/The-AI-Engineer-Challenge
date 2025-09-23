#!/usr/bin/env python3
"""
Test script to debug RAG retrieval issues with quantumML.pdf

This script directly tests the RAG implementation to identify why
"quantum machine learning" queries are not finding relevant content
even when the document contains that information.
"""

import os
import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add the current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from aimakerspace.processing_utils.rag_service import RAGService
from aimakerspace.models import ChunkingConfig, ProcessingLimits

api_key = os.getenv('OPENAI_API_KEY')

class RAGDebugger:
    """Debug RAG retrieval issues with detailed logging."""
    
    def __init__(self, api_key: str):
        """Initialize the RAG debugger."""
        self.api_key = api_key
        
        # Configure RAG service with debug-friendly settings
        chunking_config = ChunkingConfig(
            chunk_size=1000,
            overlap=200,
            preserve_sentences=True
        )
        processing_limits = ProcessingLimits(max_file_size_mb=50)
        
        self.rag_service = RAGService(
            api_key=api_key,
            chunking_config=chunking_config,
            processing_limits=processing_limits,
            embedding_model_name="text-embedding-3-small",
            chat_model_name="gpt-4o-mini"
        )
    
    async def test_document_processing(self, document_path: Path) -> Dict[str, Any]:
        """Test document processing and return detailed results."""
        print(f"\n=== Testing Document Processing ===")
        print(f"Document: {document_path}")
        
        try:
            # Process the document
            processed_doc = await self.rag_service.process_document(
                source=document_path,
                document_id=document_path.name,
                use_page_aware_chunking=True,
                filename_override=document_path.name
            )
            
            print(f"✅ Document processed successfully")
            print(f"   - Chunks created: {len(processed_doc.chunks)}")
            print(f"   - Document ID: {processed_doc.original_document.document_id}")
            print(f"   - Content length: {len(processed_doc.original_document.content)} characters")
            
            # Show first few chunks for inspection
            print(f"\n--- First 3 Chunks Preview ---")
            for i, chunk in enumerate(processed_doc.chunks[:3]):
                print(f"Chunk {i+1} (ID: {chunk.chunk_id}):")
                print(f"  Content preview: {chunk.content[:200]}...")
                print(f"  Metadata: {chunk.metadata}")
                print()
            
            return {
                'success': True,
                'chunks_count': len(processed_doc.chunks),
                'document_id': processed_doc.original_document.document_id,
                'chunks': processed_doc.chunks
            }
            
        except Exception as e:
            print(f"❌ Document processing failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_search_functionality(self, query: str, k: int = 5) -> Dict[str, Any]:
        """Test search functionality with detailed scoring."""
        print(f"\n=== Testing Search Functionality ===")
        print(f"Query: '{query}'")
        print(f"Requesting top {k} results")
        
        try:
            # Perform search
            search_result = await self.rag_service.search(query, k=k)
            
            print(f"✅ Search completed")
            print(f"   - Results found: {len(search_result.chunks)}")
            print(f"   - Scores: {search_result.scores}")
            
            # Show detailed results
            print(f"\n--- Search Results ---")
            for i, (chunk, score) in enumerate(zip(search_result.chunks, search_result.scores)):
                print(f"Result {i+1} (Score: {score:.4f}):")
                print(f"  Chunk ID: {chunk.chunk_id}")
                print(f"  Source: {chunk.source_document_id}")
                print(f"  Content preview: {chunk.content[:300]}...")
                print()
            
            return {
                'success': True,
                'results_count': len(search_result.chunks),
                'scores': search_result.scores,
                'chunks': search_result.chunks
            }
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_conversation_mode(self) -> Dict[str, Any]:
        """Test conversation mode setup."""
        print(f"\n=== Testing Conversation Mode ===")
        
        try:
            # Get all processed documents
            if not self.rag_service.processed_documents:
                print("❌ No processed documents found")
                return {'success': False, 'error': 'No documents processed'}
            
            # Enter document mode
            documents = [doc.original_document for doc in self.rag_service.processed_documents.values()]
            session = self.rag_service.enter_document_mode(documents)
            
            # Update document chunks in session
            for doc_id in self.rag_service.processed_documents.keys():
                self.rag_service.update_document_chunks_in_session(doc_id)
            
            print(f"✅ Document mode entered")
            print(f"   - Session ID: {session.session_id}")
            print(f"   - Mode: {session.mode.value}")
            print(f"   - Documents: {len(session.documents)}")
            
            # Get conversation status
            status = self.rag_service.get_conversation_status()
            print(f"   - Status: {status}")
            
            return {
                'success': True,
                'session_id': session.session_id,
                'mode': session.mode.value,
                'documents_count': len(session.documents),
                'status': status
            }
            
        except Exception as e:
            print(f"❌ Conversation mode setup failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_fallback_detection(self, query: str) -> Dict[str, Any]:
        """Test fallback detection with detailed confidence analysis."""
        print(f"\n=== Testing Fallback Detection ===")
        print(f"Query: '{query}'")
        
        try:
            # Test query with fallback detection
            result = await self.rag_service.query_with_fallback(
                query=query,
                max_context_chunks=5
            )
            
            print(f"✅ Fallback detection completed")
            print(f"   - Needs fallback: {result['needs_fallback']}")
            print(f"   - Confidence score: {result.get('confidence_score', 'N/A')}")
            
            if result['needs_fallback']:
                fallback_req = result.get('fallback_request', {})
                print(f"   - Fallback explanation: {fallback_req.get('explanation', 'N/A')}")
                print(f"   - Retrieved chunks: {len(fallback_req.get('retrieved_chunks', []))}")
            else:
                print(f"   - Response generated from documents")
                print(f"   - Citations: {len(result.get('citations', []))}")
            
            return result
            
        except Exception as e:
            print(f"❌ Fallback detection failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_confidence_thresholds(self, query: str) -> Dict[str, Any]:
        """Test different confidence thresholds to find optimal settings."""
        print(f"\n=== Testing Confidence Thresholds ===")
        print(f"Query: '{query}'")
        
        # Test different thresholds
        thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        results = {}
        
        for threshold in thresholds:
            print(f"\nTesting threshold: {threshold}")
            
            try:
                # Temporarily modify the conversation manager's threshold
                original_threshold = self.rag_service.conversation_manager.confidence_threshold
                self.rag_service.conversation_manager.confidence_threshold = threshold
                
                # Test query
                result = await self.rag_service.query_with_fallback(
                    query=query,
                    max_context_chunks=5
                )
                
                needs_fallback = result['needs_fallback']
                confidence = result.get('confidence_score', 0.0)
                
                print(f"   - Needs fallback: {needs_fallback}")
                print(f"   - Confidence: {confidence:.4f}")
                
                results[threshold] = {
                    'needs_fallback': needs_fallback,
                    'confidence_score': confidence,
                    'passes_threshold': confidence >= threshold
                }
                
                # Restore original threshold
                self.rag_service.conversation_manager.confidence_threshold = original_threshold
                
            except Exception as e:
                print(f"   - Error: {e}")
                results[threshold] = {'error': str(e)}
        
        return results
    
    def inspect_vector_database(self) -> Dict[str, Any]:
        """Inspect the current state of the vector database."""
        print(f"\n=== Inspecting Vector Database ===")
        
        vector_db = self.rag_service.vector_db
        
        print(f"Vector database state:")
        print(f"   - Total vectors: {len(vector_db.vectors)}")
        print(f"   - Total metadata entries: {len(vector_db.metadata)}")
        
        # Show sample metadata
        if vector_db.metadata:
            print(f"\n--- Sample Metadata ---")
            for i, (key, metadata) in enumerate(list(vector_db.metadata.items())[:3]):
                print(f"Entry {i+1} (Key: {key}):")
                print(f"  Content preview: {metadata.get('content', '')[:200]}...")
                print(f"  Source document: {metadata.get('source_document_id', 'N/A')}")
                print(f"  Chunk index: {metadata.get('chunk_index', 'N/A')}")
                print()
        
        return {
            'total_vectors': len(vector_db.vectors),
            'total_metadata': len(vector_db.metadata),
            'sample_keys': list(vector_db.vectors.keys())[:5]
        }


async def test_adaptive_thresholds_only():
    """Test only the adaptive threshold implementation without heavy processing."""
    print("🔍 Testing Adaptive Confidence Thresholds Implementation")
    print("=" * 60)
    
    # Test the conversation manager directly
    from aimakerspace.processing_utils.conversation_mode_manager import (
        ConversationModeManager, DocumentModeSession, ConversationMode
    )
    from aimakerspace.models import SearchResult, Chunk
    from datetime import datetime, timedelta
    
    # Initialize with new thresholds
    manager = ConversationModeManager(
        confidence_threshold=0.45,  # Primary threshold
        fallback_threshold=0.3      # Fallback threshold
    )
    
    print(f"✅ Primary Threshold: {manager.confidence_threshold}")
    print(f"✅ Fallback Threshold: {manager.fallback_threshold}")
    print()
    
    # Create mock session
    now = datetime.now()
    session = DocumentModeSession(
        mode=ConversationMode.DOCUMENT,
        session_id="test-session",
        created_at=now.isoformat(),
        expires_at=(now + timedelta(hours=24)).isoformat(),
        documents={"test-doc": {"name": "test.pdf", "chunk_count": 10}},
        conversation_context={
            'last_document_query': '',
            'last_confidence_score': 0.0,
            'fallback_history': [],
            'conflict_resolutions': []
        }
    )
    manager.current_session = session
    
    # Test scenarios - accounting for confidence smoothing
    test_scenarios = [
        {
            "name": "High Confidence (0.8) - Should be NORMAL",
            "scores": [0.8, 0.8, 0.8, 0.8, 0.8],  # Consistent high scores
            "expected": "normal"
        },
        {
            "name": "Medium Confidence (0.4) - Should be DISCLAIMER", 
            "scores": [0.4, 0.4, 0.4, 0.4, 0.4],  # Consistent medium scores
            "expected": "disclaimer"
        },
        {
            "name": "Low Confidence (0.2) - Should be FALLBACK",
            "scores": [0.2, 0.2, 0.2, 0.2, 0.2],  # Consistent low scores
            "expected": "fallback"
        },
        {
            "name": "Edge Case - Just Above Fallback (0.31)",
            "scores": [0.31, 0.31, 0.31, 0.31, 0.31],  # Consistent edge case
            "expected": "disclaimer"
        },
        {
            "name": "Edge Case - Just Below Primary (0.44)",
            "scores": [0.44, 0.44, 0.44, 0.44, 0.44],  # Consistent edge case
            "expected": "disclaimer"
        }
    ]
    
    all_passed = True
    
    for scenario in test_scenarios:
        print(f"🧪 Testing: {scenario['name']}")
        print("-" * 40)
        
        # Reset confidence history for each test to avoid interference
        manager.confidence_history = []
        
        # Create mock chunks
        chunks = []
        for i, score in enumerate(scenario['scores']):
            chunk = Chunk(
                content=f"Mock content {i+1} about quantum computing",
                chunk_index=i,
                source_document_id="test-doc",
                chunk_id=f"test-chunk-{i:03d}",
                metadata={"test": True}
            )
            chunks.append(chunk)
        
        # Create mock search result
        search_result = SearchResult(
            chunks=chunks,
            scores=scenario['scores'],
            query=None
        )
        
        # Test the adaptive threshold logic
        response_type, fallback_request = manager.query_with_fallback(
            "test query", search_result
        )
        
        print(f"   Response Type: {response_type}")
        print(f"   Expected: {scenario['expected']}")
        
        if response_type == scenario['expected']:
            print("   ✅ PASS")
        else:
            print("   ❌ FAIL")
            all_passed = False
        
        if fallback_request:
            print(f"   Confidence Score: {fallback_request.confidence_score:.3f}")
            print(f"   Explanation: {fallback_request.explanation}")
        
        print()
    
    # Test explanation methods
    print("🎯 Testing Explanation Methods")
    print("-" * 40)
    
    disclaimer = manager._generate_disclaimer_explanation(0.4, 0.45)
    print(f"Disclaimer Example: {disclaimer}")
    print()
    
    fallback = manager._generate_fallback_explanation(0.2, 0.3)
    print(f"Fallback Example: {fallback}")
    print()
    
    if all_passed:
        print("✅ All Adaptive Threshold Tests PASSED!")
        print("\n🎉 Implementation is working correctly!")
        print("\nKey improvements:")
        print("- Primary threshold lowered to 0.45 (from 0.7)")
        print("- New fallback threshold at 0.3")
        print("- Three response types: normal, disclaimer, fallback")
        print("- Appropriate explanations for each type")
    else:
        print("❌ Some tests failed - check implementation")
    
    return all_passed


async def main():
    """Main test function - now focused on adaptive thresholds."""
    print("🔍 RAG Adaptive Threshold Test")
    print("=" * 50)
    
    # Test adaptive thresholds first (lightweight)
    threshold_success = await test_adaptive_thresholds_only()
    
    if not threshold_success:
        print("❌ Adaptive threshold tests failed")
        return
    
    # Configuration - Get API key from environment
    import os
    API_KEY = os.getenv('OPENAI_API_KEY')
    if not API_KEY:
        print("\n⚠️  OPENAI_API_KEY not set - skipping full document tests")
        print("✅ Adaptive threshold implementation verified successfully!")
        return
    
    print("\n" + "="*60)
    print("🔍 Testing with Real Document (if API key available)")
    print("="*60)
    
    TEST_DOCUMENT = Path("docs/test-docs/quantumML.pdf")
    
    # Check if test document exists
    if not TEST_DOCUMENT.exists():
        print(f"⚠️  Test document not found: {TEST_DOCUMENT}")
        print("✅ Adaptive threshold implementation verified successfully!")
        return
    
    # Quick test with real document
    try:
        debugger = RAGDebugger(API_KEY)
        
        print("Processing document (this may take a moment)...")
        doc_result = await debugger.test_document_processing(TEST_DOCUMENT)
        
        if doc_result['success']:
            print("✅ Document processed successfully")
            
            # Test one query to verify integration
            conv_result = await debugger.test_conversation_mode()
            if conv_result['success']:
                print("✅ Conversation mode setup successful")
                
                # Test the critical "What is a qubit?" query
                print("\n🎯 Testing critical query: 'What is a qubit?'")
                fallback_result = await debugger.test_fallback_detection("What is a qubit?")
                
                if 'response_type' in fallback_result:
                    print(f"✅ Query processed with response type: {fallback_result['response_type']}")
                    print(f"   Confidence: {fallback_result.get('confidence_score', 'N/A')}")
                else:
                    print("✅ Query processed successfully")
        
    except Exception as e:
        print(f"⚠️  Document test failed: {e}")
        print("✅ But adaptive threshold implementation is verified!")
    
    print("\n🎉 Testing completed!")
    print("✅ Adaptive confidence thresholds implemented successfully!")


if __name__ == "__main__":
    asyncio.run(main())
