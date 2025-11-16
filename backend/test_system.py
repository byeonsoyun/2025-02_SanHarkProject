#!/usr/bin/env python3
import requests
import json
import time

def test_chat_api(question, session_id="test-session"):
    """Test the chat API"""
    try:
        response = requests.post(
            "http://localhost:8000/chat/api/chat/",
            json={
                "message": question,
                "user_session_id": session_id
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json().get("reply", "No reply")
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Connection error: {e}"

def run_tests():
    """Run comprehensive system tests"""
    print("🧪 Testing Updated Civil Law Chatbot System\n")
    
    # Test 1: Custom Model Response
    print("1️⃣ Testing Custom Civil Law Model...")
    response1 = test_chat_api("계약 위반 시 손해배상 범위는 어떻게 결정되나요?")
    print(f"Response: {response1[:200]}...")
    print("✅ Should show legal expert terminology\n")
    
    # Test 2: Context Maintenance
    print("2️⃣ Testing Context Maintenance...")
    session_id = "context-test"
    
    response2a = test_chat_api("교통사고 손해배상은 어떻게 계산하나요?", session_id)
    print(f"First: {response2a[:100]}...")
    
    time.sleep(1)  # Brief pause
    
    response2b = test_chat_api("그럼 과실비율은 어떻게 정해지나요?", session_id)
    print(f"Follow-up: {response2b[:100]}...")
    print("✅ Should reference traffic accident context\n")
    
    # Test 3: Simple vs Complex
    print("3️⃣ Testing Complexity Detection...")
    simple = test_chat_api("임대차 계약")
    complex = test_chat_api("임대차보증금 반환청구권과 우선변제권의 관계에 대해 분석해주세요")
    
    print(f"Simple: {simple[:100]}...")
    print(f"Complex: {complex[:100]}...")
    print("✅ Complex should be longer and more analytical\n")
    
    # Test 4: Civil Law Database
    print("4️⃣ Testing Civil Law Database...")
    response4 = test_chat_api("부동산 매매계약 해제")
    print(f"Response: {response4[:200]}...")
    print("✅ Should find civil law cases (not public servant cases)\n")
    
    print("🎉 System testing complete!")
    print("\nTo test manually:")
    print("1. Start Django: python3 manage.py runserver")
    print("2. Open React frontend")
    print("3. Try the test questions above")

if __name__ == "__main__":
    run_tests()
