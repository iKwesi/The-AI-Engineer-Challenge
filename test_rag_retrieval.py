#!/usr/bin/env python3
"""
Test script to debug RAG retrieval issues with quantumML.pdf

This script directly tests the RAG implementation to identify why
"quantum machine learning" queries are not finding relevant content
even when the document contains that information.
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add the current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from aimakerspace.processing_utils.rag_service import RAGService
from aimakerspace.models import ChunkingConfig, ProcessingLimits


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


async def main():
    """Main test function."""
    print("🔍 RAG Retrieval Debug Test")
    print("=" * 50)
    
    # Configuration
    API_KEY = "test-api-key-for-debugging"  # Replace with actual API key if needed
    TEST_DOCUMENT = Path("docs/test-docs/quantumML.pdf")
    TEST_QUERIES = [
        "quantum machine learning",
        "tell me about quantum machine learning",
        "what is quantum ML",
        "quantum computing and machine learning",
        "quantum algorithms"
    ]
    
    # Check if test document exists
    if not TEST_DOCUMENT.exists():
        print(f"❌ Test document not found: {TEST_DOCUMENT}")
        print("Please ensure the quantumML.pdf file exists in docs/test-docs/")
        return
    
    # Initialize debugger
    debugger = RAGDebugger(API_KEY)
    
    # Test 1: Document Processing
    doc_result = await debugger.test_document_processing(TEST_DOCUMENT)
    if not doc_result['success']:
        print("❌ Cannot proceed - document processing failed")
        return
    
    # Test 2: Vector Database Inspection
    db_info = debugger.inspect_vector_database()
    
    # Test 3: Conversation Mode Setup
    conv_result = await debugger.test_conversation_mode()
    if not conv_result['success']:
        print("❌ Cannot proceed - conversation mode setup failed")
        return
    
    # Test 4: Search Functionality for each query
    for query in TEST_QUERIES:
        search_result = await debugger.test_search_functionality(query)
        
        if search_result['success']:
            # Test 5: Fallback Detection
            fallback_result = await debugger.test_fallback_detection(query)
            
            # Test 6: Confidence Threshold Analysis
            threshold_results = await debugger.test_confidence_thresholds(query)
            
            print(f"\n--- Threshold Analysis Summary for '{query}' ---")
            for threshold, result in threshold_results.items():
                if 'error' not in result:
                    status = "✅ PASS" if result['passes_threshold'] else "❌ FAIL"
                    print(f"Threshold {threshold}: {status} (confidence: {result['confidence_score']:.4f})")
    
    print(f"\n🎯 Debug Summary")
    print("=" * 50)
    print("1. Check the confidence scores above")
    print("2. Look for the threshold where queries start passing")
    print("3. Consider lowering the default threshold in ConversationModeManager")
    print("4. Review chunk content to ensure relevant information is captured")
    print("\nRecommendation: If confidence scores are consistently below 0.7,")
    print("consider lowering the threshold to 0.4-0.5 for better retrieval.")


if __name__ == "__main__":
    asyncio.run(main())
