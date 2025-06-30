# 🚀 Deploy LinkedIn Sourcing Agent to Hugging Face Spaces

## **📋 Step-by-Step Deployment Guide**

### **1. Prepare Your Repository**

First, create a new repository structure for Hugging Face Spaces:

```
linkedin-sourcing-agent/          # New HF repository
├── README.md                     # Hugging Face Space description
├── requirements.txt              # Python dependencies 
├── app.py                       # Main FastAPI app (renamed)
├── synapse-agent/               # Your existing code
│   ├── api.py
│   ├── src/
│   │   ├── agent.py
│   │   └── tools.py
│   └── ...
└── .env.example                 # Example environment file
```

### **2. Create Hugging Face Space**

1. Go to **[Hugging Face](https://huggingface.co/)**
2. **Sign up/Login** to your account
3. Click **"Create new Space"**
4. **Configure your Space:**
   - **Space name:** `linkedin-sourcing-agent`
   - **License:** MIT
   - **SDK:** Choose **"Gradio"** (but we'll use FastAPI)
   - **Hardware:** Free tier (CPU) or upgrade if needed
   - **Visibility:** Public or Private

### **3. Required Files for Deployment**

#### **README.md** (Hugging Face Space description)
```markdown
---
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
```

#### **requirements.txt**
```txt
google-genai
python-dotenv
fastapi
uvicorn[standard]
requests
beautifulsoup4
playwright
google-api-python-client
pydantic
python-multipart
```

#### **app.py** (Main entry point for HF Spaces)
```python
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
    print("   • Web Interface: /web")
    print("   • API Docs: /docs")
    print("   • Health Check: /health")
    print("   • Full Pipeline: /run-sourcing-job-sync/")
    
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
```

### **4. Environment Variables Setup**

In your Hugging Face Space settings, add these **Secret Variables**:

```bash
# LinkedIn Authentication
LINKEDIN_SESSION_COOKIE=AQEDARXNaAAB4gAAAYUCtTgQAAABhQTC6FA4AAAB4wEAAA...

# Google APIs  
GOOGLE_API_KEY=AIzaSyDpGBslLkXrhqQOuqhLhA-cCxjhW7Vdj2k
CUSTOM_SEARCH_ENGINE_ID=a1b2c3d4e567890f:g8h9i0j1k2l3m4n
GEMINI_API_KEY=AIzaSyG9pL8mXYzQ4vR7nK2sT6uE1wP3hF5dC8b
```

**How to add them:**
1. Go to your Space settings
2. Click **"Variables and secrets"**
3. Add each variable as a **"Secret"** (not public)
4. Click **"Save"**

### **5. Deployment Methods**

#### **Method A: Git Upload (Recommended)**

```bash
# Clone your new HF Space repository
git clone https://huggingface.co/spaces/YOUR_USERNAME/linkedin-sourcing-agent
cd linkedin-sourcing-agent

# Copy your project files
cp -r /path/to/your/synapse-agent ./
cp /path/to/requirements.txt ./
# Create app.py, README.md as shown above

# Commit and push
git add .
git commit -m "Deploy LinkedIn Sourcing Agent"
git push
```

#### **Method B: Web Upload**
1. Go to your Space **"Files"** tab
2. **Upload** all necessary files
3. **Create** the required files (README.md, app.py, requirements.txt)
4. Space will **automatically rebuild**

### **6. Testing Your Deployment**

Once deployed, your Space will be available at:
```
https://YOUR_USERNAME-linkedin-sourcing-agent.hf.space
```

**Test endpoints:**
- **Web Interface**: `https://your-space.hf.space/web`
- **API Documentation**: `https://your-space.hf.space/docs`
- **Health Check**: `https://your-space.hf.space/health`

#### **API Testing Example:**
```bash
curl -X POST "https://your-space.hf.space/run-sourcing-job-sync/" \
     -H "Content-Type: application/json" \
     -d '{
       "job_description": "Senior Python Developer",
       "max_candidates": 5
     }'
```

### **7. Troubleshooting**

#### **Build Fails**
- Check **"Logs"** tab for errors
- Ensure all files are properly uploaded
- Verify requirements.txt format

#### **Runtime Errors**
- Check environment variables are set
- Monitor **"Logs"** for specific errors
- Test API endpoints individually

#### **Playwright Issues**
- HF Spaces may have browser limitations
- Consider using headless mode only
- Monitor memory usage

### **8. Space Configuration Tips**

#### **Hardware Requirements**
- **Free Tier**: Usually sufficient for demo
- **Upgrade**: If you need faster processing or more memory

#### **Persistent Storage**
- HF Spaces have limited persistent storage
- Consider external storage for large results

#### **Custom Domain** (Optional)
- Available with paid plans
- Can set up custom domain pointing to your Space

---

## **🎉 Your Live API Endpoints**

Once deployed, share these links:

**🌐 Live Demo:** `https://YOUR_USERNAME-linkedin-sourcing-agent.hf.space/web`

**📚 API Documentation:** `https://YOUR_USERNAME-linkedin-sourcing-agent.hf.space/docs`

**🔗 Main API Endpoint:** 
```
POST https://YOUR_USERNAME-linkedin-sourcing-agent.hf.space/run-sourcing-job-sync/
```

**💡 Pro Tip:** Pin the Space to your profile and share the link as your live demo!

---

**✅ Your LinkedIn Sourcing Agent is now live on Hugging Face Spaces!**
