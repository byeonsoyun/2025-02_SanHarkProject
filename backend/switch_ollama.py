#!/usr/bin/env python3
import os
import sys

def switch_to_local():
    """Switch to local Ollama with Korean-only civil law model"""
    config = """# Local Korean-only Civil Law Model (M3 optimized)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=civil-law-korean"""
    
    with open('.env', 'w') as f:
        f.write(config)
    print("✅ Switched to LOCAL with Korean-only civil law model (M3 optimized)")

def switch_to_external():
    """Switch to external GPU server with full civil law model"""
    config = """# External GPU Server with Full Civil Law Model
OLLAMA_BASE_URL=http://10.198.138.249:22434
OLLAMA_MODEL=civil-law-expert"""
    
    with open('.env', 'w') as f:
        f.write(config)
    print("✅ Switched to EXTERNAL GPU with full civil law model")

def show_current():
    """Show current configuration"""
    try:
        with open('.env', 'r') as f:
            content = f.read()
            if 'localhost' in content:
                server = "LOCAL (M3 Optimized)"
            else:
                server = "EXTERNAL GPU"
            
            if 'civil-law-lite' in content:
                model = "Lightweight Civil Law Model"
            elif 'civil-law-expert' in content:
                model = "Full Civil Law Model"
            else:
                model = "Standard Model"
            
            print(f"🔧 Current: {server} + {model}")
            print(f"Config:\n{content}")
    except FileNotFoundError:
        print("❌ No .env file found")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 switch_ollama.py local     # Local lightweight model (M3 optimized)")
        print("  python3 switch_ollama.py external  # External full model (GPU server)")
        print("  python3 switch_ollama.py status    # Show current config")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'local':
        switch_to_local()
    elif command == 'external':
        switch_to_external()
    elif command == 'status':
        show_current()
    else:
        print("❌ Invalid command. Use: local, external, or status")
