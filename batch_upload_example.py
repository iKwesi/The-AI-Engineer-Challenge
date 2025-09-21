"""
Example demonstrating batch PDF upload with cumulative size validation.

This shows how multiple PDFs can be uploaded together as long as their
total size doesn't exceed the maximum limit.
"""

from pathlib import Path
from aimakerspace.document_utils.pdf_utils import PDFLoader
from aimakerspace.models import ProcessingLimits, FileTooLargeError

def demonstrate_batch_upload_scenarios():
    """Demonstrate different batch upload scenarios."""
    
    print("=== Batch PDF Upload Scenarios ===\n")
    
    # Scenario 1: ✅ Multiple small PDFs within limit
    print("Scenario 1: Multiple Small PDFs (SHOULD WORK)")
    print("Files:")
    print("  - report1.pdf (8MB)")
    print("  - report2.pdf (12MB)")  
    print("  - summary.pdf (5MB)")
    print("  - analysis.pdf (15MB)")
    print("  Total: 40MB (within 50MB limit)")
    
    try:
        # This would work - 40MB total is under 50MB limit
        loader = PDFLoader("/path/to/small/pdfs")
        documents, skipped = loader.load_with_security_compliance(
            "/path/to/small/pdfs", 
            validate_batch_size=True
        )
        print("✅ Result: All 4 PDFs processed successfully")
        print(f"   Loaded: {len(documents)} documents")
        print(f"   Skipped: {len(skipped)} files\n")
        
    except FileTooLargeError as e:
        print(f"❌ Batch rejected: {e}\n")
    
    # Scenario 2: ❌ Multiple PDFs exceeding limit
    print("Scenario 2: Multiple Large PDFs (SHOULD FAIL)")
    print("Files:")
    print("  - large1.pdf (20MB)")
    print("  - large2.pdf (18MB)")
    print("  - large3.pdf (15MB)")
    print("  Total: 53MB (exceeds 50MB limit)")
    
    try:
        loader = PDFLoader("/path/to/large/pdfs")
        documents, skipped = loader.load_with_security_compliance(
            "/path/to/large/pdfs",
            validate_batch_size=True
        )
        print("✅ Result: Processed successfully")
        
    except FileTooLargeError as e:
        print(f"❌ Batch rejected: {e}")
        print("   Solution: Upload fewer files or compress PDFs\n")
    
    # Scenario 3: ✅ Mixed with individual file validation disabled
    print("Scenario 3: Custom Limits")
    print("Files:")
    print("  - doc1.pdf (15MB)")
    print("  - doc2.pdf (15MB)")
    print("  - doc3.pdf (15MB)")
    print("  Total: 45MB")
    print("  Custom limit: 100MB")
    
    try:
        # Custom processing limits
        custom_limits = ProcessingLimits(max_file_size_mb=100)
        loader = PDFLoader("/path/to/docs", processing_limits=custom_limits)
        
        documents, skipped = loader.load_with_security_compliance(
            "/path/to/docs",
            validate_batch_size=True
        )
        print("✅ Result: All PDFs processed with custom 100MB limit")
        print(f"   Loaded: {len(documents)} documents\n")
        
    except FileTooLargeError as e:
        print(f"❌ Batch rejected: {e}\n")

def demonstrate_api_usage():
    """Show how this would work in an API context."""
    
    print("=== API Usage Example ===\n")
    
    # Simulating multiple file upload
    uploaded_files = [
        {"filename": "contract.pdf", "size_mb": 12},
        {"filename": "proposal.pdf", "size_mb": 8},
        {"filename": "terms.pdf", "size_mb": 15},
        {"filename": "appendix.pdf", "size_mb": 10},
    ]
    
    total_size = sum(f["size_mb"] for f in uploaded_files)
    max_size = 50  # MB
    
    print(f"📁 Files uploaded: {len(uploaded_files)}")
    for f in uploaded_files:
        print(f"   - {f['filename']} ({f['size_mb']}MB)")
    print(f"📊 Total size: {total_size}MB")
    print(f"📏 Limit: {max_size}MB")
    
    if total_size <= max_size:
        print("✅ Batch accepted - processing PDFs...")
        
        # In real API, you would:
        # 1. Save uploaded files to temp directory
        # 2. Use PDFLoader with batch validation
        # 3. Process all files together
        # 4. Return results
        
        print("   Step 1: Save files to temp directory")
        print("   Step 2: Run batch validation")
        print("   Step 3: Process each PDF")
        print("   Step 4: Return success/failure for each file")
        
    else:
        print(f"❌ Batch rejected - {total_size}MB exceeds {max_size}MB limit")
        print("   Response: Ask user to upload fewer files")

def demonstrate_progressive_upload():
    """Show progressive upload strategy."""
    
    print("\n=== Progressive Upload Strategy ===\n")
    
    all_files = [
        {"name": "file1.pdf", "size": 15},
        {"name": "file2.pdf", "size": 12},
        {"name": "file3.pdf", "size": 18},
        {"name": "file4.pdf", "size": 8},
        {"name": "file5.pdf", "size": 22},
    ]
    
    max_batch_size = 50  # MB
    current_batch = []
    current_size = 0
    batch_num = 1
    
    print("📁 Files to upload:")
    for f in all_files:
        print(f"   - {f['name']} ({f['size']}MB)")
    
    print(f"\n📏 Max batch size: {max_batch_size}MB")
    print("\n🔄 Progressive batching:")
    
    for file in all_files:
        if current_size + file["size"] <= max_batch_size:
            current_batch.append(file)
            current_size += file["size"]
        else:
            # Process current batch
            if current_batch:
                print(f"   Batch {batch_num}: {len(current_batch)} files, {current_size}MB")
                for f in current_batch:
                    print(f"     - {f['name']}")
                batch_num += 1
            
            # Start new batch
            current_batch = [file]
            current_size = file["size"]
    
    # Process final batch
    if current_batch:
        print(f"   Batch {batch_num}: {len(current_batch)} files, {current_size}MB")
        for f in current_batch:
            print(f"     - {f['name']}")
    
    print(f"\n✅ Solution: Upload in {batch_num} separate batches")

if __name__ == "__main__":
    demonstrate_batch_upload_scenarios()
    demonstrate_api_usage()
    demonstrate_progressive_upload()
