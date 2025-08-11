import json
import os
import traceback
import sys
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from tavily import TavilyClient


# Add detailed logging function
def log_debug(message, level="INFO"):
    """Log debug information that will appear in Vercel logs"""
    print(f"[{level}] {message}", file=sys.stderr)
    sys.stderr.flush()


# Pydantic models
class LoginRequest(BaseModel):
    password: str


class ChatMessage(BaseModel):
    role: str
    content: str
    parts: List[Dict[str, Any]] = []


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


# Alternative chat request format for ai-sdk compatibility
class AiSdkMessage(BaseModel):
    role: str
    content: str


class AiSdkChatRequest(BaseModel):
    messages: List[AiSdkMessage]


# Create FastAPI app
app = FastAPI(title="Chatbot API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "service": "Chatbot API",
        "openai_key_present": bool(OPENAI_API_KEY),
        "chat_password_present": bool(CHAT_PASSWORD),
        "tavily_key_present": bool(TAVILY_API_KEY),
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


# Log startup info
log_debug("=== VERCEL SERVERLESS FUNCTION STARTING ===")

# Environment variables with debugging
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
CHAT_PASSWORD = os.environ.get("CHAT_PASSWORD") or os.getenv("CHAT_PASSWORD")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY")

log_debug(f"OPENAI_API_KEY present: {'Yes' if OPENAI_API_KEY else 'No'}")
log_debug(f"CHAT_PASSWORD present: {'Yes' if CHAT_PASSWORD else 'No'}")
log_debug(f"TAVILY_API_KEY present: {'Yes' if TAVILY_API_KEY else 'No'}")


# Create Tavily search tool
@tool
def search_companies(query: str) -> str:
    """Search for companies in a specific market or problem. Use this when users ask about finding companies."""
    if not TAVILY_API_KEY:
        return "Tavily API key not configured"

    try:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        search_query = f"companies {query}"
        response = tavily_client.search(search_query, search_depth="advanced")

        results = []
        for result in response.get("results", [])[:5]:  # Limit to top 5 results
            results.append(
                f"• {result.get('title', 'N/A')}: {result.get('content', 'N/A')[:200]}..."
            )

        return f"🔍 Tool executed: Found companies using web search\n\n" + "\n".join(
            results
        )
    except Exception as e:
        log_debug(f"Tavily search error: {e}", "ERROR")
        return f"Error searching for companies: {str(e)}"


def _history_from_messages(messages: List[Dict[str, Any]]):
    history = []
    for i, m in enumerate(messages):
        role = m.get("role", "user")

        # Enhanced content extraction with debugging (prioritize 'text' field)
        content = ""
        if "text" in m:
            content = m.get("text", "")
            log_debug(f"Extracted content from text field[{i}]: '{content}'")
        elif "content" in m:
            content = m.get("content", "")
            log_debug(f"Extracted content from content field[{i}]: '{content}'")
        elif isinstance(m.get("parts"), list) and m.get("parts"):
            # Extract from parts array
            text_parts = []
            for p in m["parts"]:
                if isinstance(p, dict):
                    if p.get("type") == "text" and "text" in p:
                        text_parts.append(p["text"])
                    elif "text" in p:
                        text_parts.append(p["text"])
            content = "".join(text_parts)
            log_debug(f"Extracted content from parts[{i}]: '{content}'")

        # Log the final content for this message
        log_debug(f"Final content for message[{i}] (role: {role}): '{content}'")

        if role == "system":
            history.append(SystemMessage(content=content))
        elif role == "user":
            history.append(HumanMessage(content=content))
        elif role == "assistant":
            history.append(AIMessage(content=content))

    log_debug(f"Built history with {len(history)} messages")
    return history


def _respond(messages: List[Dict[str, Any]]) -> str:
    if not OPENAI_API_KEY:
        log_debug("OPENAI_API_KEY not set, returning fallback response", "WARNING")
        return "I'm sorry, the AI service is not configured. Please check your API keys."

    # Create model with tool binding
    model = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)
    tools = [search_companies]
    model_with_tools = model.bind_tools(tools)

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant. If users ask about finding companies in specific market or problem, use the search_companies tool to help them. If you use the tool, say so by adding to the beginning of your response '🔍 Tool executed: Found companies using web search\n\n'.",
            ),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

    # Create agent
    agent = create_tool_calling_agent(model_with_tools, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # Convert messages to chat history
    history = _history_from_messages(messages)

    # Get the latest user message
    latest_message = messages[-1].get("content", "") if messages else ""

    # Execute agent
    try:
        response = agent_executor.invoke(
            {
                "input": latest_message,
                "chat_history": history[:-1],  # All messages except the last one
            }
        )
        return response["output"]
    except Exception as e:
        log_debug(f"Agent execution error: {e}", "ERROR")
        # Fallback to basic model if agent fails
        ai = model.invoke(history)
        return ai.content


@app.post("/login")
async def login(request: LoginRequest):
    if not CHAT_PASSWORD:
        raise HTTPException(status_code=500, detail="Server not configured")

    if request.password != CHAT_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Success response with cookie
    response = JSONResponse(content={"ok": True})
    response.set_cookie(
        key="chat_auth",
        value="1",
        httponly=True,
        samesite="lax",
        max_age=604800,
        path="/",
        secure=bool(os.environ.get("VERCEL")),
    )
    return response


@app.post("/chat")
async def chat(request: Request):
    log_debug("=== CHAT REQUEST START ===")

    try:
        # Parse the request body
        body = await request.json()
        log_debug(f"RAW REQUEST BODY: {json.dumps(body, indent=2)}")

        messages = body.get("messages", [])
        log_debug(f"Received {len(messages)} messages")

        # Convert messages to the format expected by _respond
        messages_dict = []
        for i, msg in enumerate(messages):
            log_debug(f"Processing message {i}: {json.dumps(msg, indent=2)}")

            # Handle ai-sdk format where content might be in different places
            content = ""
            parts = []

            if isinstance(msg, dict):
                # Try different ways to extract content (prioritize 'text' field for ai-sdk)
                if "text" in msg:
                    content = msg.get("text", "")
                elif "content" in msg:
                    content = msg.get("content", "")
                elif "parts" in msg and isinstance(msg["parts"], list):
                    # Extract text from parts array
                    text_parts = []
                    for part in msg["parts"]:
                        if isinstance(part, dict):
                            if part.get("type") == "text" and "text" in part:
                                text_parts.append(part["text"])
                            elif "text" in part:
                                text_parts.append(part["text"])
                    content = "".join(text_parts)
                    parts = msg["parts"]

                role = msg.get("role", "user")
            else:
                # Fallback for other formats
                content = getattr(msg, "content", "") or getattr(msg, "text", "")
                role = getattr(msg, "role", "user")
                parts = getattr(msg, "parts", [])

            msg_dict = {
                "role": role,
                "content": content,
                "parts": parts,
            }
            log_debug(f"Converted message {i}: {json.dumps(msg_dict, indent=2)}")
            messages_dict.append(msg_dict)

        log_debug(f"FINAL MESSAGES_DICT: {json.dumps(messages_dict, indent=2)}")

        # Check if we have any actual content
        if not messages_dict or not any(
            msg.get("content", "").strip() for msg in messages_dict
        ):
            log_debug("WARNING: No content found in messages!", "WARNING")
            return StreamingResponse(
                iter(["No message content received. Please try again."]),
                media_type="text/plain",
            )

        log_debug("Calling _respond function...")
        text = _respond(messages_dict)
        log_debug(f"Response generated successfully: {len(text)} characters")

        # Return the response as streaming for ai-sdk compatibility
        # But send the full text at once for Vercel compatibility
        async def generate():
            yield text

        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        error_details = traceback.format_exc()
        log_debug(f"CHAT ERROR: {str(e)}", "ERROR")
        log_debug(f"CHAT TRACEBACK:\n{error_details}", "ERROR")

        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "traceback": error_details,
                "openai_key_present": bool(OPENAI_API_KEY),
            },
        )


# Vercel serverless function handler
from mangum import Mangum

# Create the handler for Vercel
handler = Mangum(app)
