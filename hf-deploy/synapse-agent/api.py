from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import asyncio
import os
import sys
import json
import uuid
from datetime import datetime
from typing import Optional, List
import time

# Fix for Windows asyncio subprocess issue
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Load environment variables early - try multiple paths to ensure it works
env_paths = [
    os.path.join(os.path.dirname(__file__), '.env'),  # synapse-agent/.env
    '.env'  # current directory
]
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded environment from: {env_path}")
        break

# Verify critical environment variables are loaded
gemini_key = os.getenv("GEMINI_API_KEY")
print(f"GEMINI_API_KEY loaded: {'Yes' if gemini_key else 'No'}")

# Fix imports for both direct execution and package imports
try:
    from .src.agent import SourcingAgent
except ImportError:
    # If running directly, adjust the path
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    from agent import SourcingAgent

app = FastAPI(
    title="LinkedIn Sourcing Agent API",
    description="An AI-powered autonomous agent that sources LinkedIn profiles, scores candidates using fit algorithms, and generates personalized outreach - built for the Synapse AI Hackathon",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for web interface
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:
    print("Static files directory not found - web interface disabled")

@app.on_event("startup")
async def startup_event():
    """Ensure proper asyncio event loop policy on startup"""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("FastAPI startup complete with Windows asyncio policy set.")

# I'm using a try-except block to handle the case where the session cookie is missing.
# This is a critical piece of configuration for our custom parser.
try:
    # The agent is now a global instance, initialized on startup.
    agent = SourcingAgent()
except ValueError as e:
    # If the cookie is not set, the API will start but the endpoint will raise an error.
    agent = None
    print(f"CRITICAL ERROR: Could not initialize SourcingAgent. {e}")

class SourcingRequest(BaseModel):
    job_description: str
    search_query: str = Field(default="", description="Optional custom search query. If empty, will be generated from job description")
    send_outreach: bool = False
    max_candidates: int = Field(default=10, ge=1, le=50, description="Maximum number of candidates to return")

class JobDescriptionRequest(BaseModel):
    job_description: str

class CandidateSearchRequest(BaseModel):
    job_description: str
    search_query: str = ""
    num_results: int = Field(default=10, ge=1, le=50)

class ScoringRequest(BaseModel):
    candidates: List[dict]
    job_description: str

class OutreachRequest(BaseModel):
    candidates: List[dict]
    job_description: str
    num_candidates: int = Field(default=5, ge=1, le=10)

class SourcingResponse(BaseModel):
    job_id: str
    job_description: str
    candidates_found: int
    top_candidates: list
    timestamp: str
    status: str
    processing_time: Optional[float] = None
    search_query_used: Optional[str] = None

# Storage for results
RESULTS_DIR = "results"
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

async def run_agent_with_policy(job_description: str, search_query: str, send_outreach: bool = False, num_results: int = 10):
    """Wrapper to ensure Windows asyncio policy is set before running agent"""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    if agent:
        return await agent.run(job_description=job_description, 
                              search_query=search_query, 
                              send_outreach=send_outreach,
                              num_results=num_results)

def save_results(job_id: str, results: dict):
    """Save results to JSON file"""
    try:
        file_path = os.path.join(RESULTS_DIR, f"{job_id}.json")
        with open(file_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {file_path}")
    except Exception as e:
        print(f"Error saving results: {e}")

def load_results(job_id: str) -> Optional[dict]:
    """Load results from JSON file"""
    try:
        file_path = os.path.join(RESULTS_DIR, f"{job_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading results: {e}")
    return None

def format_results(raw_results: dict, job_description: str, processing_time: float = None, max_candidates: int = 10) -> dict:
    """Format and filter results to top N candidates"""
    if "results" not in raw_results:
        return {
            "job_id": str(uuid.uuid4()),
            "job_description": job_description,
            "candidates_found": 0,
            "top_candidates": [],
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error": raw_results.get("error", "Unknown error"),
            "processing_time": processing_time,
            "search_query_used": raw_results.get("search_query_used")
        }
    
    # Filter out failed candidates and sort by fit_score
    valid_candidates = []
    for candidate in raw_results.get("results", []):
        if isinstance(candidate, dict) and "fit_score" in candidate:
            try:
                # Ensure fit_score is a number
                fit_score = float(candidate.get("fit_score", 0))
                candidate["fit_score"] = fit_score
                valid_candidates.append(candidate)
            except (ValueError, TypeError):
                continue
    
    # Sort by fit_score (highest first) and take top N based on max_candidates
    valid_candidates.sort(key=lambda x: x.get("fit_score", 0), reverse=True)
    top_candidates = valid_candidates[:max_candidates]
    
    job_id = str(uuid.uuid4())
    
    formatted_results = {
        "job_id": job_id,
        "job_description": job_description,
        "search_query_used": raw_results.get("search_query_used"),
        "candidates_found": len(valid_candidates),
        "top_candidates": top_candidates,
        "timestamp": datetime.now().isoformat(),
        "status": "completed",
        "processing_time": processing_time
    }
    
    # Save results
    save_results(job_id, formatted_results)
    
    return formatted_results

# I'm updating the main endpoint to be asynchronous to support the async agent.
@app.post("/run-sourcing-job/")
async def run_sourcing_job(request: SourcingRequest, background_tasks: BackgroundTasks):
    """
    This endpoint kicks off the full sourcing process.
    It requires a job description and a search query, and can optionally send outreach.
    The actual processing is run in the background.
    """
    if not agent:
        raise HTTPException(
            status_code=503, 
            detail="Sourcing Agent is not available. Check server logs for initialization errors (e.g., missing LINKEDIN_SESSION_COOKIE)."
        )

    # This will run the agent's main function in the background with proper asyncio policy
    background_tasks.add_task(run_agent_with_policy, 
                              job_description=request.job_description,
                              search_query=request.search_query,
                              send_outreach=request.send_outreach,
                              num_results=request.max_candidates)
    
    return {"message": "Sourcing job started in the background. Results will be processed and stored."}

# NEW: Synchronous endpoint that returns results immediately
@app.post("/run-sourcing-job-sync/", response_model=SourcingResponse)
async def run_sourcing_job_sync(request: SourcingRequest):
    """
    Synchronous endpoint that runs the sourcing process and returns results immediately.
    Perfect for demos and testing.
    """
    if not agent:
        raise HTTPException(
            status_code=503, 
            detail="Sourcing Agent is not available. Check server logs for initialization errors (e.g., missing LINKEDIN_SESSION_COOKIE)."
        )
    
    try:
        start_time = time.time()
        
        # If search_query is an empty string, set it to None so the agent generates it
        search_query = request.search_query or None
        
        # Run the agent synchronously
        raw_results = await run_agent_with_policy(
            job_description=request.job_description,
            search_query=search_query,
            send_outreach=request.send_outreach,
            num_results=request.max_candidates
        )
        
        processing_time = time.time() - start_time
        
        # Format and save results
        formatted_results = format_results(raw_results, request.job_description, processing_time, request.max_candidates)
        
        return formatted_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing sourcing job: {str(e)}")

# NEW: Get results by job ID
@app.get("/results/{job_id}")
async def get_results(job_id: str):
    """
    Retrieve results by job ID
    """
    results = load_results(job_id)
    if not results:
        raise HTTPException(status_code=404, detail="Results not found")
    return results

# NEW: List all job results
@app.get("/results/")
async def list_results():
    """
    List all available job results
    """
    try:
        results = []
        if os.path.exists(RESULTS_DIR):
            for filename in os.listdir(RESULTS_DIR):
                if filename.endswith('.json'):
                    job_id = filename[:-5]  # Remove .json extension
                    job_data = load_results(job_id)
                    if job_data:
                        results.append({
                            "job_id": job_id,
                            "timestamp": job_data.get("timestamp"),
                            "candidates_found": job_data.get("candidates_found", 0),
                            "status": job_data.get("status", "unknown")
                        })
        return {"jobs": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing results: {str(e)}")

# REQUIRED ENDPOINTS - Matching the hackathon requirements exactly

@app.post("/search-linkedin/")
async def search_linkedin_endpoint(request: CandidateSearchRequest):
    """
    # 2. Candidate Discovery
    candidates = agent.search_linkedin(job_description)
    # Returns: [{"name": "John Doe", "linkedin_url": "...", "headline": "..."}]
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Sourcing Agent is not available.")
    
    try:
        candidates = await agent.search_linkedin(request.job_description, request.num_results)
        return {"candidates": candidates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching LinkedIn: {str(e)}")

@app.post("/score-candidates/")
async def score_candidates_endpoint(request: ScoringRequest):
    """
    # 3. Fit Scoring
    scored_candidates = agent.score_candidates(candidates, job_description)
    # Returns: [{"name": "...", "score": 8.5, "breakdown": {...}}]
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Sourcing Agent is not available.")
    
    try:
        scored_candidates = await agent.score_candidates(request.candidates, request.job_description)
        return {"scored_candidates": scored_candidates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scoring candidates: {str(e)}")

@app.post("/generate-outreach/")
async def generate_outreach_endpoint(request: OutreachRequest):
    """
    # 4. Message Generation
    messages = agent.generate_outreach(scored_candidates[:5], job_description)
    # Returns: [{"candidate": "...", "message": "Hi John, I noticed..."}]
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Sourcing Agent is not available.")
    
    try:
        # Take only the requested number of top candidates
        top_candidates = request.candidates[:request.num_candidates]
        messages = await agent.generate_outreach(top_candidates, request.job_description)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating outreach: {str(e)}")

# ENHANCED ENDPOINTS

@app.post("/find-candidates-with-outreach/")
async def find_candidates_with_outreach(request: JobDescriptionRequest):
    """
    Complete candidate sourcing pipeline that takes job description as input 
    and returns top 10 candidates with personalized outreach messages.
    
    Returns candidates with their profile characteristics and job match analysis.
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Sourcing Agent is not available.")
    
    try:
        start_time = time.time()
        
        # Run the complete pipeline with outreach generation
        raw_results = await run_agent_with_policy(
            job_description=request.job_description,
            search_query=None,  # Auto-generate search query
            send_outreach=False,  # We'll generate messages but not send them
            num_results=10  # Fixed at 10 candidates as requested
        )
        
        processing_time = time.time() - start_time
        
        if "results" not in raw_results or not raw_results["results"]:
            return {
                "job_description": request.job_description,
                "total_candidates_found": 0,
                "top_candidates": [],
                "processing_time_seconds": processing_time,
                "search_query_used": raw_results.get("search_query_used"),
                "status": "no_candidates_found"
            }
        
        # Filter and sort candidates by fit_score
        valid_candidates = []
        for candidate in raw_results.get("results", []):
            if isinstance(candidate, dict) and "fit_score" in candidate:
                try:
                    fit_score = float(candidate.get("fit_score", 0))
                    candidate["fit_score"] = fit_score
                    valid_candidates.append(candidate)
                except (ValueError, TypeError):
                    continue
        
        # Sort by fit_score (highest first) and take top 10
        valid_candidates.sort(key=lambda x: x.get("fit_score", 0), reverse=True)
        top_10_candidates = valid_candidates[:10]
        
        # Format the response with enhanced outreach messages
        formatted_candidates = []
        for i, candidate in enumerate(top_10_candidates, 1):
            formatted_candidate = {
                "rank": i,
                "name": candidate.get("name", "N/A"),
                "linkedin_url": candidate.get("linkedin_url", ""),
                "headline": candidate.get("headline", "N/A"),
                "fit_score": candidate.get("fit_score", 0),
                "confidence_score": candidate.get("confidence_score", 0),
                "profile_characteristics": {
                    "experience": candidate.get("experience", []),
                    "education": candidate.get("education", []),
                    "skills": candidate.get("skills", []),
                    "current_position": candidate.get("headline", "N/A")
                },
                "job_match_analysis": {
                    "key_strengths": candidate.get("reasoning", "").split(". ")[:3] if candidate.get("reasoning") else [],
                    "fit_reasoning": candidate.get("reasoning", "No analysis available"),
                    "match_score_breakdown": {
                        "technical_skills": min(candidate.get("fit_score", 0), 10),
                        "experience_level": min(candidate.get("fit_score", 0) * 0.9, 10),
                        "cultural_fit": min(candidate.get("confidence_score", 0) * 10, 10)
                    }
                },
                "personalized_outreach_message": candidate.get("outreach_message", f"Hi {candidate.get('name', 'there')}, I'd love to connect and discuss an exciting opportunity that matches your background!")
            }
            formatted_candidates.append(formatted_candidate)
        
        response = {
            "job_description": request.job_description,
            "search_query_used": raw_results.get("search_query_used", "Auto-generated"),
            "total_candidates_found": len(valid_candidates),  
            "top_candidates": formatted_candidates,
            "processing_time_seconds": round(processing_time, 2),
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding candidates with outreach: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Health check endpoint with system status
    """
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_available": agent is not None,
        "results_directory": os.path.exists(RESULTS_DIR),
        "total_jobs_processed": len(os.listdir(RESULTS_DIR)) if os.path.exists(RESULTS_DIR) else 0
    }
    
    # Check environment variables
    required_env_vars = ["LINKEDIN_SESSION_COOKIE", "GOOGLE_API_KEY", "CUSTOM_SEARCH_ENGINE_ID", "GEMINI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        status["warnings"] = f"Missing environment variables: {', '.join(missing_vars)}"
    
    return status

# WEB INTERFACE
@app.get("/web", response_class=HTMLResponse)
async def web_interface():
    """
    Simple web interface for testing the API
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LinkedIn Sourcing Agent</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f8f9fa; }
            .header { text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; }
            .container { background: white; padding: 25px; border-radius: 12px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            textarea { width: 100%; height: 120px; margin: 10px 0; padding: 12px; border: 2px solid #e1e5e9; border-radius: 8px; font-family: inherit; }
            input[type="text"] { width: 100%; padding: 12px; margin: 10px 0; border: 2px solid #e1e5e9; border-radius: 8px; }
            button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; margin: 5px; }
            button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3); }
            .result { background: #f8f9fa; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #667eea; }
            .candidate { background: #e8f5e8; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #28a745; }
            .score { font-weight: bold; color: #d4650f; background: #fff3cd; padding: 4px 8px; border-radius: 4px; }
            .loading { color: #6c757d; font-style: italic; }
            .error { background: #f8d7da; color: #721c24; border-left-color: #dc3545; }
            .success { background: #d4edda; color: #155724; border-left-color: #28a745; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1> LinkedIn Sourcing Agent</h1>
            <p>Synapse AI Hackathon - Autonomous LinkedIn Recruitment Agent</p>
        </div>
        
        <div class="container">
            <h2> Run Full Sourcing Job</h2>
            <p>Enter a job description to find and analyze the best LinkedIn candidates automatically.</p>
            <textarea id="jobDescription" placeholder="Enter job description here...">Software Engineer, ML Research at Windsurf (Forbes AI 50 company) - Building AI-powered developer tools. Looking for someone to train LLMs for code generation, $140-300k + equity in Mountain View. Required: PhD in CS/ML, experience with large neural networks, Python expertise, research background.</textarea>
            <input type="text" id="searchQuery" placeholder="Optional: Custom search query (leave empty for auto-generation)">
            <div style="margin: 10px 0;">
                <label for="maxCandidates" style="display: inline-block; margin-right: 10px; font-weight: bold;">Number of Candidates:</label>
                <select id="maxCandidates" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
                    <option value="5">5 candidates</option>
                    <option value="10" selected>10 candidates</option>
                    <option value="15">15 candidates</option>
                    <option value="20">20 candidates</option>
                    <option value="25">25 candidates</option>
                    <option value="30">30 candidates</option>
                    <option value="50">50 candidates</option>
                </select>
                <small style="color: #666; margin-left: 10px;">⏱ More candidates = longer processing time</small>
            </div>
            <div style="margin: 15px 0;">
                <label style="display: flex; align-items: center; gap: 8px; font-weight: bold;">
                    <input type="checkbox" id="sendOutreach" style="transform: scale(1.2);">
                    <span> Send LinkedIn Connection Requests</span>
                </label>
                <small style="color: #666; margin-left: 24px;">Automatically send personalized connection requests to top candidates</small>
            </div>
            <br>
            <button onclick="runSourcingJob()"> Find & Score Candidates</button>
            <button onclick="findCandidatesWithOutreach()"> Find Top 10 + Outreach Messages</button>
            <button onclick="clearResults()"> Clear Results</button>
            <div id="results"></div>
        </div>

        <div class="container">
            <h2> System Health & Status</h2>
            <button onclick="checkHealth()"> Check System Health</button>
            <button onclick="listJobs()"> List All Jobs</button>
            <div id="healthResults"></div>
        </div>

        <div class="container">
            <h2>API Documentation</h2>
            <p>This agent provides the following endpoints:</p>
            <ul>
                <li><strong>POST /run-sourcing-job-sync/</strong> - Complete sourcing pipeline (recommended)</li>
                <li><strong>POST /find-candidates-with-outreach/</strong> - Find top 10 candidates with outreach messages (NEW)</li>
                <li><strong>POST /search-linkedin/</strong> - Find LinkedIn profiles only</li>
                <li><strong>POST /score-candidates/</strong> - Score existing candidates</li>
                <li><strong>POST /generate-outreach/</strong> - Generate personalized messages</li>
                <li><strong>GET /docs</strong> - Interactive API documentation</li>
            </ul>
            <button onclick="window.open('/docs', '_blank')"> Open API Docs</button>
        </div>

        <script>
            async function runSourcingJob() {
                const jobDesc = document.getElementById('jobDescription').value;
                const searchQuery = document.getElementById('searchQuery').value;
                const maxCandidates = parseInt(document.getElementById('maxCandidates').value);
                const sendOutreach = document.getElementById('sendOutreach').checked;
                const resultsDiv = document.getElementById('results');
                
                if (!jobDesc.trim()) {
                    resultsDiv.innerHTML = '<div class="result error"> Please enter a job description</div>';
                    return;
                }
                
                resultsDiv.innerHTML = `<div class="result loading"> Processing your request for ${maxCandidates} candidates... This may take ${Math.ceil(maxCandidates * 0.2)}-${Math.ceil(maxCandidates * 0.4)} minutes while we scrape LinkedIn profiles and analyze candidates...</div>`;
                
                try {
                    const startTime = Date.now();
                    const response = await fetch('/run-sourcing-job-sync/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            job_description: jobDesc,
                            search_query: searchQuery,
                            send_outreach: sendOutreach,
                            max_candidates: maxCandidates
                        })
                    });
                    
                    const result = await response.json();
                    const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
                    
                    if (result.status === 'completed') {
                        let html = `
                            <div class="result success">
                                <h3> Sourcing Job Completed Successfully!</h3>
                                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 15px 0;">
                                    <div><strong>Job ID:</strong> ${result.job_id}</div>
                                    <div><strong>Candidates Found:</strong> ${result.candidates_found}</div>
                                    <div><strong>Processing Time:</strong> ${totalTime}s</div>
                                    <div><strong>Search Query:</strong> ${result.search_query_used || 'Auto-generated'}</div>
                                </div>
                            </div>
                        `;
                        
                        if (result.top_candidates && result.top_candidates.length > 0) {
                            html += '<h3> Top Candidates (Ranked by Fit Score):</h3>';
                            
                            result.top_candidates.forEach((candidate, index) => {
                                const scoreColor = candidate.fit_score >= 8 ? '#28a745' : candidate.fit_score >= 6 ? '#ffc107' : '#dc3545';
                                html += `
                                    <div class="candidate">
                                        <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 10px;">
                                            <h4 style="margin: 0;">#${index + 1} ${candidate.name}</h4>
                                            <span class="score" style="background-color: ${scoreColor}20; color: ${scoreColor};">
                                                Score: ${candidate.fit_score}/10
                                            </span>
                                        </div>
                                        <p><strong> LinkedIn:</strong> <a href="${candidate.linkedin_url}" target="_blank" style="color: #0077b5;">View Profile</a></p>
                                        ${candidate.reasoning ? `<p><strong> Analysis:</strong> ${candidate.reasoning}</p>` : ''}
                                        ${candidate.outreach_message ? `<p><strong> Suggested Outreach:</strong> <em>"${candidate.outreach_message}"</em></p>` : ''}
                                        ${candidate.confidence_score ? `<p><strong> Confidence:</strong> ${(candidate.confidence_score * 100).toFixed(0)}%</p>` : ''}
                                    </div>
                                `;
                            });
                        } else {
                            html += '<div class="result"> No qualifying candidates found. Try adjusting your job description or search criteria.</div>';
                        }
                        
                        resultsDiv.innerHTML = html;
                    } else {
                        resultsDiv.innerHTML = `<div class="result error"> Error: ${result.error || 'Unknown error occurred'}</div>`;
                    }
                } catch (error) {
                    resultsDiv.innerHTML = `<div class="result error"> Network Error: ${error.message}</div>`;
                }
            }
            
            async function findCandidatesWithOutreach() {
                const jobDesc = document.getElementById('jobDescription').value;
                const resultsDiv = document.getElementById('results');
                
                if (!jobDesc.trim()) {
                    resultsDiv.innerHTML = '<div class="result error"> Please enter a job description</div>';
                    return;
                }
                
                resultsDiv.innerHTML = '<div class="result loading"> Finding top 10 candidates with personalized outreach messages... This may take 2-5 minutes...</div>';
                
                try {
                    const startTime = Date.now();
                    const response = await fetch('/find-candidates-with-outreach/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            job_description: jobDesc
                        })
                    });
                    
                    const result = await response.json();
                    const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
                    
                    if (result.status === 'success') {
                        let html = `
                            <div class="result success">
                                <h3> Top 10 Candidates with Outreach Messages</h3>
                                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 15px 0;">
                                    <div><strong>Total Found:</strong> ${result.total_candidates_found}</div>
                                    <div><strong>Processing Time:</strong> ${totalTime}s</div>
                                    <div><strong>Search Query:</strong> ${result.search_query_used || 'Auto-generated'}</div>
                                </div>
                            </div>
                        `;
                        
                        if (result.top_candidates && result.top_candidates.length > 0) {
                            result.top_candidates.forEach((candidate, index) => {
                                const scoreColor = candidate.fit_score >= 8 ? '#28a745' : candidate.fit_score >= 6 ? '#ffc107' : '#dc3545';
                                html += `
                                    <div class="candidate" style="margin: 20px 0; padding: 20px;">
                                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                            <h4 style="margin: 0;">#{candidate.rank} ${candidate.name}</h4>
                                            <span class="score" style="background-color: ${scoreColor}20; color: ${scoreColor};">
                                                Score: ${candidate.fit_score}/10
                                            </span>
                                        </div>
                                        
                                        <p><strong> LinkedIn:</strong> <a href="${candidate.linkedin_url}" target="_blank" style="color: #0077b5;">View Profile</a></p>
                                        <p><strong> Current Role:</strong> ${candidate.headline}</p>
                                        
                                        <div style="margin: 15px 0;">
                                            <strong> Job Match Analysis:</strong>
                                            <div style="margin-left: 20px; font-size: 14px;">
                                                <p><strong>Fit Reasoning:</strong> ${candidate.job_match_analysis.fit_reasoning}</p>
                                                <p><strong>Technical Skills:</strong> ${candidate.job_match_analysis.match_score_breakdown.technical_skills.toFixed(1)}/10</p>
                                                <p><strong>Experience Level:</strong> ${candidate.job_match_analysis.match_score_breakdown.experience_level.toFixed(1)}/10</p>
                                            </div>
                                        </div>
                                        
                                        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 15px;">
                                            <strong> Personalized Outreach Message:</strong>
                                            <p style="font-style: italic; margin-top: 10px; color: #495057;">"${candidate.personalized_outreach_message}"</p>
                                        </div>
                                        
                                        <p><strong> Confidence:</strong> ${(candidate.confidence_score * 100).toFixed(0)}%</p>
                                    </div>
                                `;
                            });
                        } else {
                            html += '<div class="result"> No candidates found. Try adjusting your job description.</div>';
                        }
                        
                        resultsDiv.innerHTML = html;
                    } else {
                        resultsDiv.innerHTML = `<div class="result error"> Error: ${result.error || 'No candidates found'}</div>`;
                    }
                } catch (error) {
                    resultsDiv.innerHTML = `<div class="result error"> Network Error: ${error.message}</div>`;
                }
            }
            
            async function checkHealth() {
                const healthDiv = document.getElementById('healthResults');
                
                try {
                    const response = await fetch('/health');
                    const health = await response.json();
                    
                    const statusIcon = health.status === 'healthy' ? '✅' : '❌';
                    const agentIcon = health.agent_available ? '✅' : '❌';
                    
                    healthDiv.innerHTML = `
                        <div class="result ${health.status === 'healthy' ? 'success' : 'error'}">
                            <h3>System Status: ${statusIcon} ${health.status.toUpperCase()}</h3>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                                <div><strong>Agent Status:</strong> ${agentIcon} ${health.agent_available ? 'Available' : 'Unavailable'}</div>
                                <div><strong>Jobs Processed:</strong> ${health.total_jobs_processed}</div>
                                <div><strong>Results Storage:</strong> ${health.results_directory ? '✅' : '❌'}</div>
                                <div><strong>Timestamp:</strong> ${new Date(health.timestamp).toLocaleString()}</div>
                            </div>
                            ${health.warnings ? `<p style="margin-top: 15px;"><strong>⚠️ Warnings:</strong> ${health.warnings}</p>` : ''}
                        </div>
                    `;
                } catch (error) {
                    healthDiv.innerHTML = `<div class="result error">❌ Error checking health: ${error.message}</div>`;
                }
            }
            
            async function listJobs() {
                const healthDiv = document.getElementById('healthResults');
                
                try {
                    const response = await fetch('/results/');
                    const data = await response.json();
                    
                    if (data.jobs && data.jobs.length > 0) {
                        let html = '<div class="result"><h3>📋 Recent Sourcing Jobs:</h3><ul>';
                        data.jobs.forEach(job => {
                            const date = new Date(job.timestamp).toLocaleString();
                            html += `<li><strong>Job ID:</strong> ${job.job_id} | <strong>Candidates:</strong> ${job.candidates_found} | <strong>Date:</strong> ${date}</li>`;
                        });
                        html += '</ul></div>';
                        healthDiv.innerHTML = html;
                    } else {
                        healthDiv.innerHTML = '<div class="result">📭 No previous jobs found.</div>';
                    }
                } catch (error) {
                    healthDiv.innerHTML = `<div class="result error"> Error listing jobs: ${error.message}</div>`;
                }
            }
            
            function clearResults() {
                document.getElementById('results').innerHTML = '';
                document.getElementById('healthResults').innerHTML = '';
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
