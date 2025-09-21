"""
Example usage of the enhanced PDFLoader with security compliance.

This demonstrates how the loader handles different scenarios.
"""

from pathlib import Path
from aimakerspace.document_utils.pdf_utils import PDFLoader

def demonstrate_pdf_security():
    """Demonstrate the security-compliant PDF loading."""
    
    # Scenario 1: Regular non-protected PDFs (works as before)
    print("=== Scenario 1: Non-Protected PDFs ===")
    loader = PDFLoader("/path/to/mixed/pdfs")
    documents, skipped = loader.load_with_security_compliance("/path/to/mixed/pdfs")
    
    print(f"✅ Loaded {len(documents)} documents")
    print(f"⚠️  Skipped {len(skipped)} files")
    
    # Non-protected PDFs are in documents list
    for doc in documents:
        if not doc.metadata.get("is_encrypted", False):
            print(f"✅ Regular PDF processed: {doc.metadata.get('filename')}")
    
    # Scenario 2: Protected PDFs without password (skipped)
    print("\n=== Scenario 2: Protected PDFs (No Password) ===")
    for skip_info in skipped:
        if skip_info.get("is_encrypted"):
            print(f"⚠️  Skipped: {skip_info['filename']}")
            print(f"   Reason: {skip_info['skip_reason']}")
            print(f"   Message: {skip_info.get('user_message', 'N/A')}")
    
    # Scenario 3: Protected PDFs with password (processed)
    print("\n=== Scenario 3: Protected PDFs (With Password) ===")
    loader_with_password = PDFLoader("/path/to/mixed/pdfs", password="secret123")
    documents_with_pwd, skipped_with_pwd = loader_with_password.load_with_security_compliance("/path/to/mixed/pdfs")
    
    for doc in documents_with_pwd:
        if doc.metadata.get("is_encrypted", False):
            print(f"✅ Encrypted PDF processed: {doc.metadata.get('filename')}")
            print(f"   Security handled: {doc.metadata.get('security_handled')}")
            print(f"   Decryption time: {doc.metadata.get('decryption_timestamp')}")

def demonstrate_backward_compatibility():
    """Show that existing code still works."""
    
    print("=== Backward Compatibility ===")
    
    # Old way still works for non-protected PDFs
    loader = PDFLoader("/path/to/regular/pdfs")
    loader.load()  # This still works
    
    print(f"✅ Loaded {len(loader.documents)} documents using old method")
    
    # But for mixed directories with protected files, use new method
    documents, skipped = loader.load_with_security_compliance("/path/to/mixed/pdfs")
    print(f"✅ New method: {len(documents)} loaded, {len(skipped)} skipped")

def demonstrate_upfront_detection():
    """Show upfront encryption detection."""
    
    print("=== Upfront Detection ===")
    
    loader = PDFLoader("/path/to/pdfs")
    
    # Check a specific file before processing
    file_path = Path("/path/to/document.pdf")
    encryption_info = loader.check_encryption_status(file_path)
    
    if encryption_info["is_encrypted"]:
        print(f"🔒 File '{encryption_info['filename']}' is encrypted")
        print(f"   Size: {encryption_info['file_size']} bytes")
        print(f"   Requires password: {encryption_info['requires_password']}")
        print("   Action: Ask user for password before processing")
    else:
        print(f"🔓 File '{encryption_info['filename']}' is not encrypted")
        print("   Action: Can process normally")

if __name__ == "__main__":
    demonstrate_pdf_security()
    demonstrate_backward_compatibility()
    demonstrate_upfront_detection()
