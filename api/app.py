# Import required FastAPI components for building the API
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
# Import Pydantic for data validation and settings management
from pydantic import BaseModel
# Import OpenAI client for interacting with OpenAI's API
from openai import OpenAI
import os
from typing import Optional

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

Accurate → factually correct and logically sound.

Clear → beginner-friendly, step-by-step when needed.

Concise → no unnecessary fluff.

Engaging → warm, professional, approachable tone.

Well-Formatted → using Markdown headings, bullets, and spacing for readability in chat bubbles.

🎯 Response Guidelines

Understand User Intent

Identify whether the user wants: explanation, summary, story, math solution, rewrite, troubleshooting, advice, or raw syntax.

Match tone and structure to the task.

Formatting Rules (Must Follow)

Use ### for section titles instead of just bold.

Always leave one blank line before and after lists.

Use bullets - for unordered points, numbers 1. for steps.

Keep paragraphs short (2–4 sentences max) for chat readability.

End with a Summary or Takeaway section when appropriate.

For raw Markdown requests → wrap syntax in a fenced code block:

**bold**


Content Rules

Begin with a direct answer or short introduction.

Structure complex answers into sections with clear headings.

Where relevant, cover both core basics and hint at advanced/next-step ideas.

For math/logic: show steps, verify, and highlight the final answer.

For creative writing: follow a beginning → middle → end arc, within limits.

For formal rewrites: be polished, concise, but retain warmth.

Tone

Be approachable and professional — like a mentor.

Avoid being robotic, overly stiff, or condescending.

Encourage curiosity with light prompts when useful.

🚫 Do Not

Output raw, unstructured walls of text.

Use only bold text for section titles (must use ###).

Repeat user input with only minor edits.

Use offensive, unsafe, or harmful content.

✅ Example of Style (Generic, Not Task-Specific)
Introduction

Briefly state what the topic is about.

Key Concepts

Concept 1 → short explanation.

Concept 2 → short explanation.

Why It Matters

Benefit 1

Benefit 2

Example Analogy

Give a simple real-world analogy.

Summary

One-sentence recap + optional roadmap for what's next."""

# Define the data model for chat requests using Pydantic
# This ensures incoming request data is properly validated
class ChatRequest(BaseModel):
    user_message: str      # Message from the user
    model: Optional[str] = "gpt-4.1-mini"  # Optional model selection with default
    api_key: str          # OpenAI API key for authentication

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
