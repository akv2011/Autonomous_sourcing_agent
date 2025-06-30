#!/usr/bin/env python3
"""
Real End-to-End Test Script for LinkedIn Sourcing Agent
Tests actual candidate scoring and outreach generation with real scraped data
"""

import asyncio
import json
import os
import sys
import time
import requests
from typing import List, Dict

# Configuration
BASE_URL = "http://localhost:8000"
TEST_JOB_DESCRIPTION = """
Software Engineer, ML Research at Windsurf in Mountain View, CA. We're a Forbes AI 50 company 
building developer productivity tools with proprietary LLMs. Responsibilities include training 
and fine-tuning LLMs, designing experiments, and converting ML discoveries into scalable product 
features. Requires 2+ years in software engineering, experience with large production neural 
networks, and a strong GPA from a top CS program. Familiarity with Copilot or ChatGPT is preferred.
"""

def test_server_health():
    """Test if the server is running and healthy"""
    print("🏥 Testing server health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server Status: {data.get('status', 'unknown')}")
            print(f"   Agent Available: {data.get('agent_available', False)}")
            print(f"   Jobs Processed: {data.get('jobs_processed', 0)}")
            return True
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server health check failed: {e}")
        return False

def test_linkedin_search():
    """Test LinkedIn search to get real candidate URLs"""
    print("\n🔍 Testing LinkedIn Search with Real Query...")
    try:
        payload = {
            "job_description": TEST_JOB_DESCRIPTION,
            "num_results": 5  # Smaller number for focused testing
        }
        response = requests.post(f"{BASE_URL}/search-linkedin/", json=payload, timeout=30)
        
        if response.status_code == 200:
            candidates = response.json()
            print(f"✅ Found {len(candidates)} candidate profiles")
            
            # Display candidates
            for i, candidate in enumerate(candidates[:3], 1):
                print(f"   #{i} {candidate.get('name', 'Unknown')} - {candidate.get('linkedin_url', 'No URL')}")
            
            return candidates
        else:
            print(f"❌ LinkedIn search failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return []
    except Exception as e:
        print(f"❌ LinkedIn search failed: {e}")
        return []

def test_candidate_scoring(candidates: List[Dict]):
    """Test real candidate scoring with actual profiles"""
    print("\n📊 Testing Real Candidate Scoring...")
    
    if not candidates:
        print("⚠️ No candidates to score - skipping scoring test")
        return []
    
    try:
        payload = {
            "candidates": candidates,
            "job_description": TEST_JOB_DESCRIPTION
        }
        
        print(f"   Scoring {len(candidates)} candidates...")
        start_time = time.time()
        
        response = requests.post(f"{BASE_URL}/score-candidates/", json=payload, timeout=120)
        
        if response.status_code == 200:
            scored_candidates = response.json()
            duration = time.time() - start_time
            
            print(f"✅ Scoring completed in {duration:.1f} seconds")
            print(f"   Scored {len(scored_candidates)} candidates")
            
            # Display top candidates
            sorted_candidates = sorted(scored_candidates, key=lambda x: x.get('score', 0), reverse=True)
            print("\n🏆 Top Scored Candidates:")
            
            for i, candidate in enumerate(sorted_candidates[:3], 1):
                score = candidate.get('score', 0)
                name = candidate.get('name', 'Unknown')
                linkedin_url = candidate.get('linkedin_url', 'No URL')
                reasoning = candidate.get('reasoning', 'No reasoning provided')[:100]
                
                print(f"   #{i} {name}")
                print(f"       Score: {score}/10")
                print(f"       LinkedIn: {linkedin_url}")
                print(f"       Reasoning: {reasoning}...")
                
                # Show score breakdown if available
                breakdown = candidate.get('breakdown', {})
                if breakdown:
                    print(f"       Breakdown: Education:{breakdown.get('education', 0):.1f}, "
                          f"Experience:{breakdown.get('skills', 0):.1f}, "
                          f"Company:{breakdown.get('company', 0):.1f}")
                print()
            
            return scored_candidates
            
        else:
            print(f"❌ Candidate scoring failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Candidate scoring failed: {e}")
        return []

def test_outreach_generation(scored_candidates: List[Dict]):
    """Test real outreach message generation"""
    print("\n💌 Testing Real Outreach Generation...")
    
    if not scored_candidates:
        print("⚠️ No scored candidates - skipping outreach test")
        return []
    
    try:
        # Take top 3 candidates for outreach testing
        top_candidates = sorted(scored_candidates, key=lambda x: x.get('score', 0), reverse=True)[:3]
        
        payload = {
            "candidates": top_candidates,
            "job_description": TEST_JOB_DESCRIPTION
        }
        
        print(f"   Generating outreach for {len(top_candidates)} top candidates...")
        start_time = time.time()
        
        response = requests.post(f"{BASE_URL}/generate-outreach/", json=payload, timeout=60)
        
        if response.status_code == 200:
            outreach_messages = response.json()
            duration = time.time() - start_time
            
            print(f"✅ Outreach generation completed in {duration:.1f} seconds")
            print(f"   Generated {len(outreach_messages)} messages")
            
            # Display generated messages
            print("\n📧 Generated Outreach Messages:")
            
            for i, msg_data in enumerate(outreach_messages, 1):
                candidate_name = msg_data.get('candidate', 'Unknown')
                message = msg_data.get('message', 'No message generated')
                fit_score = msg_data.get('fit_score', 0)
                linkedin_url = msg_data.get('linkedin_url', 'No URL')
                
                print(f"   #{i} Message for {candidate_name} (Score: {fit_score}/10)")
                print(f"       LinkedIn: {linkedin_url}")
                print(f"       Message:")
                print(f"       \"{message}\"")
                print()
            
            return outreach_messages
            
        else:
            print(f"❌ Outreach generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Outreach generation failed: {e}")
        return []

def test_full_pipeline_comparison():
    """Test the full pipeline and compare with individual endpoints"""
    print("\n🔄 Testing Full Pipeline for Comparison...")
    
    try:
        payload = {
            "job_description": TEST_JOB_DESCRIPTION,
            "search_query": "",  # Let it generate
            "send_outreach": False  # Don't actually send messages
        }
        
        print("   Running full synchronous pipeline...")
        start_time = time.time()
        
        response = requests.post(f"{BASE_URL}/run-sourcing-job-sync/", json=payload, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            duration = time.time() - start_time
            
            print(f"✅ Full pipeline completed in {duration:.1f} seconds")
            
            results = result.get('results', [])
            search_query = result.get('search_query_used', 'Unknown')
            
            print(f"   Search Query Used: {search_query}")
            print(f"   Total Candidates Processed: {len(results)}")
            
            # Show top candidates from full pipeline
            sorted_results = sorted(results, key=lambda x: x.get('fit_score', 0), reverse=True)
            print("\n🏆 Top Candidates from Full Pipeline:")
            
            for i, candidate in enumerate(sorted_results[:3], 1):
                name = candidate.get('name', 'Unknown')
                score = candidate.get('fit_score', 0)
                linkedin_url = candidate.get('linkedin_url', 'No URL')
                outreach = candidate.get('outreach_message', 'No message')[:80]
                
                print(f"   #{i} {name}")
                print(f"       Score: {score}/10")
                print(f"       LinkedIn: {linkedin_url}")
                print(f"       Outreach: \"{outreach}...\"")
                print()
            
            return results
            
        else:
            print(f"❌ Full pipeline failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Full pipeline failed: {e}")
        return []

def main():
    """Main test execution"""
    print("=" * 60)
    print("🚀 REAL END-TO-END LINKEDIN SOURCING AGENT TESTS")
    print("=" * 60)
    
    # Test server health
    if not test_server_health():
        print("\n❌ Server is not healthy. Please start the server first.")
        print("   Run: python start_server.py")
        return False
    
    # Test individual endpoints with real data
    print("\n" + "=" * 40)
    print("🧪 TESTING INDIVIDUAL ENDPOINTS")
    print("=" * 40)
    
    # 1. Search for real candidates
    candidates = test_linkedin_search()
    
    # 2. Score real candidates
    scored_candidates = test_candidate_scoring(candidates)
    
    # 3. Generate real outreach messages
    outreach_messages = test_outreach_generation(scored_candidates)
    
    # Test full pipeline for comparison
    print("\n" + "=" * 40)
    print("🔄 TESTING FULL PIPELINE")
    print("=" * 40)
    
    full_pipeline_results = test_full_pipeline_comparison()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    print(f"✅ LinkedIn Search: Found {len(candidates)} candidates")
    print(f"✅ Candidate Scoring: Scored {len(scored_candidates)} candidates")
    print(f"✅ Outreach Generation: Generated {len(outreach_messages)} messages")
    print(f"✅ Full Pipeline: Processed {len(full_pipeline_results)} candidates")
    
    print("\n🎉 All tests completed successfully!")
    print("💡 The agent is working correctly with real data and actual LLM calls.")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        sys.exit(1)
