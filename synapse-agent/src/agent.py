import os
import json
import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from google import genai
from google.genai import types
from playwright.async_api import async_playwright

# Load environment variables from the .env file in the synapse-agent directory
# Load from multiple possible locations to ensure it works
env_paths = [
    os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'),  # ../synapse-agent/.env
    os.path.join(os.path.dirname(__file__), '..', '.env'),  # synapse-agent/.env
    '.env'  # current directory
]
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break

# Import tools with fallback for both package and direct execution
try:
    from . import tools
except ImportError:
    import tools

class SourcingAgent:
    """
    The Sourcing Agent, now refactored for a streamlined, end-to-end workflow.
    It uses the LinkedInParser for all scraping and outreach and makes a single,
    efficient LLM call per candidate to get a full analysis.
    """
    def __init__(self, model="gemini-1.5-flash"):
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("The GEMINI_API_KEY is not set in the environment.")
        # Create the client - it automatically picks up GEMINI_API_KEY from environment
        self.client = genai.Client()
        self.model_name = model

        self.session_cookie = os.environ.get("LINKEDIN_SESSION_COOKIE")
        if not self.session_cookie:
            print("Warning: LINKEDIN_SESSION_COOKIE not set. The agent cannot run.")

    async def _generate_search_query(self, job_description: str) -> str:
        """
        Uses the LLM to generate a concise, effective search query from a job description.
        """
        print("Generating a targeted search query from the job description...")
        try:
            prompt = f"""
            Analyze the following job description and distill it into a concise Google search query of 5-7 keywords to find relevant LinkedIn profiles.
            Focus on the core job title, key technologies, and location.

            **Example:**

            *Job Description:*
            "Software Engineer, ML Research at Windsurf in Mountain View, CA. We're a Forbes AI 50 company building developer productivity tools with proprietary LLMs. Responsibilities include training and fine-tuning LLMs, designing experiments, and converting ML discoveries into scalable product features. Requires 2+ years in software engineering, experience with large production neural networks, and a strong GPA from a top CS program. Familiarity with Copilot or ChatGPT is preferred."

            *Optimal Google Search Query:*
            "Software Engineer Machine Learning Research LLM Mountain View"

            **Your Turn:**

            *Job Description:*
            ---
            {job_description}
            ---

            *Optimal Google Search Query:*
            """
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=50
                )
            )
            
            # Clean up the response
            query = response.text.strip().replace('"', '')
            print(f"Generated Search Query: {query}")
            return query
        except Exception as e:
            print(f"Error generating search query: {e}")
            # Fallback to a simple query if generation fails
            return " ".join(job_description.split()[:10])


    async def _run_playwright_scraping(self, profile_urls: list, job_description: str, send_outreach: bool):
        """
        Run Playwright scraping in a way that's compatible with Windows asyncio
        """
        def run_in_new_loop():
            # Set Windows policy for this thread
            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(self._scrape_profiles_with_playwright(profile_urls, job_description, send_outreach))
            finally:
                loop.close()
        
        # Run in thread pool to avoid blocking
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_in_new_loop)
            return future.result()

    async def _scrape_profiles_with_playwright(self, profile_urls: list, job_description: str, send_outreach: bool):
        """
        The actual Playwright scraping logic
        """
        results = []
        
        async with async_playwright() as p:
            # Launch browser with Windows-compatible options
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
            )
            page = await browser.new_page()
            
            # Set LinkedIn session cookie if available
            if self.session_cookie:
                await page.context.add_cookies([{
                    'name': 'li_at',
                    'value': self.session_cookie,
                    'domain': '.linkedin.com',
                    'path': '/'
                }])
                print("LinkedIn session cookie set")

            parser = tools.LinkedInParser(page)
            for url in profile_urls:
                print(f"Scraping profile: {url}")
                profile_data = await parser.scrape_profile(url)
                
                if profile_data and not profile_data.get("error"):
                    profile_data["linkedin_url"] = url # Ensure URL is in the data
                    print(f"Analyzing candidate: {profile_data.get('name')}")
                    analysis_result = self._get_llm_analysis(profile_data, job_description)
                    
                    # Step 4 (Optional): Send Outreach
                    if send_outreach and analysis_result.get("outreach_message"):
                        print(f"Sending connection request to: {url}")
                        success = await parser.send_connection_request(url, analysis_result["outreach_message"])
                        analysis_result["outreach_sent"] = success
                    
                    results.append(analysis_result)
                else:
                    print(f"Skipping analysis for {url} due to scraping error or empty profile.")
                    results.append({
                        "url": url,
                        "status": "Failed to scrape or process",
                        "details": profile_data.get("error", "No data found")
                    })
                await asyncio.sleep(2) # Be respectful to LinkedIn's servers
            await browser.close()
        
        return results

    def _get_llm_analysis(self, profile_data: dict, job_description: str) -> dict:
        """
        Analyzes the structured profile data against the job description using a single, comprehensive LLM prompt.
        """
        profile_text = json.dumps(profile_data, indent=2)
        profile_url = profile_data.get("linkedin_url", "N/A") # Assuming the URL is passed in profile_data

        master_prompt = f"""
You are an expert AI Talent Sourcer. Your task is to analyze a candidate's structured profile data against a specific job description and return a structured JSON object.

**Job Description:**
{job_description}

**Candidate's Profile URL:**
{profile_url}

**Candidate's Profile Data (JSON):**
{profile_text}

**Your Task:**
Analyze the candidate's profile and return a single JSON object with the following structure. Do not include any text outside of the JSON object.

**Fit Score Rubric:**
- **Education (20%):** Score 9-10 for elite schools (MIT, Stanford, CMU, etc.), 7-8 for other strong CS schools, 5-6 for standard universities.
- **Career Trajectory (20%):** Score 8-10 for clear progression with promotions, 6-8 for steady growth, 3-5 for limited progression.
- **Company Relevance (15%):** Score 9-10 for top tech/AI companies (Google, Meta, OpenAI), 7-8 for relevant tech startups, 5-6 for any software experience.
- **Experience Match (25%):** Score 9-10 for direct experience training production LLMs or similar large NNs, 7-8 for strong ML research/engineering overlap, 5-6 for general backend experience.
- **Location Match (10%):** Score 10 for Mountain View/Bay Area, 8 for same state/willing to relocate, 6 for remote-friendly profiles.
- **Tenure (10%):** Score 9-10 for 2-4 years average tenure, 6-8 for 1-2 years, 3-5 for job hopping (<1 year).

**Required JSON Output Format:**
{{
  "name": "{profile_data.get('name', 'N/A')}",
  "linkedin_url": "{profile_url}",
  "fit_score": "Calculate the final weighted score from 1.0 to 10.0",
  "score_breakdown": {{
    "education": 0.0,
    "trajectory": 0.0,
    "company": 0.0,
    "skills": 0.0,
    "location": 0.0,
    "tenure": 0.0
  }},
  "reasoning": "A concise paragraph explaining your scoring decisions, referencing specific details from their profile.",
  "confidence_score": "A float from 0.0 to 1.0 indicating your confidence based on the completeness of the profile data.",
  "outreach_message": "A personalized, professional 3-4 sentence LinkedIn message. Reference a specific project or company from their profile and connect it to the job. Mention the role title from the job description."
}}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=master_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )
            # The response should be a JSON object now
            response_text = response.text.strip()
            return json.loads(response_text)
        except Exception as e:
            print(f"Error during LLM analysis for {profile_url}: {e}")
            # Fallback to the general llm_call if the structured one fails
            fallback_response = tools.llm_call(master_prompt)
            if fallback_response:
                try:
                    return json.loads(fallback_response)
                except json.JSONDecodeError as json_err:
                    print(f"JSON decode error in fallback: {json_err}")
                    # Return a basic structure with the available data
                    return {
                        "name": profile_data.get('name', 'N/A'),
                        "linkedin_url": profile_url,
                        "fit_score": 5.0,
                        "score_breakdown": {
                            "education": 5.0,
                            "trajectory": 5.0,
                            "company": 5.0,
                            "skills": 5.0,
                            "location": 5.0,
                            "tenure": 5.0
                        },
                        "reasoning": "Could not analyze profile due to LLM processing error",
                        "confidence_score": 0.1,
                        "outreach_message": f"Hi {profile_data.get('name', 'there')}, I came across your profile and would love to connect!"
                    }
            else:
                # Return basic fallback structure
                return {
                    "name": profile_data.get('name', 'N/A'),
                    "linkedin_url": profile_url,
                    "fit_score": 5.0,
                    "score_breakdown": {
                        "education": 5.0,
                        "trajectory": 5.0,
                        "company": 5.0,
                        "skills": 5.0,
                        "location": 5.0,
                        "tenure": 5.0
                    },
                    "reasoning": "Could not analyze profile due to LLM processing error",
                    "confidence_score": 0.1,
                    "outreach_message": f"Hi {profile_data.get('name', 'there')}, I came across your profile and would love to connect!"
                }

    async def run(self, job_description: str, search_query: str, send_outreach: bool = False, num_results: int = 10):
        """
        The main pipeline: search, scrape, analyze, and optionally send outreach.
        Now using threaded approach for Windows compatibility.
        """
        if not self.session_cookie:
            return {"error": "Sourcing Agent is not available. Check server logs for initialization errors (e.g., missing LINKEDIN_SESSION_COOKIE)."}

        print("Starting the sourcing process...")
        
        # Step 1: Generate search query if not provided
        if not search_query:
            print("No search query provided, generating one from job description...")
            search_query = await self._generate_search_query(job_description)
            print(f"Generated search query: {search_query}")

        # Step 2: Find candidate URLs
        profile_urls = await tools.search_linkedin_urls(search_query, num_results)
        if not profile_urls:
            print("No LinkedIn profile URLs found.")
            return {"message": "No LinkedIn profile URLs found for the given query."}

        print(f"Found {len(profile_urls)} candidate profiles. Starting scraping and analysis...")

        # Step 3 & 4: Scrape and Analyze using threaded approach for Windows compatibility
        try:
            results = await self._run_playwright_scraping(profile_urls, job_description, send_outreach)
            print("Sourcing process completed.")
            return {"results": results, "search_query_used": search_query}
        except Exception as e:
            print(f"An error occurred during Playwright operations: {e}")
            return {"error": f"Failed to process candidates due to a browser automation error: {e}"}

    async def search_linkedin(self, job_description: str, num_results: int = 10):
        """
        # 2. Candidate Discovery
        Find LinkedIn profile URLs based on job description
        Returns: [{"name": "John Doe", "linkedin_url": "...", "headline": "..."}]
        """
        search_query = f"site:linkedin.com/in/ \"{job_description[:100]}\""
        profile_urls = await tools.search_linkedin_urls(search_query, num_results)
        
        candidates = []
        for url in profile_urls:
            candidates.append({
                "name": "Profile Found",
                "linkedin_url": url,
                "headline": "To be scraped"
            })
        
        return candidates

    async def score_candidates(self, candidates: list, job_description: str):
        """
        # 3. Fit Scoring
        Score candidates against job requirements
        Returns: [{"name": "...", "score": 8.5, "breakdown": {...}}]
        """
        scored_results = []
        
        for candidate in candidates:
            if "linkedin_url" in candidate:
                # Use the existing scraping and analysis pipeline
                search_query = f"site:linkedin.com {candidate['linkedin_url']}"
                raw_results = await self._run_playwright_scraping([candidate['linkedin_url']], job_description, False)
                
                if raw_results and len(raw_results) > 0:
                    result = raw_results[0]
                    if isinstance(result, dict) and "fit_score" in result:
                        scored_results.append({
                            "name": result.get("name", candidate.get("name", "Unknown")),
                            "score": result.get("fit_score", 0),
                            "breakdown": result.get("score_breakdown", {}),
                            "linkedin_url": candidate["linkedin_url"],
                            "reasoning": result.get("reasoning", ""),
                            "confidence_score": result.get("confidence_score", 0)
                        })
        
        return scored_results

    async def generate_outreach(self, candidates: list, job_description: str):
        """
        # 4. Message Generation
        Generate personalized outreach messages
        Returns: [{"candidate": "...", "message": "Hi John, I noticed..."}]
        """
        messages = []
        
        for candidate in candidates:
            if "linkedin_url" in candidate:
                # Use the existing pipeline to get outreach message
                raw_results = await self._run_playwright_scraping([candidate['linkedin_url']], job_description, False)
                
                if raw_results and len(raw_results) > 0:
                    result = raw_results[0]
                    if isinstance(result, dict) and "outreach_message" in result:
                        messages.append({
                            "candidate": result.get("name", candidate.get("name", "Unknown")),
                            "linkedin_url": candidate["linkedin_url"],
                            "message": result.get("outreach_message", ""),
                            "fit_score": result.get("fit_score", 0)
                        })
        
        return messages
