#!/usr/bin/env python3
"""
Setup script for the integrated RAG chatbot system
"""
import os
import sys
import subprocess
import shutil

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def setup_system():
    """Setup the integrated RAG chatbot system"""
    print("🚀 Setting up Integrated RAG Chatbot System")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("backend") or not os.path.exists("frontend"):
        print("❌ Please run this script from the SanHark_25_02 directory")
        return False
    
    # 1. Copy RAG system files to backend
    print("\n📁 Copying RAG system files...")
    rag_files = [
        "/Users/sang/data_processor.py",
        "/Users/sang/ollama_client.py",
        "/Users/sang/requirements.txt"
    ]
    
    for file_path in rag_files:
        if os.path.exists(file_path):
            shutil.copy2(file_path, "backend/")
            print(f"✅ Copied {os.path.basename(file_path)}")
        else:
            print(f"⚠️  {file_path} not found, skipping...")
    
    # 2. Install backend dependencies
    os.chdir("backend")
    if not run_command("pip install -r requirements.txt", "Installing backend dependencies"):
        return False
    
    # 3. Run Django migrations
    if not run_command("python manage.py makemigrations", "Creating Django migrations"):
        return False
    
    if not run_command("python manage.py migrate", "Running Django migrations"):
        return False
    
    # 4. Initialize RAG system with sample data
    print("\n🧠 Initializing RAG system...")
    init_script = """
import sys
sys.path.append('.')
from rag_integration import rag_chatbot
import json

# Create sample data
sample_data = {
    "products": [
        {"id": 1, "name": "Laptop", "price": 999, "category": "Electronics"},
        {"id": 2, "name": "Book", "price": 29, "category": "Education"},
        {"id": 3, "name": "Coffee Maker", "price": 149, "category": "Appliances"}
    ],
    "company": "Sample Corp",
    "description": "A sample dataset for testing the RAG chatbot system"
}

with open("sample_data.json", "w") as f:
    json.dump(sample_data, f, indent=2)

print("Sample data created successfully")
"""
    
    with open("init_rag.py", "w") as f:
        f.write(init_script)
    
    run_command("python init_rag.py", "Creating sample data")
    
    # 5. Setup frontend
    os.chdir("../frontend")
    if not run_command("npm install", "Installing frontend dependencies"):
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Start Ollama: ollama serve")
    print("2. Pull a model: ollama pull llama3.2")
    print("3. Start Django backend: cd backend && python manage.py runserver")
    print("4. Start React frontend: cd frontend && npm start")
    print("5. Visit http://localhost:3000 to use the chatbot")
    
    return True

if __name__ == "__main__":
    setup_system()
