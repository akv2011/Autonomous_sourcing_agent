# 🚀 How to Run the LinkedIn Sourcing Agent Server

## **Method 1: Enhanced Start (With Environment Checks)**
```bash
cd synapse-agent  
python start_server.py
```

## **Method 2: Manual Uvicorn**
```bash
cd synapse-agent
python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

## **🌐 Access Points**
Once the server is running:
- **Web Interface**: http://localhost:8000/web
- **API Documentation**: http://localhost:8000/docs  
- **Health Check**: http://localhost:8000/health

## **📁 Clean Project Structure**
```
synapse-agent/
├── api.py                    # Main FastAPI application
├── start_server.py          # Enhanced startup with env checks
├── requirements.txt         # Dependencies
├── .env                     # Environment variables
├── src/
│   ├── agent.py            # Core agent logic
│   └── tools.py            # LinkedIn parser & LLM calls
├── screenshots/            # Debug screenshots (auto-created)
└── results/               # Job results storage
```

## **🔧 Troubleshooting**
If the server won't start:
1. Make sure you're in the `synapse-agent` directory
2. Check your `.env` file has all required variables
3. Install dependencies: `pip install -r requirements.txt`
4. Try the enhanced start: `python start_server.py` (shows detailed error info)

## **⚙️ Environment Variables Required**
```bash
LINKEDIN_SESSION_COOKIE=your_session_cookie
GOOGLE_API_KEY=your_google_api_key  
CUSTOM_SEARCH_ENGINE_ID=your_cse_id
GEMINI_API_KEY=your_gemini_key
```
