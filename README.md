# 🚀 LinkedIn Sourcing Agent 

An autonomous AI-powered recruitment agent that discovers, analyzes, and creates personalized outreach for LinkedIn candidates based on job descriptions.

## 🌟 Live Demo - Try It Now!

**🚀 No Installation Required!** The agent is live on Hugging Face Spaces:

- **🖥️ Web Interface**: https://akv2011-linkedin-reach.hf.space/web
- **📚 API Documentation**: https://akv2011-linkedin-reach.hf.space/docs
- **💚 Health Check**: https://akv2011-linkedin-reach.hf.space/health

**Ready for judging and demonstrations!**

## 🎯 What This Agent Does

1. **🔍 Discovers Candidates** - Uses Google Custom Search to find relevant LinkedIn profiles
2. **📊 Scores Candidates** - AI-powered analysis using hackathon's fit scoring rubric (1-10 scale)
3. **💬 Generates Outreach** - Creates personalized LinkedIn messages for top candidates
4. **⚡ Handles Scale** - Processes multiple jobs with intelligent rate limiting
5. **📚 Connection Request**: Simulates Connection Request

### **Fit Scoring Rubric Implementation**
The agent implements the **exact** hackathon scoring criteria:
- **Education (20%)** - Elite schools (MIT, Stanford) = 9-10
- **Career Trajectory (20%)** - Clear progression = 8-10
- **Company Relevance (15%)** - Top tech companies = 9-10
- **Experience Match (25%)** - Direct LLM/ML experience = 9-10
- **Location Match (10%)** - Mountain View/Bay Area = 10
- **Tenure (10%)** - 2-4 years average = 9-10

## 🚀 Quick Start

### **🌟 Option 1: Try Live Demo (Instant)**
**No setup required!** Visit the live Hugging Face deployment:
- **🌐 Web Interface**: https://akv2011-linkedin-reach.hf.space/web
- **📚 API Docs**: https://akv2011-linkedin-reach.hf.space/docs

### **🛠️ Option 2: Local Development**
```bash
# 1. Install dependencies
cd synapse-agent
pip install -r requirements.txt
playwright install chromium

# 2. Setup environment variables
cp .env.example .env  # Edit with your API keys

# 3. Start the server
python start_server.py

# 4. Access the local interface
# Open: http://localhost:8000/web
```

## 🌐 Demo & Testing

### **🌍 Live Hugging Face Deployment**
**🚀 Try it now - No installation required!**

- **🖥️ Web Interface**: https://akv2011-linkedin-reach.hf.space/web
- **📚 API Documentation**: https://akv2011-linkedin-reach.hf.space/docs
- **💚 Health Check**: https://akv2011-linkedin-reach.hf.space/health

### **🏠 Local Development**
- **URL**: http://localhost:8000/web
- Pre-filled with Windsurf job description
- Real-time processing display
- Ranked candidate results with scores

### **API Endpoints (Available Both Local & HF)**
- **Complete Pipeline**: `POST /run-sourcing-job-sync/`
- **Enhanced Pipeline**: `POST /find-candidates-with-outreach/`
- **Candidate Discovery**: `POST /search-linkedin/`
- **Fit Scoring**: `POST /score-candidates/`
- **Message Generation**: `POST /generate-outreach/`
- **Interactive Docs**: `/docs` (works on both local and HF)

## 🛠️ Technical Architecture

### **Technology Stack**
- **Language**: Python
- **Web Framework**: FastAPI
- **AI/LLM**: Google Gemini
- **Web Scraping**: Playwright + Beautiful Soup
- **Search**: Google Custom Search API
- **Storage**: JSON files
- **Authentication**: LinkedIn session cookies

### **Core Components**
```
synapse-agent/
├── api.py                   # FastAPI server with 8+ endpoints
├── src/
│   ├── agent.py            # Main SourcingAgent class
│   └── tools.py            # LinkedIn scraping & AI utilities
├── requirements.txt        # Dependencies
├── .env                    # Environment configuration
└── results/               # Job results storage
```

### **Data Flow**
```
Job Description → Search Query Generation → LinkedIn Profile Discovery 
                                                        ↓
Profile Scraping ← Google Custom Search ← Query Optimization
       ↓
AI Analysis & Scoring → Personalized Outreach → Results Storage
```

## 📊 Expected Performance

**Typical Results:**
- **Candidates Found**: 5-15 per job description
- **Fit Scores**: 60-95% range
- **Processing Time**: 2-5 minutes for 10 candidates
- **Success Rate**: 80-90% profile scraping success
- **Message Quality**: Personalized, professional outreach

## 🔧 Configuration

### **(Read synapse-agent\HOW_TO_RUN.md to get more info on where to get keys from ) Required Environment Variables**
```bash
LINKEDIN_SESSION_COOKIE=your_linkedin_li_at_cookie
GOOGLE_API_KEY=your_google_api_key
CUSTOM_SEARCH_ENGINE_ID=your_custom_search_engine_id
GEMINI_API_KEY=your_gemini_api_key
```

### **API Configuration**
- **Live Demo Base URL**: https://akv2011-linkedin-reach.hf.space
- **Local Base URL**: http://localhost:8000
- **Rate Limiting**: Built-in delays for LinkedIn respect
- **Background Processing**: Async job handling
- **Error Handling**: Comprehensive fallbacks

## 🧪 Testing

### **Automated Testing**
```bash
# Test core functionality
python test_full_agent.py

# Test new endpoints
python test_new_endpoint.py
```

### **Manual Testing**
1. **Live Demo**: Visit https://akv2011-linkedin-reach.hf.space/web
2. **Health Check**: 
   - Live: https://akv2011-linkedin-reach.hf.space/health
   - Local: `curl http://localhost:8000/health`
3. **API Testing**: 
   - Live: https://akv2011-linkedin-reach.hf.space/docs
   - Local: http://localhost:8000/docs

## 🚀 Scaling Capabilities

### **Current Scale**
- Handles 10-50 candidates per job
- Background job processing
- Results caching and retrieval
- Rate limiting for API respect

### **Scale to 100s of Jobs**
- **Distributed Processing**: Multiple worker instances
- **Database Storage**: Replace JSON with PostgreSQL/MongoDB
- **Queue System**: Redis/RabbitMQ for job management
- **Caching**: Redis for profile data caching
- **Load Balancing**: Multiple API server instances

## 🏆 Key Features

### **✅ Autonomous Operation**
- Auto-generates search queries from job descriptions
- Handles LinkedIn authentication automatically
- Intelligent retry logic for failed operations

### **✅ AI-Powered Analysis**
- Uses Google Gemini for candidate scoring
- Implements exact hackathon rubric
- Confidence scoring for data quality

### **✅ Production Ready**
- Comprehensive error handling
- Windows/Linux compatibility
- REST API with OpenAPI documentation
- Background job processing

### **✅ Demo Friendly**
- Beautiful web interface
- Real-time progress updates
- Pre-configured test cases
- Interactive API documentation

## 📝 API Usage Examples

### **Complete Sourcing Job (Live Demo)**
```python
import requests

# Using the live Hugging Face deployment
response = requests.post("https://akv2011-linkedin-reach.hf.space/run-sourcing-job-sync/", json={
    "job_description": "Senior Python Developer with FastAPI and ML experience",
    "max_candidates": 10
})

result = response.json()
print(f"Found {result['candidates_found']} candidates")
for candidate in result['top_candidates']:
    print(f"- {candidate['name']}: {candidate['fit_score']}/10")
```

### **Complete Sourcing Job (Local)**
```python
import requests

# Using local development server
response = requests.post("http://localhost:8000/run-sourcing-job-sync/", json={
    "job_description": "Senior Python Developer with FastAPI and ML experience",
    "max_candidates": 10
})

result = response.json()
print(f"Found {result['candidates_found']} candidates")
for candidate in result['top_candidates']:
    print(f"- {candidate['name']}: {candidate['fit_score']}/10")
```

### **Individual Components (Works on both Live & Local)**
```python
# 1. Search LinkedIn
search_response = requests.post("BASE_URL/search-linkedin/", json={
    "job_description": "Python Developer",
    "num_results": 10
})

# 2. Score Candidates  
score_response = requests.post("BASE_URL/score-candidates/", json={
    "candidates": search_response.json()["candidates"],
    "job_description": "Python Developer"
})

# 3. Generate Outreach
outreach_response = requests.post("BASE_URL/generate-outreach/", json={
    "candidates": score_response.json()["scored_candidates"][:5],
    "job_description": "Python Developer"
})
```

**Where BASE_URL is:**
- **Live Demo**: `https://akv2011-linkedin-reach.hf.space`
- **Local**: `http://localhost:8000`

## 🎬 Demo Script

1. **Introduction** (30s): "This is my LinkedIn Sourcing Agent for the Synapse AI Hackathon"
2. **Live Demo** (2 mins): Show end-to-end pipeline at https://akv2011-linkedin-reach.hf.space/web
3. **API Demo** (1 min): Demonstrate programmatic usage via https://akv2011-linkedin-reach.hf.space/docs
4. **Results** (30s): Highlight fit scores and personalized outreach

## 🌐 Deployment Options

### **🚀 Live Production Deployment**
- **Platform**: Hugging Face Spaces (Docker)
- **URL**: https://akv2011-linkedin-reach.hf.space
- **Status**: ✅ Live and Accessible
- **Features**: Full functionality, public API, shareable demos

### **🛠️ Local Development**
- **Platform**: Any machine with Python 3.9+
- **URL**: http://localhost:8000
- **Status**: ✅ Ready for development
- **Features**: Full debugging, custom configurations

