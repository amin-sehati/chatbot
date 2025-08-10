import json
import os
from http.server import BaseHTTPRequestHandler
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            messages = data.get("messages", [])

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                self.send_response(500)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Error: OPENAI_API_KEY not set")
                return

            model = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)

            history = []
            for m in messages:
                role = m.get("role", "user")
                # Support both {content: string} and Vercel AI SDK {parts: [{type: "text", text: string}]}
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

            ai = model.invoke(history)

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
