#!/usr/bin/env python3
"""
Local development server for testing the FastAPI application
Run this alongside `npm run dev` for local development
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to path so we can import from api/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
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
