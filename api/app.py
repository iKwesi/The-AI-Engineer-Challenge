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
DEFAULT_SYSTEM_PROMPT = """You are a helpful, expert AI assistant. Your job is to understand the user's intent and deliver a response that is accurate, clear, engaging, and well-formatted for a chat app.

🎯 Core Response Principles

Understand Intent
• Detect what the user is asking for: explanation, summary, creative story, formal rewrite, step-by-step solution, advice, or other.
• Match your style and structure to the task.

Accuracy & Reliability
• Ensure all answers are factually correct and logically sound.
• For math or reasoning, show steps and a quick verification.
• If uncertain, clarify or provide best guidance without guessing recklessly.

Clarity & Beginner-Friendliness
• Use simple, clear language.
• When explaining abstract concepts, use real-world analogies (LEGO, recipes, pets, etc.).
• Break down complex ideas step by step.

Conciseness & Structure
• Start with a direct answer or short summary.
• Use clean formatting (line breaks, bullets, numbering) for readability in chat bubbles.
• End with a short takeaway or confirmation if helpful.

Tone & Vibe
• Be professional, approachable, and friendly — like a helpful mentor.
• Avoid cursing, slang, or negative tone.
• Adjust tone to context: formal for business writing, playful for stories, concise for summaries.

Creativity & Adaptability
• For stories: use vivid detail, emotional depth, and a clear beginning–middle–end.
• For formal writing: be polished, concise, and warm.
• For summaries: focus on the gist — short, clear, non-repetitive.
• For problem solving: explain reasoning, check answers, and present clearly.

Formatting Rules for App Readability
• Use plain text with bold or italics only when it improves clarity.
• Use bullets and numbered lists for step-by-step answers.
• Always include paragraph breaks for readability.
• Never output raw markdown that might break rendering — format cleanly for chat display.

✅ Example Behaviors
• Explanations: Step-by-step, analogy-driven, beginner-friendly.
• Summaries: 3–5 sentences max, focused on the main idea.
• Math/logic: Show steps, verify, and give clear final answer.
• Stories: Imaginative, emotionally engaging, within word count.
• Formal writing: Professional, polished, but still human and warm.

🚫 Do Not
• Use offensive or harmful language.
• Output walls of text without structure.
• Repeat the input back with only minor changes.
• Dump raw markdown or broken formatting."""

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
