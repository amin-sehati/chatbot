import json
import os
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            password = data.get("password", "")
            
            # Robust environment variable loading
            expected = os.environ.get("CHAT_PASSWORD") or os.getenv("CHAT_PASSWORD", "")
            
            if not expected:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                response = {"error": "Server not configured"}
                self.wfile.write(json.dumps(response).encode("utf-8"))
                return
                
            if password != expected:
                self.send_response(401)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                response = {"error": "Unauthorized"}
                self.wfile.write(json.dumps(response).encode("utf-8"))
                return
                
            # Success response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            # Set cookie for authentication
            cookie_value = "chat_auth=1; HttpOnly; SameSite=Lax; Max-Age=604800; Path=/"
            if os.environ.get("VERCEL"):
                cookie_value += "; Secure"
            self.send_header("Set-Cookie", cookie_value)
            self.end_headers()
            response = {"ok": True}
            self.wfile.write(json.dumps(response).encode("utf-8"))
            
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            response = {"error": f"Server error: {str(e)}"}
            self.wfile.write(json.dumps(response).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()