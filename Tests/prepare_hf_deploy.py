#!/usr/bin/env python3
"""
Quick deployment preparation script for Hugging Face Spaces
"""

import os
import shutil
import sys

def create_hf_deployment():
    """Create deployment-ready structure for Hugging Face Spaces"""
    
    print("🚀 Preparing LinkedIn Sourcing Agent for Hugging Face Spaces...")
    
    # Create deployment directory
    deploy_dir = "hf-deploy"
    if os.path.exists(deploy_dir):
        shutil.rmtree(deploy_dir)
    os.makedirs(deploy_dir)
    
    # Copy synapse-agent directory
    if os.path.exists("synapse-agent"):
        shutil.copytree("synapse-agent", os.path.join(deploy_dir, "synapse-agent"))
        print("✅ Copied synapse-agent directory")
    else:
        print("❌ synapse-agent directory not found!")
        return
    
    # Create app.py (main entry point)
    app_py_content = '''#!/usr/bin/env python3
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
    print("\\n🔗 Available Endpoints:")
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
        print(f"\\n⚠️ Missing environment variables: {', '.join(missing_env)}")
        print("   Configure these in Space Settings → Variables")
    else:
        print("\\n✅ All environment variables configured!")
    
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info"
    )
'''
    
    with open(os.path.join(deploy_dir, "app.py"), "w", encoding="utf-8") as f:
        f.write(app_py_content)
    print("✅ Created app.py")
    
    # Create requirements.txt
    requirements = """google-genai
python-dotenv
fastapi
uvicorn[standard]
requests
beautifulsoup4
playwright
google-api-python-client
pydantic
python-multipart
"""
    
    with open(os.path.join(deploy_dir, "requirements.txt"), "w", encoding="utf-8") as f:
        f.write(requirements)
    print("✅ Created requirements.txt")
    
    # Create README.md for HF Spaces
    readme_content = '''---
title: LinkedIn Sourcing Agent
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.0.0
app_file: app.py
pinned: false
license: mit
short_description: AI-powered LinkedIn candidate sourcing and scoring agent
---

# 🔍 LinkedIn Sourcing Agent

An autonomous AI-powered recruitment agent that discovers, analyzes, and creates personalized outreach for LinkedIn candidates.

## 🚀 Features
- **Candidate Discovery**: Uses Google Custom Search to find LinkedIn profiles
- **AI Scoring**: Gemini-powered candidate evaluation (1-10 scale)  
- **Personalized Outreach**: Auto-generated LinkedIn messages
- **REST API**: Complete FastAPI backend with documentation

## 🌐 Live Demo
- **Web Interface**: Click the "App" button above
- **API Documentation**: Visit `/docs` endpoint
- **Health Check**: Visit `/health` endpoint

## ⚙️ Required Environment Variables
Add these in the Space settings:
- `LINKEDIN_SESSION_COOKIE`: Your LinkedIn li_at cookie
- `GOOGLE_API_KEY`: Google Cloud API key
- `CUSTOM_SEARCH_ENGINE_ID`: Google Custom Search Engine ID
- `GEMINI_API_KEY`: Google Gemini API key

## 🔗 GitHub Repository
[View Source Code](https://github.com/your-username/linkedin-sourcing-agent)

## 📝 API Usage

### Complete Sourcing Job
```python
import requests

response = requests.post("https://your-space.hf.space/run-sourcing-job-sync/", json={
    "job_description": "Senior Python Developer with FastAPI experience",
    "max_candidates": 10
})

result = response.json()
print(f"Found {result['candidates_found']} candidates")
```

### Individual Endpoints
- `POST /search-linkedin/` - Find LinkedIn profiles
- `POST /score-candidates/` - Score candidates with AI
- `POST /generate-outreach/` - Generate personalized messages
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## 🎯 Demo
Use the web interface above or test the API with sample data. The system automatically:
1. Generates search queries from job descriptions
2. Finds LinkedIn profiles via Google Search
3. Scrapes profile data with Playwright
4. Scores candidates with AI (Gemini)
5. Creates personalized outreach messages

**Expected Results:**
- 5-15 candidates found per job
- Fit scores: 60-95% range
- Processing time: 2-5 minutes
- Personalized LinkedIn messages for top candidates
'''
    
    with open(os.path.join(deploy_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("✅ Created README.md")
    
    # Create .env.example
    env_example = """# LinkedIn Authentication (Required)
LINKEDIN_SESSION_COOKIE=AQEDARXNaAAB4gAAAYUCtTgQAAABhQTC6FA4AAAB4wEAAA...

# Google Custom Search (Required)
GOOGLE_API_KEY=AIzaSyDpGBslLkXrhqQOuqhLhA-cCxjhW7Vdj2k
CUSTOM_SEARCH_ENGINE_ID=a1b2c3d4e567890f:g8h9i0j1k2l3m4n

# AI Analysis (Required)
GEMINI_API_KEY=AIzaSyG9pL8mXYzQ4vR7nK2sT6uE1wP3hF5dC8b
"""
    
    with open(os.path.join(deploy_dir, ".env.example"), "w", encoding="utf-8") as f:
        f.write(env_example)
    print("✅ Created .env.example")
    
    print(f"\n🎉 Deployment files ready in '{deploy_dir}' directory!")
    print("\n📋 Next Steps:")
    print("1. Create a new Hugging Face Space at https://huggingface.co/new-space")
    print("2. Upload all files from the 'hf-deploy' directory")
    print("3. Configure environment variables in Space settings")
    print("4. Your API will be live at: https://YOUR_USERNAME-SPACE_NAME.hf.space")
    
    return deploy_dir

if __name__ == "__main__":
    create_hf_deployment()
