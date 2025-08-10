import json
import os
from http.server import BaseHTTPRequestHandler
from typing import List, Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_PASSWORD = os.getenv("CHAT_PASSWORD")

app = FastAPI()


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
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    model = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)
    history = _history_from_messages(messages)
    ai = model.invoke(history)
    return ai.content


@app.post("/api/python-chat", response_class=PlainTextResponse)
async def python_chat(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    text = _respond(messages)
    return PlainTextResponse(text)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Only handle the chat endpoint; ignore others like /api/login
            if self.path != "/api/python-chat":
                self.send_response(404)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Not Found")
                return
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            messages = data.get("messages", [])
            try:
                text = _respond(messages)
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(f"Error: {str(e)}".encode("utf-8"))
                return
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(text.encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
