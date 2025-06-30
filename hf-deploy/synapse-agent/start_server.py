#!/usr/bin/env python3
"""
Enhanced startup script for the Synapse AI LinkedIn Sourcing Agent
This script handles environment setup and starts the FastAPI server
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """Set up the environment for the application"""
    # Get the current directory (synapse-agent)
    current_dir = Path(__file__).parent
    
    # Add the current directory to Python path so imports work
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    # Add the src directory to Python path
    src_dir = current_dir / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    
    # Load environment variables
    from dotenv import load_dotenv
    env_file = current_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"[+] Loaded environment from: {env_file}")
        
        # Verify critical variables
        required_vars = ["GEMINI_API_KEY", "GOOGLE_API_KEY", "CUSTOM_SEARCH_ENGINE_ID", "LINKEDIN_SESSION_COOKIE"]
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"[!] Missing environment variables: {', '.join(missing_vars)}")
        else:
            print("[+] All required environment variables are set")
    else:
        print(f"[-] Environment file not found: {env_file}")
        return False
    
    return True

def start_server():
    """Start the FastAPI server"""
    print("Synapse AI LinkedIn Sourcing Agent")
    print("==================================================")
    
    if not setup_environment():
        print("[-] Environment setup failed")
        return
    
    try:
        # Set the PYTHONPATH environment variable
        current_dir = Path(__file__).parent
        env = os.environ.copy()
        env['PYTHONPATH'] = str(current_dir)
        
        print("Starting server...")
        print("Server will be available at: http://localhost:8000")
        print("Web interface: http://localhost:8000/web")
        print("API docs: http://localhost:8000/docs")
        print("\nPress Ctrl+C to stop the server")
        print("--------------------------------------------------")
        
        # Run uvicorn command
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "api:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ]
        
        subprocess.run(cmd, cwd=current_dir, env=env)
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're in the synapse-agent directory")
        print("2. Check that all dependencies are installed: pip install -r requirements.txt")
        print("3. Verify your .env file has all required variables")

if __name__ == "__main__":
    start_server()
