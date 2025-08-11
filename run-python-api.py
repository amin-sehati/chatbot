#!/usr/bin/env python3
"""
Local development server for testing the API
Run this alongside `npm run dev` for local development
Supports both FastAPI (preferred) and BaseHTTPRequestHandler (Vercel-compatible) modes
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to path so we can import from api/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_fastapi():
    """Run with FastAPI (recommended for local development)"""
    try:
        import uvicorn

        print("🚀 Starting FastAPI server...")
        print("📝 Test endpoints:")
        print("   POST http://localhost:8080/login")
        print("   POST http://localhost:8080/chat")
        print("🚀 Run 'npm run dev' in another terminal for the frontend")

        # Run the FastAPI app with uvicorn
        uvicorn.run(
            "api.main:app", host="localhost", port=8080, reload=True, log_level="info"
        )
    except ImportError:
        print(
            "❌ FastAPI/Uvicorn not available, falling back to BaseHTTPRequestHandler mode"
        )
        run_base_handler()


def run_base_handler():
    """Run with BaseHTTPRequestHandler (Vercel-compatible)"""
    from http.server import HTTPServer
    from api.main import handler

    port = 8080
    server = HTTPServer(("localhost", port), handler)
    print(f"🐍 BaseHTTP server running on http://localhost:{port}")
    print(f"📝 Test endpoints:")
    print(f"   POST http://localhost:{port}/api/login")
    print(f"   POST http://localhost:{port}/api/chat")
    print(f"🚀 Run 'npm run dev' in another terminal for the frontend")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local API development server")
    parser.add_argument(
        "--mode",
        choices=["fastapi", "handler"],
        default="fastapi",
        help="Server mode: fastapi (recommended) or handler (Vercel-compatible)",
    )
    args = parser.parse_args()

    if args.mode == "fastapi":
        run_fastapi()
    else:
        run_base_handler()
