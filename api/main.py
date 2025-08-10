import json
import os
import traceback
import sys
from http.server import BaseHTTPRequestHandler
from typing import List, Dict, Any

# Add detailed logging function
def log_debug(message, level="INFO"):
    """Log debug information that will appear in Vercel logs"""
    print(f"[{level}] {message}", file=sys.stderr)
    sys.stderr.flush()

# Log startup info
log_debug("=== VERCEL SERVERLESS FUNCTION STARTING ===")

# Environment variables with debugging
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
CHAT_PASSWORD = os.environ.get("CHAT_PASSWORD") or os.getenv("CHAT_PASSWORD")

log_debug(f"OPENAI_API_KEY present: {'Yes' if OPENAI_API_KEY else 'No'}")
log_debug(f"CHAT_PASSWORD present: {'Yes' if CHAT_PASSWORD else 'No'}")

# Try importing dependencies with error handling
try:
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    log_debug("Successfully imported langchain_core.messages")
except ImportError as e:
    log_debug(f"Failed to import langchain_core.messages: {e}", "ERROR")

try:
    from langchain_openai import ChatOpenAI
    log_debug("Successfully imported langchain_openai")
except ImportError as e:
    log_debug(f"Failed to import langchain_openai: {e}", "ERROR")

def _history_from_messages(messages: List[Dict[str, Any]]):
    history = []
    for m in messages:
        role = m.get("role", "user")
        if isinstance(m.get("parts"), list):
            text_parts = [
                (p.get("text") or "")
                for p in m["parts"]
                if isinstance(p, dict) and p.get("type") == "text"
            ]
            content = "".join(text_parts)
        else:
            content = m.get("content") or ""
        if role == "system":
            history.append(SystemMessage(content=content))
        elif role == "user":
            history.append(HumanMessage(content=content))
        elif role == "assistant":
            history.append(AIMessage(content=content))
    return history

def _respond(messages: List[Dict[str, Any]]) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    model = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)
    history = _history_from_messages(messages)
    ai = model.invoke(history)
    return ai.content

def handle_login(data):
    password = data.get("password", "")
    
    if not CHAT_PASSWORD:
        return {
            "status": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Server not configured"})
        }
        
    if password != CHAT_PASSWORD:
        return {
            "status": 401,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Unauthorized"})
        }
        
    # Success response
    headers = {
        "Content-Type": "application/json",
        "Set-Cookie": "chat_auth=1; HttpOnly; SameSite=Lax; Max-Age=604800; Path=/" + ("; Secure" if os.environ.get("VERCEL") else "")
    }
    return {
        "status": 200,
        "headers": headers,
        "body": json.dumps({"ok": True})
    }

def handle_chat(data):
    log_debug("=== CHAT REQUEST START ===")
    messages = data.get("messages", [])
    log_debug(f"Received {len(messages)} messages")
    
    try:
        log_debug("Calling _respond function...")
        text = _respond(messages)
        log_debug(f"Response generated successfully: {len(text)} characters")
        return {
            "status": 200,
            "headers": {"Content-Type": "text/plain"},
            "body": text
        }
    except Exception as e:
        error_details = traceback.format_exc()
        log_debug(f"CHAT ERROR: {str(e)}", "ERROR")
        log_debug(f"CHAT TRACEBACK:\n{error_details}", "ERROR")
        return {
            "status": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": str(e),
                "traceback": error_details,
                "openai_key_present": bool(OPENAI_API_KEY),
                "message_count": len(messages)
            })
        }

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            log_debug(f"=== REQUEST START === Path: {self.path}")
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            log_debug(f"Request body parsed successfully")
            
            # Route based on path
            if self.path == "/api/login":
                log_debug("Routing to login handler")
                response = handle_login(data)
            elif self.path == "/api/chat":
                log_debug("Routing to chat handler")
                response = handle_chat(data)
            else:
                log_debug(f"Unknown path: {self.path}")
                response = {
                    "status": 404,
                    "headers": {"Content-Type": "text/plain"},
                    "body": "Not Found"
                }
            
            # Send response
            log_debug(f"Sending response with status {response['status']}")
            self.send_response(response["status"])
            for key, value in response["headers"].items():
                self.send_header(key, value)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(response["body"].encode("utf-8"))
            log_debug("=== REQUEST COMPLETE ===")
            
        except Exception as e:
            error_details = traceback.format_exc()
            log_debug(f"HANDLER ERROR: {str(e)}", "ERROR")
            log_debug(f"HANDLER TRACEBACK:\n{error_details}", "ERROR")
            
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            error_response = json.dumps({
                "error": str(e),
                "traceback": error_details,
                "path": getattr(self, 'path', 'unknown')
            })
            self.wfile.write(error_response.encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()