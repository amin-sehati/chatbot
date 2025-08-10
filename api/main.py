import json
import os
from http.server import BaseHTTPRequestHandler
from typing import List, Dict, Any

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

# Environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
CHAT_PASSWORD = os.environ.get("CHAT_PASSWORD") or os.getenv("CHAT_PASSWORD")

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
    messages = data.get("messages", [])
    try:
        text = _respond(messages)
        return {
            "status": 200,
            "headers": {"Content-Type": "text/plain"},
            "body": text
        }
    except Exception as e:
        return {
            "status": 500,
            "headers": {"Content-Type": "text/plain"},
            "body": f"Error: {str(e)}"
        }

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            
            # Route based on path
            if self.path == "/api/login":
                response = handle_login(data)
            elif self.path == "/api/chat":
                response = handle_chat(data)
            else:
                response = {
                    "status": 404,
                    "headers": {"Content-Type": "text/plain"},
                    "body": "Not Found"
                }
            
            # Send response
            self.send_response(response["status"])
            for key, value in response["headers"].items():
                self.send_header(key, value)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(response["body"].encode("utf-8"))
            
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()