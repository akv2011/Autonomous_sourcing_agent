#!/usr/bin/env python3
"""
Quick test runner for the LinkedIn Sourcing Agent
Tests all endpoints and core functionality
"""

import requests
import json
import time
import sys
import os

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_JOB_DESCRIPTION = "Senior Python Developer with FastAPI experience and machine learning background"
TEST_COMPANY_DESCRIPTION = "Tech startup building AI-powered recruitment tools"

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_web_interface():
    """Test if web interface is accessible"""
    print("🔍 Testing web interface...")
    try:
        response = requests.get(f"{BASE_URL}/web")
        if response.status_code == 200:
            print("✅ Web interface accessible")
            return True
        else:
            print(f"❌ Web interface failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Web interface error: {e}")
        return False

def test_linkedin_search():
    """Test LinkedIn search endpoint"""
    print("🔍 Testing LinkedIn search...")
    try:
        payload = {
            "query": "Python Developer",
            "max_results": 5
        }
        response = requests.post(f"{BASE_URL}/search-linkedin/", 
                               json=payload, 
                               timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                print(f"✅ LinkedIn search passed - Found {len(data['candidates'])} candidates")
                return True, data["candidates"]
            else:
                print("⚠️ LinkedIn search returned no candidates")
                return False, []
        else:
            print(f"❌ LinkedIn search failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False, []
    except Exception as e:
        print(f"❌ LinkedIn search error: {e}")
        return False, []

def test_score_candidates(candidates):
    """Test candidate scoring endpoint"""
    print("🔍 Testing candidate scoring...")
    try:
        if not candidates:
            print("⚠️ No candidates to score, skipping...")
            return False, []
        
        # Take first 3 candidates for testing
        test_candidates = candidates[:3]
        payload = {
            "candidates": test_candidates,
            "job_description": TEST_JOB_DESCRIPTION
        }
        response = requests.post(f"{BASE_URL}/score-candidates/", 
                               json=payload, 
                               timeout=60)
        if response.status_code == 200:
            data = response.json()
            if "scored_candidates" in data:
                scored = data["scored_candidates"]
                print(f"✅ Candidate scoring passed - Scored {len(scored)} candidates")
                for candidate in scored[:2]:  # Show first 2
                    print(f"   - {candidate.get('name', 'Unknown')}: {candidate.get('fit_score', 0)}/100")
                return True, scored
            else:
                print("❌ Scoring returned invalid format")
                return False, []
        else:
            print(f"❌ Candidate scoring failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False, []
    except Exception as e:
        print(f"❌ Candidate scoring error: {e}")
        return False, []

def test_outreach_generation(candidates):
    """Test outreach generation endpoint"""
    print("🔍 Testing outreach generation...")
    try:
        if not candidates:
            print("⚠️ No candidates for outreach, skipping...")
            return False
        
        # Use first candidate
        candidate = candidates[0]
        payload = {
            "candidate": candidate,
            "job_description": TEST_JOB_DESCRIPTION,
            "company_description": TEST_COMPANY_DESCRIPTION
        }
        response = requests.post(f"{BASE_URL}/generate-outreach/", 
                               json=payload, 
                               timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "outreach_message" in data:
                message = data["outreach_message"]
                print(f"✅ Outreach generation passed")
                print(f"   Sample message: {message[:100]}...")
                return True
            else:
                print("❌ Outreach generation returned invalid format")
                return False
        else:
            print(f"❌ Outreach generation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Outreach generation error: {e}")
        return False

def test_sync_job():
    """Test the synchronous job endpoint"""
    print("🔍 Testing synchronous job execution...")
    try:
        payload = {
            "job_description": TEST_JOB_DESCRIPTION,
            "company_description": TEST_COMPANY_DESCRIPTION,
            "top_n": 5
        }
        print("   (This may take 30-60 seconds...)")
        response = requests.post(f"{BASE_URL}/run-sourcing-job-sync/", 
                               json=payload, 
                               timeout=120)
        if response.status_code == 200:
            data = response.json()
            if "results" in data and "job_id" in data:
                results = data["results"]
                job_id = data["job_id"]
                print(f"✅ Sync job passed - Job ID: {job_id}")
                print(f"   Found {len(results)} candidates")
                if results:
                    best = max(results, key=lambda x: x.get('fit_score', 0))
                    print(f"   Best candidate: {best.get('name', 'Unknown')} (Score: {best.get('fit_score', 0)})")
                return True, job_id
            else:
                print("❌ Sync job returned invalid format")
                return False, None
        else:
            print(f"❌ Sync job failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ Sync job error: {e}")
        return False, None

def test_results_retrieval(job_id):
    """Test results retrieval endpoint"""
    print("🔍 Testing results retrieval...")
    try:
        if not job_id:
            print("⚠️ No job ID to test, skipping...")
            return False
        
        response = requests.get(f"{BASE_URL}/results/{job_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Results retrieval passed")
            return True
        else:
            print(f"❌ Results retrieval failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Results retrieval error: {e}")
        return False

def main():
    print("🚀 LinkedIn Sourcing Agent - Test Runner")
    print("=" * 50)
    
    # Check if server is running
    print("Checking if server is running...")
    if not test_health():
        print("\n❌ Server is not running or not accessible")
        print("Please start the server first:")
        print("   cd synapse-agent")
        print("   python startup.py")
        return
    
    print("\n🧪 Running comprehensive tests...\n")
    
    # Track results
    results = {
        "health": False,
        "web": False,
        "linkedin_search": False,
        "scoring": False,
        "outreach": False,
        "sync_job": False,
        "results_retrieval": False
    }
    
    # Run tests
    results["health"] = test_health()
    results["web"] = test_web_interface()
    
    # Test LinkedIn search and dependent features
    search_success, candidates = test_linkedin_search()
    results["linkedin_search"] = search_success
    
    if search_success:
        scoring_success, scored_candidates = test_score_candidates(candidates)
        results["scoring"] = scoring_success
        
        if scoring_success:
            results["outreach"] = test_outreach_generation(scored_candidates)
    
    # Test full pipeline
    sync_success, job_id = test_sync_job()
    results["sync_job"] = sync_success
    
    if sync_success:
        results["results_retrieval"] = test_results_retrieval(job_id)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title():<20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your agent is ready for demo!")
        print("\nNext steps:")
        print("1. Open http://localhost:8000/web for the web interface")
        print("2. Record your demo video")
        print("3. Submit to the hackathon!")
    elif passed >= total * 0.7:
        print("\n⚠️ Most tests passed, but check the failed ones")
        print("Your agent should still work for the demo")
    else:
        print("\n❌ Several tests failed - please check your setup")
        print("1. Verify your .env file has all required API keys")
        print("2. Check that LinkedIn session cookie is valid")
        print("3. Ensure all dependencies are installed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
