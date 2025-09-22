# Import required FastAPI components for building the API
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
# Import Pydantic for data validation and settings management
from pydantic import BaseModel
# Import OpenAI client for interacting with OpenAI's API
from openai import OpenAI
import os
import sys
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from io import BytesIO
import tempfile

# Add the parent directory to the path to import aimakerspace
sys.path.append(str(Path(__file__).parent.parent))

# Import aimakerspace utilities
from aimakerspace.document_utils import DocumentLoaderFactory
from aimakerspace.processing_utils.rag_service import RAGService
from aimakerspace.models import ChunkingConfig, ProcessingLimits
from aimakerspace.vectordatabase import VectorDatabase
from aimakerspace.openai_utils.embedding import EmbeddingModel
from aimakerspace.openai_utils.chatmodel import ChatOpenAI

# Initialize FastAPI application with a title
app = FastAPI(title="OpenAI Chat API")

# Configure CORS (Cross-Origin Resource Sharing) middleware
# This allows the API to be accessed from different domains/origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any origin
    allow_credentials=True,  # Allows cookies to be included in requests
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers in requests
)

# Custom exception handler for HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    from fastapi.responses import JSONResponse
    
    # If detail is a dict, return it directly
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    
    # Otherwise, wrap string detail in error format
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": str(exc.detail)}
    )

# Define the default system prompt for the AI assistant
DEFAULT_SYSTEM_PROMPT = """You are a helpful, expert AI assistant.  
Your mission is to always provide gold-standard responses that are:

- Accurate → factually correct, logically sound.  
- Clear → beginner-friendly, step by step when needed.  
- Concise → no unnecessary repetition.  
- Engaging → professional, warm, approachable.  
- Well-Formatted → using Markdown consistently so the frontend displays clean, structured answers.  

---

### Response Rules

1. Understand Intent  
   - Identify if the user wants an explanation, summary, story, math solution, rewrite, advice, or raw Markdown.  
   - Adapt style and depth to the request.  

2. Strict Formatting Rules (Must Follow)  
   - Use `###` for all section headings (not plain text).  
   - Always leave one blank line before and after lists or headings.  
   - Use bullets (`-`) for unordered lists.  
   - Use numbering (`1.`) for ordered steps.  
   - Keep paragraphs short (2–4 sentences max).  
   - End long answers with a **Summary** or **Takeaway** section.  
   - If the user explicitly asks for raw Markdown, wrap it inside a fenced code block:  
     ```markdown
     **bold**
     ```  

3. Mathematical Expressions (CRITICAL)  
   - ALWAYS use proper LaTeX notation for mathematical expressions.  
   - Use `$...$` for inline math: `$x = 5$`, `$\frac{1}{2}$`  
   - Use `$$...$$` for display math (centered, larger): `$$\frac{a}{b} = c$$`  
   - NEVER use parentheses `( )` or square brackets `[ ]` around math expressions.  
   - Examples of CORRECT formatting:  
     * `$x = 3$` (inline)  
     * `$$\text{Number of packs} = \frac{12}{4} = 3$$` (display)  
     * `$2x + 5 = 11$` (inline equation)  
   - Examples of INCORRECT formatting:  
     * `( x = 3 )` ❌  
     * `[ 2x + 5 = 11 ]` ❌  
     * `\frac{12}{4} = 3` (without delimiters) ❌  

4. Content Rules  
   - Begin with a short intro sentence before diving into details.  
   - Use clear section titles (`###`) for organization.  
   - For explanations, cover both basic ideas and, if relevant, mention advanced concepts briefly.  
   - For math/logic: show steps, verify, then present the final answer clearly using proper LaTeX.  
   - For stories: follow a beginning → middle → end arc within requested limits.  
   - For formal rewrites: professional, concise, and personable.  

5. Tone & Vibe  
   - Sound like a helpful mentor — approachable, never robotic or condescending.  
   - Adjust tone: formal when needed, light/playful for creative tasks.  

---

### Do Not
- Output plain-text headings — always use `###`.  
- Mix list styles (always use `-` for bullets, `1.` for steps).  
- Output unstructured walls of text.  
- Repeat user input with only small edits.  
- Use offensive or unsafe content.  
- Use parentheses `( )` or square brackets `[ ]` for mathematical expressions.  
- Output mathematical expressions without proper LaTeX delimiters.  

---

### Example Style (Generic Only)

### Introduction  
One line to introduce the topic.  

### Key Concepts  
- Concept 1 → short explanation.  
- Concept 2 → short explanation.  

### Why It Matters  
- Benefit 1  
- Benefit 2  

### Example Analogy  
One simple analogy in plain language.  

### Summary  
One or two lines wrapping up the explanation.  
"""

# Define the data models for requests using Pydantic
# This ensures incoming request data is properly validated
class ChatRequest(BaseModel):
    user_message: str      # Message from the user
    model: Optional[str] = "gpt-4.1-mini"  # Optional model selection with default
    api_key: str          # OpenAI API key for authentication

class RAGChatRequest(BaseModel):
    user_message: str      # Message from the user
    model: Optional[str] = "gpt-4.1-mini"  # Optional model selection with default
    api_key: str          # OpenAI API key for authentication
    use_context: bool = True  # Whether to use RAG context

class YouTubeRequest(BaseModel):
    youtube_url: str       # YouTube URL to process
    api_key: str          # OpenAI API key for authentication

class DocumentUploadResponse(BaseModel):
    status: str
    message: str
    chunks_processed: int
    filename: str

class BatchUploadFileResult(BaseModel):
    filename: str
    status: str
    message: str
    chunks_processed: int
    file_size: int

class BatchUploadResponse(BaseModel):
    status: str
    message: str
    total_files: int
    successful_files: int
    failed_files: int
    results: List[BatchUploadFileResult]
    entered_document_mode: bool

class YouTubeProcessResponse(BaseModel):
    status: str
    message: str
    video_title: str
    chunks_processed: int

class ErrorResponse(BaseModel):
    status: str
    message: str

# Conversation Mode Management Models
class ConversationModeRequest(BaseModel):
    api_key: str

class FallbackConfirmationRequest(BaseModel):
    query: str
    use_general_knowledge: bool
    api_key: str

class ConflictResolutionRequest(BaseModel):
    query: str
    selected_document_id: str
    confidence_scores: Dict[str, float]
    api_key: str

class ConversationModeResponse(BaseModel):
    status: str
    mode: str
    session_id: Optional[str]
    documents: List[Dict[str, Any]]
    message: str

class FallbackResponse(BaseModel):
    needs_fallback: bool
    fallback_request: Optional[Dict[str, Any]]
    response: Optional[str]
    citations: Optional[List[Dict[str, Any]]]
    confidence_score: float

class ConflictDetectionResponse(BaseModel):
    has_conflict: bool
    conflict_info: Optional[Dict[str, Any]]

# Global variables for RAG system - store per API key
rag_services: Dict[str, RAGService] = {}

# File size limit (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

def get_rag_service(api_key: str) -> RAGService:
    """Get or create RAG service instance for the given API key."""
    global rag_services
    
    # Create a hash of the API key for storage (for security)
    import hashlib
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    if api_key_hash not in rag_services:
        chunking_config = ChunkingConfig(chunk_size=1000, overlap=200)
        processing_limits = ProcessingLimits(max_file_size_mb=50)
        rag_services[api_key_hash] = RAGService(
            api_key=api_key,  # Use the actual API key passed from frontend
            chunking_config=chunking_config,
            processing_limits=processing_limits
        )
    return rag_services[api_key_hash]

# Define the main chat endpoint that handles POST requests
@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        # Initialize OpenAI client with the provided API key
        client = OpenAI(api_key=request.api_key)
        
        # Create an async generator function for streaming responses
        async def generate():
            # Create a streaming chat completion request with fixed system prompt
            stream = client.chat.completions.create(
                model=request.model,
                messages=[
                    {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                    {"role": "user", "content": request.user_message}
                ],
                stream=True  # Enable streaming response
            )
            
            # Yield each chunk of the response as it becomes available
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        # Return a streaming response to the client
        return StreamingResponse(generate(), media_type="text/plain")
    
    except Exception as e:
        # Handle any errors that occur during processing
        raise HTTPException(status_code=500, detail=str(e))

# RAG Chat endpoint with document context
@app.post("/api/rag-chat")
async def rag_chat(request: RAGChatRequest):
    try:
        rag = get_rag_service(request.api_key)
        
        if request.use_context and len(rag.processed_documents) > 0:
            # Use RAG with context
            response = await rag.chat_with_context(
                user_message=request.user_message,
                max_context_chunks=5
            )
            return {"response": response, "used_context": True}
        else:
            # Fall back to regular chat
            client = OpenAI(api_key=request.api_key)
            response = client.chat.completions.create(
                model=request.model,
                messages=[
                    {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                    {"role": "user", "content": request.user_message}
                ]
            )
            return {"response": response.choices[0].message.content, "used_context": False}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

# Document upload endpoint
@app.post("/api/upload-document", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    api_key: str = Form(...)
):
    try:
        # Check file size
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Process document with RAG service
            rag = get_rag_service(api_key)
            processed_doc = await rag.process_document(
                source=Path(tmp_file_path),
                document_id=file.filename,
                use_page_aware_chunking=True
            )
            
            return DocumentUploadResponse(
                status="success",
                message=f"Document '{file.filename}' processed successfully",
                chunks_processed=len(processed_doc.chunks),
                filename=file.filename
            )
        
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
    
    except Exception as e:
        # Return 400 for validation/processing errors, 500 for unexpected errors
        if "Unsupported file type" in str(e) or "Invalid" in str(e):
            raise HTTPException(status_code=400, detail={"status": "error", "message": str(e)})
        else:
            raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

# Multiple documents upload endpoint (batch processing)
@app.post("/api/upload-documents", response_model=BatchUploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    api_key: str = Form(...)
):
    try:
        # Validate that files were provided
        if not files:
            raise HTTPException(
                status_code=400,
                detail={"status": "error", "message": "No files provided"}
            )
        
        # Check total combined file size
        total_size = 0
        file_sizes = {}
        for file in files:
            if file.size:
                total_size += file.size
                file_sizes[file.filename] = file.size
        
        if total_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail={
                    "status": "error", 
                    "message": f"Combined file size too large. Maximum total size is {MAX_FILE_SIZE // (1024*1024)}MB, got {total_size // (1024*1024)}MB"
                }
            )
        
        # Initialize results tracking
        results = []
        successful_files = 0
        failed_files = 0
        rag = get_rag_service(api_key)
        
        # Process each file sequentially
        for file in files:
            file_result = BatchUploadFileResult(
                filename=file.filename,
                status="pending",
                message="",
                chunks_processed=0,
                file_size=file_sizes.get(file.filename, 0)
            )
            
            try:
                # Validate file type by extension
                file_extension = Path(file.filename).suffix.lower()
                processing_limits = ProcessingLimits()
                
                if not processing_limits.is_format_supported(file_extension):
                    file_result.status = "failed"
                    file_result.message = f"Unsupported file type: {file_extension}"
                    failed_files += 1
                    results.append(file_result)
                    continue
                
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                    content = await file.read()
                    tmp_file.write(content)
                    tmp_file_path = tmp_file.name
                
                try:
                    # Process document with RAG service
                    processed_doc = await rag.process_document(
                        source=Path(tmp_file_path),
                        document_id=file.filename,
                        use_page_aware_chunking=True
                    )
                    
                    file_result.status = "success"
                    file_result.message = f"Document '{file.filename}' processed successfully"
                    file_result.chunks_processed = len(processed_doc.chunks)
                    successful_files += 1
                
                finally:
                    # Clean up temporary file
                    os.unlink(tmp_file_path)
            
            except Exception as e:
                file_result.status = "failed"
                file_result.message = str(e)
                failed_files += 1
            
            results.append(file_result)
        
        # Auto-enter document mode if any files were successfully processed
        entered_document_mode = False
        if successful_files > 0:
            try:
                # Get all processed documents
                if rag.processed_documents:
                    # Convert processed documents to Document objects for conversation manager
                    documents = [doc.original_document for doc in rag.processed_documents.values()]
                    
                    # Enter document mode
                    session = rag.enter_document_mode(documents)
                    
                    # Update document chunks in session
                    for doc_id in rag.processed_documents.keys():
                        rag.update_document_chunks_in_session(doc_id)
                    
                    entered_document_mode = True
            except Exception as e:
                # Don't fail the entire batch if document mode entry fails
                pass
        
        # Determine overall status
        if successful_files == len(files):
            overall_status = "success"
            overall_message = f"All {successful_files} files processed successfully"
        elif successful_files > 0:
            overall_status = "partial_success"
            overall_message = f"{successful_files} of {len(files)} files processed successfully"
        else:
            overall_status = "failed"
            overall_message = "No files were processed successfully"
        
        if entered_document_mode and successful_files > 0:
            overall_message += ". Entered document mode automatically."
        
        return BatchUploadResponse(
            status=overall_status,
            message=overall_message,
            total_files=len(files),
            successful_files=successful_files,
            failed_files=failed_files,
            results=results,
            entered_document_mode=entered_document_mode
        )
    
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

# YouTube processing endpoint
@app.post("/api/process-youtube", response_model=YouTubeProcessResponse)
async def process_youtube(request: YouTubeRequest):
    try:
        rag = get_rag_service(request.api_key)
        
        # Process YouTube URL
        processed_doc = await rag.process_document(
            source=request.youtube_url,
            use_page_aware_chunking=False  # YouTube transcripts don't need page-aware chunking
        )
        
        # Extract video title from metadata
        video_title = processed_doc.original_document.metadata.get('video_title', 
                     processed_doc.original_document.metadata.get('title', 'Unknown Video'))
        
        return YouTubeProcessResponse(
            status="success",
            message=f"YouTube video processed successfully",
            video_title=video_title,
            chunks_processed=len(processed_doc.chunks)
        )
    
    except Exception as e:
        # Return 400 for validation/processing errors, 500 for unexpected errors
        if "Invalid YouTube URL" in str(e) or "Invalid" in str(e):
            raise HTTPException(status_code=400, detail={"status": "error", "message": str(e)})
        else:
            raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

# List processed documents
@app.get("/api/documents")
async def list_documents(api_key: str):
    try:
        rag = get_rag_service(api_key)
        documents = rag.list_documents()
        return {"documents": documents}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

# Remove document from vector database
@app.delete("/api/documents/{document_id}")
async def remove_document(document_id: str, api_key: str):
    try:
        rag = get_rag_service(api_key)
        success = rag.remove_document(document_id)
        
        if success:
            return {"status": "success", "message": f"Document '{document_id}' removed successfully"}
        else:
            raise HTTPException(status_code=404, detail={"status": "error", "message": f"Document '{document_id}' not found"})
    
    except HTTPException:
        # Re-raise HTTPException as-is (don't catch and convert to 500)
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

# Get RAG service statistics
@app.get("/api/rag-stats")
async def get_rag_stats(api_key: str):
    try:
        rag = get_rag_service(api_key)
        stats = rag.get_stats()
        return {"stats": stats}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

# Conversation Mode Management Endpoints

# Enter document mode (automatically triggered when documents are uploaded)
@app.post("/api/conversation/enter-document-mode", response_model=ConversationModeResponse)
async def enter_document_mode(request: ConversationModeRequest):
    try:
        print(f"DEBUG: Entering document mode for API key: {request.api_key[:10]}...")
        rag = get_rag_service(request.api_key)
        print(f"DEBUG: RAG service obtained, processed documents: {len(rag.processed_documents)}")
        
        # Get all processed documents
        if not rag.processed_documents:
            print("DEBUG: No processed documents found")
            raise HTTPException(
                status_code=400, 
                detail={"status": "error", "message": "No documents available. Please upload documents first."}
            )
        
        print(f"DEBUG: Converting {len(rag.processed_documents)} documents for conversation manager")
        # Convert processed documents to Document objects for conversation manager
        documents = [doc.original_document for doc in rag.processed_documents.values()]
        print(f"DEBUG: Documents converted: {[doc.document_id for doc in documents]}")
        
        # Enter document mode
        print("DEBUG: Calling enter_document_mode on RAG service")
        session = rag.enter_document_mode(documents)
        print(f"DEBUG: Document mode entered, session: {session.session_id}, mode: {session.mode}")
        
        # Update document chunks in session
        print("DEBUG: Updating document chunks in session")
        for doc_id in rag.processed_documents.keys():
            rag.update_document_chunks_in_session(doc_id)
        print("DEBUG: Document chunks updated")
        
        return ConversationModeResponse(
            status="success",
            mode=session.mode.value,
            session_id=session.session_id,
            documents=list(session.documents.values()) if hasattr(session, 'documents') else [],
            message="Entered document mode. Your queries will now be answered using your uploaded documents."
        )
    
    except HTTPException as e:
        print(f"DEBUG: HTTPException in enter_document_mode: {e}")
        raise
    except Exception as e:
        print(f"DEBUG: Exception in enter_document_mode: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

# Exit document mode
@app.post("/api/conversation/exit-document-mode", response_model=ConversationModeResponse)
async def exit_document_mode(request: ConversationModeRequest):
    try:
        rag = get_rag_service(request.api_key)
        session = rag.exit_document_mode()
        
        return ConversationModeResponse(
            status="success",
            mode=session.mode.value,
            session_id=session.session_id,
            documents=[],
            message="Exited document mode. Your queries will now use general knowledge."
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

# Get conversation status
@app.get("/api/conversation/status")
async def get_conversation_status(api_key: str):
    try:
        rag = get_rag_service(api_key)
        status = rag.get_conversation_status()
        return {"status": "success", "conversation_status": status}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

# Enhanced RAG chat with fallback detection
@app.post("/api/conversation/chat", response_model=FallbackResponse)
async def conversation_chat(request: RAGChatRequest):
    try:
        print(f"DEBUG: Conversation chat request for API key: {request.api_key[:10]}...")
        rag = get_rag_service(request.api_key)
        print(f"DEBUG: RAG service obtained")
        
        # Check if we're in document mode
        print("DEBUG: Getting conversation status")
        conversation_status = rag.get_conversation_status()
        print(f"DEBUG: Conversation status: {conversation_status}")
        
        if conversation_status['mode'] == 'document' and conversation_status['session_active']:
            print("DEBUG: In document mode, using RAG with fallback detection")
            # Use conversation mode with fallback detection
            result = await rag.query_with_fallback(
                query=request.user_message,
                max_context_chunks=5
            )
            print(f"DEBUG: RAG query result: needs_fallback={result.get('needs_fallback')}")
            
            return FallbackResponse(
                needs_fallback=result['needs_fallback'],
                fallback_request=result.get('fallback_request'),
                response=result.get('response'),
                citations=result.get('citations'),
                confidence_score=result.get('confidence_score', 0.0)
            )
        else:
            print("DEBUG: Not in document mode, using regular chat")
            # Regular chat mode
            client = OpenAI(api_key=request.api_key)
            response = client.chat.completions.create(
                model=request.model,
                messages=[
                    {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                    {"role": "user", "content": request.user_message}
                ]
            )
            
            return FallbackResponse(
                needs_fallback=False,
                fallback_request=None,
                response=response.choices[0].message.content,
                citations=None,
                confidence_score=1.0
            )
    
    except Exception as e:
        print(f"DEBUG: Exception in conversation_chat: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

# Handle fallback confirmation
@app.post("/api/conversation/fallback-confirm")
async def confirm_fallback(request: FallbackConfirmationRequest):
    try:
        rag = get_rag_service(request.api_key)
        
        if request.use_general_knowledge:
            # User confirmed to use general knowledge
            client = OpenAI(api_key=request.api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                    {"role": "user", "content": request.query}
                ]
            )
            
            return {
                "status": "success",
                "response": f"Note: this answer is not grounded in your uploaded document.\n\n{response.choices[0].message.content}",
                "used_general_knowledge": True
            }
        else:
            # User declined, stay in document mode
            return {
                "status": "success",
                "message": "Staying in document mode. Please try rephrasing your question or ask about content in your documents.",
                "used_general_knowledge": False
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

# Detect multi-document conflicts
@app.post("/api/conversation/detect-conflicts", response_model=ConflictDetectionResponse)
async def detect_conflicts(request: RAGChatRequest):
    try:
        rag = get_rag_service(request.api_key)
        
        # Check if we're in document mode with multiple documents
        conversation_status = rag.get_conversation_status()
        
        if (conversation_status['mode'] != 'document' or 
            not conversation_status['session_active'] or 
            len(conversation_status['documents']) < 2):
            
            return ConflictDetectionResponse(
                has_conflict=False,
                conflict_info=None
            )
        
        # Detect conflicts
        conflict_info = await rag.detect_multi_document_conflicts(
            query=request.user_message,
            max_context_chunks=5
        )
        
        return ConflictDetectionResponse(
            has_conflict=conflict_info is not None,
            conflict_info=conflict_info
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

# Resolve multi-document conflicts
@app.post("/api/conversation/resolve-conflict")
async def resolve_conflict(request: ConflictResolutionRequest):
    try:
        rag = get_rag_service(request.api_key)
        
        # Record the user's resolution
        resolution = rag.resolve_conflict(
            query=request.query,
            selected_document_id=request.selected_document_id,
            confidence_scores=request.confidence_scores
        )
        
        # Now answer the query using the selected document
        search_result = await rag.search(
            query=request.query,
            k=5,
            filters={'source_document_id': request.selected_document_id}
        )
        
        # Generate response with context from selected document
        response = await rag.chat_with_context(
            user_message=request.query,
            max_context_chunks=5
        )
        
        # Build citations from selected document
        citations = []
        for chunk in search_result.chunks:
            doc_info = rag.get_document_info(chunk.source_document_id)
            citations.append({
                'chunk_id': chunk.chunk_id,
                'document_name': doc_info['filename'] if doc_info else 'Unknown',
                'document_id': chunk.source_document_id,
                'content_preview': chunk.content[:200] + '...' if len(chunk.content) > 200 else chunk.content
            })
        
        return {
            "status": "success",
            "resolution": resolution,
            "response": response,
            "citations": citations,
            "message": f"Answered using {resolution['selected_document_name']}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

# Define a health check endpoint to verify API status
@app.get("/api/health")
async def health_check():
    from datetime import datetime
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Entry point for running the application directly
if __name__ == "__main__":
    import uvicorn
    # Start the server on all network interfaces (0.0.0.0) on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
