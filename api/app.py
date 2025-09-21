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
from aimakerspace.text_utils import TextFileLoader, PDFLoader, CharacterTextSplitter
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

class YouTubeProcessResponse(BaseModel):
    status: str
    message: str
    video_title: str
    chunks_processed: int

# Global variables for RAG system
vector_db: Optional[VectorDatabase] = None
embedding_model: Optional[EmbeddingModel] = None
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

# File size limit (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

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

# Define a health check endpoint to verify API status
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Entry point for running the application directly
if __name__ == "__main__":
    import uvicorn
    # Start the server on all network interfaces (0.0.0.0) on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
