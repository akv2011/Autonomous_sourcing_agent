#!/usr/bin/env python3
"""
LinkedIn Sourcing Agent - Hugging Face Spaces Deployment
"""

import os
import sys
import subprocess

# Install playwright on first run
try:
    subprocess.run(["playwright", "install", "chromium"], 
                  check=True, capture_output=True, timeout=300)
except:
    print("⚠️ Playwright install failed or already installed")

# Add synapse-agent to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'synapse-agent'))

# Import the FastAPI app
from api import app

# Hugging Face Spaces configuration
PORT = int(os.environ.get("PORT", 7860))
HOST = "0.0.0.0"

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 LinkedIn Sourcing Agent - Live on Hugging Face!")
    print(f"🌐 Running on {HOST}:{PORT}")
    print("\n🔗 Available Endpoints:")
    print("   - Web Interface: /web")
    print("   - API Docs: /docs") 
    print("   - Health Check: /health")
    print("   - Full Pipeline: /run-sourcing-job-sync/")
    
    # Check environment variables
    required_env = [
        "LINKEDIN_SESSION_COOKIE",
        "GOOGLE_API_KEY",
        "CUSTOM_SEARCH_ENGINE_ID", 
        "GEMINI_API_KEY"
    ]
    
    missing_env = [env for env in required_env if not os.getenv(env)]
    if missing_env:
        print(f"\n⚠️ Missing environment variables: {', '.join(missing_env)}")
        print("   Configure these in Space Settings → Variables")
    else:
        print("\n✅ All environment variables configured!")
    
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info"
    )
