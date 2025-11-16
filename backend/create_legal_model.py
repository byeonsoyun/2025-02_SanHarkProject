#!/usr/bin/env python3
import subprocess
import requests
import os
import sys
from pathlib import Path

# Load environment
sys.path.append('.')
try:
    from load_env import load_env
    load_env()
except ImportError:
    pass

def create_legal_model():
    """Create custom civil law model using Modelfile"""
    
    base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    print("🏗️  Creating custom civil law model...")
    
    try:
        # Create model using Ollama API
        with open('Modelfile.civil-law', 'r') as f:
            modelfile_content = f.read()
        
        response = requests.post(
            f"{base_url}/api/create",
            json={
                "name": "civil-law-expert",
                "modelfile": modelfile_content
            },
            timeout=300  # 5 minutes for model creation
        )
        
        if response.status_code == 200:
            print("✅ Custom model 'civil-law-expert' created successfully!")
            
            # Test the new model
            test_response = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model": "civil-law-expert",
                    "prompt": "계약 위반 시 손해배상 범위에 대해 설명해주세요.",
                    "stream": False
                },
                timeout=60
            )
            
            if test_response.status_code == 200:
                print("✅ Model test successful!")
                print("Sample response:")
                print(test_response.json()['response'][:200] + "...")
                
                # Update .env to use new model
                current_config = ""
                try:
                    with open('.env', 'r') as f:
                        current_config = f.read()
                except FileNotFoundError:
                    pass
                
                # Replace model name
                if 'OLLAMA_MODEL=' in current_config:
                    lines = current_config.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith('OLLAMA_MODEL='):
                            lines[i] = 'OLLAMA_MODEL=civil-law-expert'
                    
                    with open('.env', 'w') as f:
                        f.write('\n'.join(lines))
                    
                    print("✅ Updated .env to use civil-law-expert model")
                else:
                    print("⚠️  Please manually update OLLAMA_MODEL=civil-law-expert in .env")
            else:
                print(f"❌ Model test failed: {test_response.status_code}")
        else:
            print(f"❌ Model creation failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_legal_model()
