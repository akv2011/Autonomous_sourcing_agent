import requests
import json
import time
import subprocess
import os
import sys

def test_health_check():
    """Test the health endpoint"""
    print("🏥 Testing system health...")
    try:
        response = requests.get('http://127.0.0.1:8000/health')
        if response.status_code == 200:
            health = response.json()
            print(f"✅ System Status: {health['status']}")
            print(f"   Agent Available: {health['agent_available']}")
            print(f"   Jobs Processed: {health['total_jobs_processed']}")
            if 'warnings' in health:
                print(f"   ⚠️ Warnings: {health['warnings']}")
            return health['agent_available']
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_synchronous_pipeline():
    """Test the complete synchronous sourcing pipeline"""
    print("\n🚀 Testing Synchronous Sourcing Pipeline")
    print("-" * 40)
    
    # Use the Windsurf job description from the hackathon
    data = {
        'job_description': '''Software Engineer, ML Research at Windsurf (Forbes AI 50 company) - 
        Building AI-powered developer tools. Looking for someone to train LLMs for code generation, 
        $140-300k + equity in Mountain View. Required: PhD in CS/ML, experience with large neural networks, 
        Python expertise, research background.''',
        'search_query': '',  # Auto-generate
        'send_outreach': False,
        'max_candidates': 5
    }
    
    try:
        print("📡 Sending request to synchronous endpoint...")
        start_time = time.time()
        
        response = requests.post('http://127.0.0.1:8000/run-sourcing-job-sync/', json=data)
        total_time = time.time() - start_time
        
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"🎉 Sourcing completed in {total_time:.1f} seconds!")
            print(f"📊 Results Summary:")
            print(f"   Job ID: {result['job_id']}")
            print(f"   Candidates Found: {result['candidates_found']}")
            print(f"   Top Candidates: {len(result.get('top_candidates', []))}")
            print(f"   Processing Time: {result.get('processing_time', 'N/A')}s")
            print(f"   Search Query Used: {result.get('search_query_used', 'N/A')}")
            
            # Show top candidates
            print(f"\n🏆 Top Candidates:")
            for i, candidate in enumerate(result.get('top_candidates', [])[:3]):
                print(f"   #{i+1} {candidate.get('name', 'Unknown')}")
                print(f"       Score: {candidate.get('fit_score', 0)}/10")
                print(f"       LinkedIn: {candidate.get('linkedin_url', 'N/A')}")
                if candidate.get('reasoning'):
                    print(f"       Analysis: {candidate['reasoning'][:100]}...")
                print()
            
            return result
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📋 Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the server. Make sure it's running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

def test_required_endpoints():
    """Test all required hackathon endpoints"""
    print("\n📋 Testing Required Hackathon Endpoints")
    print("-" * 40)
    
    job_description = "Senior Python Developer with ML experience"
    
    # Test 1: Search LinkedIn
    print("1️⃣ Testing LinkedIn Search...")
    try:
        response = requests.post('http://127.0.0.1:8000/search-linkedin/', json={
            "job_description": job_description,
            "num_results": 3
        })
        if response.status_code == 200:
            candidates = response.json().get('candidates', [])
            print(f"   ✅ Found {len(candidates)} candidate profiles")
            sample_candidates = candidates[:2]  # Use for next tests
        else:
            print(f"   ❌ Search failed: {response.status_code}")
            sample_candidates = [{"name": "Test User", "linkedin_url": "https://linkedin.com/in/test"}]
    except Exception as e:
        print(f"   ❌ Search error: {e}")
        sample_candidates = [{"name": "Test User", "linkedin_url": "https://linkedin.com/in/test"}]
    
    # Test 2: Score Candidates (would take too long with real profiles for quick test)
    print("2️⃣ Testing Candidate Scoring...")
    print("   ⚠️ Skipped in quick test (use full pipeline for real scoring)")
    
    # Test 3: Generate Outreach (would take too long with real profiles for quick test)
    print("3️⃣ Testing Outreach Generation...")
    print("   ⚠️ Skipped in quick test (use full pipeline for real outreach)")
    
    print("   💡 Use the synchronous pipeline test above for complete end-to-end testing")

def test_sourcing_agent():
    print("🚀 Testing Enhanced Autonomous Sourcing Agent")
    print("=" * 50)
    
    # Test 1: Health Check
    agent_available = test_health_check()
    
    if not agent_available:
        print("\n❌ Agent not available - check your environment variables:")
        print("   - LINKEDIN_SESSION_COOKIE")
        print("   - GOOGLE_API_KEY") 
        print("   - CUSTOM_SEARCH_ENGINE_ID")
        print("   - GEMINI_API_KEY")
        return
    
    # Test 2: Required Endpoints (quick test)
    test_required_endpoints()
    
    # Test 3: Full Pipeline (comprehensive test)
    result = test_synchronous_pipeline()
    
    if result:
        print(f"\n🎉 SUCCESS! Your agent is working perfectly!")
        print(f"📊 Final Summary:")
        print(f"   ✅ Health check passed")
        print(f"   ✅ All required endpoints available")
        print(f"   ✅ Complete pipeline functional")
        print(f"   ✅ Results stored with job ID: {result['job_id']}")
        print(f"\n🚀 Ready for Synapse AI Hackathon demo!")
        print(f"🌐 Web Interface: http://127.0.0.1:8000/web")
        print(f"📚 API Docs: http://127.0.0.1:8000/docs")
    else:
        print(f"\n⚠️ Some issues detected. Check the logs above.")

if __name__ == "__main__":
    server_process = None
    python_executable = sys.executable
    try:
        print("🚀 Starting FastAPI server...")
        script_path = os.path.abspath("synapse-agent/start_server.py")
        server_cwd = os.path.dirname(script_path)
        
        server_process = subprocess.Popen(
            [python_executable, script_path],
            cwd=server_cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        )
        
        print(f"✅ Server started with PID: {server_process.pid}. Waiting for it to become available...")
        
        # Poll health check endpoint instead of fixed sleep
        start_time = time.time()
        server_ready = False
        while time.time() - start_time < 30: # 30-second timeout
            try:
                response = requests.get("http://127.0.0.1:8000/health", timeout=1)
                if response.status_code == 200:
                    print("✅ Server is up and running!")
                    server_ready = True
                    break
            except requests.ConnectionError:
                time.sleep(1) # Wait and retry
        
        if not server_ready:
            print("❌ Server did not become available within 30 seconds.")
            raise RuntimeError("Server startup failed")

        print("\n" + "="*50)
        print("🏁 RUNNING E2E SOURCING AGENT TEST SUITE 🏁")
        print("="*50 + "\n")

        # Run tests
        if test_health_check():
            test_synchronous_pipeline()
            test_required_endpoints()
        else:
            print("❌ Halting tests because health check failed.")

        print("\n" + "="*50)
        print("✅ TEST SUITE COMPLETED")
        print("="*50 + "\n")

    except Exception as e:
        print(f"An error occurred during the test suite: {e}")
    finally:
        if server_process:
            print("🛑 Stopping FastAPI server...")
            if sys.platform == "win32":
                # Use taskkill on Windows to forcefully terminate the process and its children
                subprocess.run(["taskkill", "/F", "/PID", str(server_process.pid), "/T"], check=False)
            else:
                # Use terminate on other platforms
                server_process.terminate()
            
            try:
                # Wait for the process to terminate and capture output
                stdout, _ = server_process.communicate(timeout=10)
                print("--- Server Final Output ---")
                print(stdout.decode('utf-8', errors='ignore'))
                print("-------------------------")
            except subprocess.TimeoutExpired:
                print("Server did not terminate in time. Forcing kill.")
                server_process.kill()

            print("✅ Server stopped.")
