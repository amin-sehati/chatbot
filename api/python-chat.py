import json
import os
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# For local development with FastAPI
try:
    from fastapi import FastAPI, Response
    from pydantic import BaseModel
    from typing import List

    app = FastAPI()

    class Message(BaseModel):
        role: str
        content: str

    class ChatRequest(BaseModel):
        messages: List[Message]

    @app.post("/")
    async def chat(req: ChatRequest):
        try:
            print(f"Received request with {len(req.messages)} messages")
            model = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))
            history = []
            for m in req.messages:
                if m.role == "system":
                    history.append(SystemMessage(content=m.content))
                elif m.role == "user":
                    history.append(HumanMessage(content=m.content))
                elif m.role == "assistant":
                    history.append(AIMessage(content=m.content))
            print(f"Created history with {len(history)} messages")
            ai = await model.ainvoke(history)
            print(f"Got response: {ai.content[:50]}...")
            return Response(content=ai.content, media_type="text/plain")
        except Exception as e:
            print(f"Error in chat endpoint: {str(e)}")
            import traceback

            traceback.print_exc()
            return Response(
                content=f"Error: {str(e)}", media_type="text/plain", status_code=500
            )

except ImportError:
    # FastAPI not available (Vercel environment)
    pass

# For Vercel deployment
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Read request body
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))

            messages = data.get("messages", [])

            # Initialize OpenAI model
            model = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))

            # Convert messages to LangChain format
            history = []
            for m in messages:
                if m["role"] == "system":
                    history.append(SystemMessage(content=m["content"]))
                elif m["role"] == "user":
                    history.append(HumanMessage(content=m["content"]))
                elif m["role"] == "assistant":
                    history.append(AIMessage(content=m["content"]))

            # Get AI response
            ai = model.invoke(history)

            # Send response
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(ai.content.encode("utf-8"))

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
