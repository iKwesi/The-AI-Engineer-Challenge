#!/usr/bin/env python3
"""
Simple script to run the RAG test with a real API key.
This will demonstrate the confidence threshold issue.
"""

import asyncio
import os
from test_rag_retrieval import RAGDebugger
from pathlib import Path

async def run_test():
    """Run the RAG test with actual API key."""
    
    # Get API key from environment or prompt user
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable or update this script with your API key")
        print("Example: export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Test document path
    test_doc = Path("docs/test-docs/quantumML.pdf")
    
    if not test_doc.exists():
        print(f"❌ Test document not found: {test_doc}")
        print("Please ensure quantumML.pdf exists in docs/test-docs/")
        return
    
    print("🚀 Starting RAG Retrieval Test")
    print("=" * 50)
    
    # Initialize debugger
    debugger = RAGDebugger(api_key)
    
    # Process document
    print("📄 Processing quantumML.pdf...")
    doc_result = await debugger.test_document_processing(test_doc)
    
    if not doc_result['success']:
        print("❌ Document processing failed!")
        return
    
    # Setup conversation mode
    print("\n💬 Setting up conversation mode...")
    conv_result = await debugger.test_conversation_mode()
    
    if not conv_result['success']:
        print("❌ Conversation mode setup failed!")
        return
    
    # Test the specific query that's failing
    test_query = "tell me about quantum machine learning"
    
    print(f"\n🔍 Testing query: '{test_query}'")
    print("-" * 50)
    
    # Test search functionality
    search_result = await debugger.test_search_functionality(test_query, k=5)
    
    if search_result['success']:
        print(f"\n📊 Search Results Analysis:")
        print(f"   - Found {search_result['results_count']} chunks")
        print(f"   - Top scores: {search_result['scores'][:3]}")
        
        # Test fallback detection
        fallback_result = await debugger.test_fallback_detection(test_query)
        
        if fallback_result.get('needs_fallback'):
            print(f"\n⚠️  FALLBACK TRIGGERED!")
            print(f"   - Confidence: {fallback_result.get('confidence_score', 0):.3f}")
            print(f"   - Explanation: {fallback_result.get('fallback_request', {}).get('explanation', 'N/A')}")
        else:
            print(f"\n✅ Query answered from documents")
            print(f"   - Confidence: {fallback_result.get('confidence_score', 0):.3f}")
    
    # Test different confidence thresholds
    print(f"\n🎯 Testing Different Confidence Thresholds")
    print("-" * 50)
    
    threshold_results = await debugger.test_confidence_thresholds(test_query)
    
    print(f"\nThreshold Analysis:")
    for threshold, result in threshold_results.items():
        if 'error' not in result:
            confidence = result['confidence_score']
            passes = result['passes_threshold']
            status = "✅ PASS" if passes else "❌ FAIL"
            print(f"   {threshold:.1f}: {status} (confidence: {confidence:.3f})")
    
    # Recommendations
    print(f"\n💡 Recommendations")
    print("=" * 50)
    
    # Find the highest confidence score
    max_confidence = 0
    for result in threshold_results.values():
        if 'confidence_score' in result:
            max_confidence = max(max_confidence, result['confidence_score'])
    
    # Set recommended threshold based on analysis
    if max_confidence < 0.7:
        recommended_threshold = min(0.6, max_confidence + 0.1)
        print(f"🔧 Current threshold (0.7) is too high!")
        print(f"   - Maximum confidence achieved: {max_confidence:.3f}")
        print(f"   - Recommended threshold: {recommended_threshold:.1f}")
        print(f"   - This would allow the query to be answered from documents")
    else:
        recommended_threshold = 0.6  # Conservative recommendation even if scores are good
        print(f"✅ Confidence scores look good (max: {max_confidence:.3f})")
        print(f"   - Recommended threshold: {recommended_threshold:.1f} (conservative)")
    
    print(f"\n📝 To fix this issue:")
    print(f"   1. Edit aimakerspace/processing_utils/conversation_mode_manager.py")
    print(f"   2. In ConversationModeManager.__init__(), change:")
    print(f"      confidence_threshold: float = 0.7")
    print(f"      to:")
    print(f"      confidence_threshold: float = {recommended_threshold:.1f}")

if __name__ == "__main__":
    asyncio.run(run_test())
