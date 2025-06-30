# 🚀 How to Run the LinkedIn Sourcing Agent

## **Quick Start (30 seconds)**

```bash
# 1. Navigate to project directory
cd synapse-agent

# 2. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 3. Create .env file with your API keys
copy .env.example .env  # Then edit with your actual keys

# 4. Start the server
python start_server.py
```

## **🌐 Access Points**
Once running, access these URLs:
- **Web Interface**: http://localhost:8000/web
- **API Documentation**: http://localhost:8000/docs  
- **Health Check**: http://localhost:8000/health

## **⚙️ Environment Variables Required**

Create a `.env` file in the `synapse-agent` directory:

```bash
# LinkedIn Authentication (Required)
LINKEDIN_SESSION_COOKIE=AQEDARXNaAAB4...your_long_session_cookie

# Google Custom Search (Required)
GOOGLE_API_KEY=AIzaSyD4...your_google_api_key
CUSTOM_SEARCH_ENGINE_ID=a1b2c3d4e5...your_search_engine_id

# AI Analysis (Required) 
GEMINI_API_KEY=AIzaSyG9...your_gemini_api_key
```

---

## **🔑 Detailed API Key Setup Guide**

### **1. LinkedIn Session Cookie** 
**What it looks like:** `AQEDARXNaAAB4gAAAYUCtTgQAAABhQTC6FA4AAAB4wEAAA...` (very long string)

**How to get it:**
1. **Login to LinkedIn** in Chrome/Edge browser
2. **Open Developer Tools** (Press F12)
3. Go to **Application** tab → **Cookies** → **https://www.linkedin.com**
4. Find the cookie named **`li_at`**
5. **Copy the entire Value** (it's a very long string starting with `AQE...`)
6. Paste as `LINKEDIN_SESSION_COOKIE` in your `.env` file

**⚠️ Important Notes:**
- This cookie expires after ~1 year, so you'll need to refresh it
- Keep this cookie private - it gives access to your LinkedIn account
- If you logout of LinkedIn, you'll need to get a new cookie

---

### **2. Google Custom Search API Key**
**What it looks like:** `AIzaSyDpGBslLkXrhqQOuqhLhA12345678Vdj2k` (39 characters)

**How to get it:**
1. Go to **[Google Cloud Console](https://console.cloud.google.com/)**
2. **Create a new project** or select existing one
3. Go to **APIs & Services** → **Credentials**
4. Click **"+ CREATE CREDENTIALS"** → **API Key**
5. **Copy the generated key** (starts with `AIzaSy...`)
6. Go to **APIs & Services** → **Library**
7. **Enable** the "Custom Search API"

**Cost:** 100 free searches per day, then $5 per 1000 queries

---

### **3. Google Custom Search Engine ID**
**What it looks like:** `a1b2c12345678:g8h9i0j1k2l3m4n` (search engine identifier)

**How to get it:**
1. Go to **[Google Custom Search](https://programmablesearchengine.google.com/)**
2. Click **"Get Started"** and **"Add"**
3. **Sites to search:** Enter `linkedin.com/in/*` 
4. **Name your search engine:** "LinkedIn Profile Search"
5. Click **"Create"**
6. In the **"Setup"** tab, turn **ON** "Search the entire web"
7. Go to **"Overview"** tab
8. **Copy the Search Engine ID** (shown in the details section)

**Configuration:**
- **Search the entire web:** ✅ Enabled
- **Image search:** ❌ Disabled  
- **Safe search:** ❌ Disabled

---

### **4. Google Gemini API Key**
**What it looks like:** `AIzaSyG9p12345678nK2sT6uE1wP3hF5dC8b` (39 characters)

**How to get it:**
1. Go to **[Google AI Studio](https://aistudio.google.com/)**
2. **Sign in** with your Google account
3. Click **"Get API Key"** in the top navigation
4. Click **"Create API Key"** 
5. **Select your Google Cloud project** (same as step 2 above)
6. **Copy the generated key** (starts with `AIzaSy...`)

**Free Tier:** 15 requests per minute, 1500 requests per day

---

### **💡 Quick Setup Example**

Your final `.env` file should look exactly like this:

```bash
# Real example format (replace with your actual keys)
LINKEDIN_SESSION_COOKIE=AQEDARXNaAAB4gAA1234567890AAB4wEAAWaFwtToUDgAAF2hQOBQOAABdoUDgUDgAAF2hQOBQOAAA
GOOGLE_API_KEY=AIzaSyDpGBsA1234567890hA-cCxjhW7Vdj2k
CUSTOM_SEARCH_ENGINE_ID=a1b2c3dA12345678902l3m4n
GEMINI_API_KEY=AIzaSyG9pL8mXYzQ4A12345678901wP3hF5dC8b
```

**🎯 Pro Tips:**
- All keys are **case-sensitive**
- No spaces around the `=` sign
- No quotes needed around the values
- Keep your `.env` file private (never commit to git)
4. Paste as `LINKEDIN_SESSION_COOKIE` in your .env file

## **🏃‍♂️ Running Options**

### **Option 1: Enhanced Start (Recommended)**
```bash
cd synapse-agent
python start_server.py
```
*Shows environment checks and detailed startup info*

### **Option 2: Direct Uvicorn**
```bash
cd synapse-agent
python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

### **Option 3: Direct API**
```bash
cd synapse-agent
python api.py
```

## **🧪 Testing Your Setup**

### **1. Health Check**
```bash
curl http://localhost:8000/health
```

### **2. Web Interface Test**
1. Open http://localhost:8000/web
2. Use the pre-filled job description
3. Click "Find & Score Candidates"
4. Wait for results (2-5 minutes)

### **3. API Test**
```bash
curl -X POST "http://localhost:8000/run-sourcing-job-sync/" \
     -H "Content-Type: application/json" \
     -d '{
       "job_description": "Senior Python Developer with FastAPI experience",
       "max_candidates": 5
     }'
```

## **🔧 Troubleshooting**

### **Server Won't Start**
1. Ensure you're in `synapse-agent` directory
2. Check all environment variables in `.env`
3. Install dependencies: `pip install -r requirements.txt`
4. Try enhanced start: `python start_server.py`

### **No Candidates Found**
- Verify LinkedIn session cookie is valid and recent
- Check Google API quota limits in Google Cloud Console
- Test with simpler job descriptions first

### **Scoring/Analysis Fails**
- Ensure Gemini API key is valid
- Check API rate limits in Google AI Studio
- Monitor server logs for specific errors

### **Playwright Issues**
```bash
# Reinstall browsers
playwright install --force chromium

# Windows-specific fix
pip install playwright --force-reinstall
```

## **📁 Project Structure**
```
synapse-agent/
├── api.py                    # Main FastAPI application
├── start_server.py          # Enhanced startup script
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create this)
└── src/
    ├── agent.py             # Core SourcingAgent class  
    └── tools.py             # LinkedIn scraping & AI tools
```

## **🎯 Demo Mode**

For demonstrations, use these optimized settings:

```bash
# Start with detailed logging
python start_server.py --verbose

# Use the web interface with pre-filled data
# Open: http://localhost:8000/web
# Click: "Find & Score Candidates"
```

The system will automatically:
1. Generate search queries from job descriptions
2. Find LinkedIn profiles via Google Search
3. Scrape profile data with Playwright
4. Score candidates with AI (Gemini)
5. Generate personalized outreach messages

**Expected Results:**
- 5-15 candidates found per job
- Fit scores: 60-95% range  
- Processing time: 2-5 minutes
- Personalized outreach messages for each candidate

---

**✅ You're ready to run the LinkedIn Sourcing Agent!**
