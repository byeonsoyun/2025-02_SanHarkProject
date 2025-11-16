#!/usr/bin/env python3
import requests
import os
import sys
from pathlib import Path

# Load environment variables
sys.path.append('.')
try:
    from load_env import load_env
    load_env()
except ImportError:
    pass

def test_gpu_server():
    """Test connection to external GPU server"""
    
    # Get server URL from environment or use default
    server_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    print(f"Testing connection to: {server_url}")
    
    try:
        # Test basic connection
        response = requests.get(f"{server_url}/api/tags", timeout=10)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Connection successful!")
            print(f"Available models: {[m['name'] for m in models]}")
            
            # Test generation with the configured model
            model = os.getenv('OLLAMA_MODEL', 'llama3.2')
            test_response = requests.post(
                f"{server_url}/api/generate",
                json={
                    "model": model,
                    "prompt": "Hello, this is a test.",
                    "stream": False
                },
                timeout=30
            )
            
            if test_response.status_code == 200:
                print("✅ Generation test successful!")
                print(f"Response: {test_response.json()['response'][:100]}...")
            else:
                print(f"❌ Generation test failed: {test_response.status_code}")
                print(f"Error: {test_response.text}")
                
        else:
            print(f"❌ Connection failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        print("Possible issues:")
        print("1. Server IP/port incorrect")
        print("2. Server not running")
        print("3. Firewall blocking connection")
        print("4. Network connectivity issues")
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_gpu_server()
