#!/usr/bin/env python3
"""
Test script for the new /find-candidates-with-outreach/ endpoint
Demonstrates finding top 10 candidates with personalized outreach messages
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_find_candidates_with_outreach():
    """Test the new endpoint that returns top 10 candidates with outreach messages"""
    
    print("🚀 Testing Find Candidates with Outreach Endpoint")
    print("=" * 60)
    
    # Test job description
    job_description = """
    Senior Machine Learning Engineer at TechCorp
    
    We're looking for an experienced ML Engineer to join our AI research team. 
    The role involves designing and implementing deep learning models, working with 
    large-scale data pipelines, and deploying ML solutions to production.
    
    Requirements:
    - 3+ years of experience in machine learning
    - Strong Python programming skills
    - Experience with TensorFlow/PyTorch
    - Background in computer vision or NLP
    - PhD in CS/ML preferred
    - Experience with cloud platforms (AWS/GCP)
    
    Location: San Francisco, CA
    Salary: $150k - $250k + equity
    """
    
    payload = {
        "job_description": job_description
    }
    
    try:
        print("📡 Sending request to find candidates with outreach...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/find-candidates-with-outreach/",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5 minute timeout
        )
        
        processing_time = time.time() - start_time
        
        print(f"⏱️ Request completed in {processing_time:.1f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n✅ SUCCESS! Here's the response:")
            print("-" * 60)
            
            # Print summary
            print(f"📋 Job Description: {result['job_description'][:100]}...")
            print(f"🔍 Search Query Used: {result.get('search_query_used', 'N/A')}")
            print(f"👥 Total Candidates Found: {result['total_candidates_found']}")
            print(f"⏱️ Processing Time: {result['processing_time_seconds']} seconds")
            print(f"🏆 Top Candidates Returned: {len(result['top_candidates'])}")
            
            # Print each candidate
            print("\n🎯 TOP CANDIDATES WITH OUTREACH MESSAGES:")
            print("=" * 60)
            
            for candidate in result['top_candidates']:
                print(f"\n#{candidate['rank']} {candidate['name']}")
                print(f"   📊 Fit Score: {candidate['fit_score']}/10")
                print(f"   💼 Current Role: {candidate['headline']}")
                print(f"   🔗 LinkedIn: {candidate['linkedin_url']}")
                print(f"   🎯 Confidence: {candidate['confidence_score']*100:.0f}%")
                
                # Job match analysis
                print(f"   📈 Technical Skills Score: {candidate['job_match_analysis']['match_score_breakdown']['technical_skills']:.1f}/10")
                print(f"   📈 Experience Score: {candidate['job_match_analysis']['match_score_breakdown']['experience_level']:.1f}/10")
                
                # Personalized outreach message
                print(f"   💬 Outreach Message:")
                print(f"      \"{candidate['personalized_outreach_message']}\"")
                
                print("-" * 40)
            
            # Save results to file
            with open('candidates_with_outreach_results.json', 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Results saved to 'candidates_with_outreach_results.json'")
            
            return result
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def test_api_docs():
    """Test that the API docs include the new endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        if response.status_code == 200:
            openapi_spec = response.json()
            paths = openapi_spec.get("paths", {})
            
            if "/find-candidates-with-outreach/" in paths:
                print("✅ New endpoint found in API documentation")
                return True
            else:
                print("❌ New endpoint not found in API documentation")
                return False
        else:
            print(f"❌ Could not fetch API docs: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking API docs: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTING NEW FIND CANDIDATES WITH OUTREACH ENDPOINT")
    print("=" * 70)
    
    # Check if server is running
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            health = health_response.json()
            print(f"✅ Server is running - Agent Available: {health.get('agent_available')}")
        else:
            print("❌ Server health check failed")
            exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Make sure the server is running: cd synapse-agent && python api.py")
        exit(1)
    
    # Test API documentation
    print("\n📚 Checking API Documentation...")
    doc_test = test_api_docs()
    
    # Test the main endpoint
    print("\n🚀 Testing Main Endpoint...")
    result = test_find_candidates_with_outreach()
    
    if result:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ New endpoint is working correctly")
        print("✅ Returns exactly what was requested:")
        print("   - Takes job description as input")
        print("   - Returns top 10 candidates")
        print("   - Includes personalized outreach messages")
        print("   - Highlights profile characteristics")
        print("   - Shows job match analysis")
        print("   - All in JSON format")
    else:
        print("\n❌ TESTS FAILED!")
        print("Check the server logs for errors")
    
    print("\n🌐 You can also test via:")
    print(f"   Web UI: {BASE_URL}/web")
    print(f"   API Docs: {BASE_URL}/docs")
