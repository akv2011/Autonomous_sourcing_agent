#!/usr/bin/env python3
"""
Debug script to test Google Custom Search API
"""

import os
import sys
from dotenv import load_dotenv
from googleapiclient.discovery import build

# Load environment
load_dotenv('.env')

def test_google_search():
    """Test Google Custom Search API"""
    print("🔍 Testing Google Custom Search API...")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("CUSTOM_SEARCH_ENGINE_ID")
    
    print(f"API Key: {'✓ Set' if api_key else '✗ Missing'}")
    print(f"CSE ID: {'✓ Set' if cse_id else '✗ Missing'}")
    
    if not api_key or not cse_id:
        print("❌ Missing API credentials")
        return
    
    try:
        service = build("customsearch", "v1", developerKey=api_key)
        
        # Test 1: Simple LinkedIn search
        print("\n📝 Test 1: Simple LinkedIn search")
        query = "software engineer site:linkedin.com/in/"
        print(f"Query: {query}")
        
        res = service.cse().list(q=query, cx=cse_id, num=3).execute()
        
        if 'items' in res:
            print(f"✓ Found {len(res['items'])} results")
            for i, item in enumerate(res['items'][:2]):
                print(f"  {i+1}. {item['title']}")
                print(f"     {item['link']}")
        else:
            print("❌ No results found")
            print(f"Response: {res}")
            
        # Test 2: General search (no site restriction)
        print("\n📝 Test 2: General search")
        query = "software engineer"
        print(f"Query: {query}")
        
        res = service.cse().list(q=query, cx=cse_id, num=3).execute()
        
        if 'items' in res:
            print(f"✓ Found {len(res['items'])} results")
            for i, item in enumerate(res['items'][:2]):
                print(f"  {i+1}. {item['title']}")
        else:
            print("❌ No results found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e)}")

if __name__ == "__main__":
    test_google_search()
