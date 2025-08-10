#!/usr/bin/env python3
"""
Local development server for testing the Python API functions
Run this alongside `npm run dev` for local development
"""

import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import importlib.util
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to path so we can import from api/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the handler from api/main.py
spec = importlib.util.spec_from_file_location("main", "api/main.py")
main_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_module)

class LocalAPIHandler(main_module.handler):
    """Extend the main handler for local development"""
    pass

if __name__ == "__main__":
    port = 8080
    server = HTTPServer(("localhost", port), LocalAPIHandler)
    print(f"🐍 Python API server running on http://localhost:{port}")
    print(f"📝 Test endpoints:")
    print(f"   POST http://localhost:{port}/api/login")
    print(f"   POST http://localhost:{port}/api/chat")
    print(f"🚀 Run 'npm run dev' in another terminal for the frontend")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        server.server_close()