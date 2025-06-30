#!/usr/bin/env python3
"""
Environment setup helper for LinkedIn Sourcing Agent
Helps you set up the required environment variables
"""

import os
import sys

def create_env_template():
    """Create a .env template file"""
    env_content = """# LinkedIn Sourcing Agent Environment Variables
# Copy this file to .env and fill in your actual values

# LinkedIn Session Cookie (from browser developer tools)
# Go to linkedin.com, open dev tools > Application > Cookies
# Copy the 'li_at' cookie value
LINKEDIN_SESSION_COOKIE=your_linkedin_session_cookie_here

# Google Custom Search API
# Get from: https://developers.google.com/custom-search/v1/introduction
GOOGLE_API_KEY=your_google_api_key_here

# Custom Search Engine ID
# Create at: https://cse.google.com/
# Configure to search LinkedIn profiles
CUSTOM_SEARCH_ENGINE_ID=your_custom_search_engine_id_here

# Gemini API Key (for AI scoring and outreach generation)
# Get from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Rate limiting settings
MAX_REQUESTS_PER_MINUTE=10
SEARCH_DELAY_SECONDS=2
"""
    
    with open(".env.template", "w") as f:
        f.write(env_content)
    
    print("✅ Created .env.template file")
    print("📝 Please copy this to .env and fill in your actual API keys")

def check_env_file():
    """Check if .env file exists and has required variables"""
    if not os.path.exists(".env"):
        print("❌ .env file not found")
        return False
    
    required_vars = [
        "LINKEDIN_SESSION_COOKIE",
        "GOOGLE_API_KEY", 
        "CUSTOM_SEARCH_ENGINE_ID",
        "GEMINI_API_KEY"
    ]
    
    missing = []
    with open(".env", "r") as f:
        content = f.read()
        for var in required_vars:
            if f"{var}=" not in content or f"{var}=your_" in content:
                missing.append(var)
    
    if missing:
        print("⚠️ Missing or incomplete environment variables:")
        for var in missing:
            print(f"   - {var}")
        return False
    else:
        print("✅ All required environment variables found")
        return True

def setup_instructions():
    """Print setup instructions"""
    print("\n🔧 SETUP INSTRUCTIONS")
    print("=" * 50)
    
    print("\n1. LinkedIn Session Cookie:")
    print("   - Go to linkedin.com and log in")
    print("   - Open browser developer tools (F12)")
    print("   - Go to Application/Storage > Cookies")
    print("   - Find 'li_at' cookie and copy its value")
    
    print("\n2. Google Custom Search API:")
    print("   - Go to: https://developers.google.com/custom-search/v1/introduction")
    print("   - Enable Custom Search API")
    print("   - Create credentials and get API key")
    
    print("\n3. Custom Search Engine:")
    print("   - Go to: https://cse.google.com/")
    print("   - Create new search engine")
    print("   - Add 'linkedin.com/in/*' as a site to search")
    print("   - Copy the Search Engine ID")
    
    print("\n4. Gemini API Key:")
    print("   - Go to: https://aistudio.google.com/app/apikey")
    print("   - Create new API key")
    print("   - Copy the key")
    
    print("\n5. Install Dependencies:")
    print("   pip install -r requirements.txt")
    print("   playwright install chromium")

def main():
    print("🚀 LinkedIn Sourcing Agent - Environment Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("api.py"):
        print("❌ Please run this script from the synapse-agent directory")
        print("   cd synapse-agent")
        print("   python ../setup_env.py")
        return
    
    # Create template if needed
    if not os.path.exists(".env") and not os.path.exists(".env.template"):
        create_env_template()
    
    # Check environment
    env_ok = check_env_file()
    
    if not env_ok:
        setup_instructions()
        print("\n📝 Next steps:")
        print("1. Fill in your .env file with actual API keys")
        print("2. Run: python ../test_runner.py")
        print("3. Start the server: python startup.py")
    else:
        print("\n🎉 Environment setup looks good!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Install Playwright: playwright install chromium") 
        print("3. Test everything: python ../test_runner.py")
        print("4. Start the server: python startup.py")

if __name__ == "__main__":
    main()
