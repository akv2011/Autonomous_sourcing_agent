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
