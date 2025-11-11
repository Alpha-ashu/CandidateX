#!/usr/bin/env python3
"""
Test script for the mock interview application APIs.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_create_interview():
    """Test interview creation."""
    print("\n🎯 Testing interview creation...")

    # Try with minimal data first
    interview_data = {
        "job_title": "Test Engineer",
        "experience_level": "mid",
        "question_count": 5,
        "time_limit_per_question": 300,
        "mode": "mixed",
        "type": "mock"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/interviews/",
            json=interview_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            interview_id = data.get("id")
            print(f"✅ Interview created successfully! ID: {interview_id}")
            print(f"   Questions: {data.get('question_count', 'N/A')}")
            print(f"   Mode: {data.get('mode', 'N/A')}")
            return interview_id
        else:
            print(f"❌ Interview creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Interview creation error: {e}")
        return None

def test_get_interview(interview_id):
    """Test getting interview details."""
    print(f"\n📖 Testing interview retrieval (ID: {interview_id})...")

    try:
        response = requests.get(f"{BASE_URL}/api/v1/interviews/{interview_id}")

        if response.status_code == 200:
            data = response.json()
            questions = data.get("questions", [])
            print(f"✅ Interview retrieved successfully!")
            print(f"   Job Title: {data.get('job_title', 'N/A')}")
            print(f"   Questions Generated: {len(questions)}")
            if questions:
                print(f"   Sample Question: {questions[0].get('question_text', 'N/A')[:50]}...")
            return True
        else:
            print(f"❌ Interview retrieval failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Interview retrieval error: {e}")
        return False

def test_ai_models():
    """Test AI models endpoint."""
    print("\n🤖 Testing AI models endpoint...")

    try:
        response = requests.get(f"{BASE_URL}/api/v1/ai/models")

        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            print(f"✅ AI models retrieved successfully!")
            print(f"   Available models: {len(models)}")
            for model in models[:3]:  # Show first 3
                print(f"   - {model.get('name', 'Unknown')}: {model.get('available', False)}")
            return True
        else:
            print(f"⚠️ AI models retrieval failed: {response.status_code} (continuing with other tests)")
            return False
    except Exception as e:
        print(f"⚠️ AI models retrieval error: {e} (continuing with other tests)")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Mock Interview Application Tests")
    print("=" * 50)

    # Test 1: Health Check
    if not test_health():
        print("\n❌ Backend is not healthy. Stopping tests.")
        return

    # Test 2: AI Models
    test_ai_models()

    # Test 3: Interview Creation
    interview_id = test_create_interview()
    if not interview_id:
        print("\n❌ Interview creation failed. Stopping tests.")
        return

    # Wait a moment for AI question generation
    print("\n⏳ Waiting for AI to generate questions...")
    time.sleep(3)

    # Test 4: Interview Retrieval
    test_get_interview(interview_id)

    print("\n" + "=" * 50)
    print("✅ All API tests completed!")
    print("\n📋 Manual Testing Instructions:")
    print("1. Open browser to http://localhost:3004")
    print("2. Navigate to Mock Interview Setup")
    print("3. Fill form with 10 questions")
    print("4. Start interview - should generate 10 questions")
    print("5. Check Settings page in navigation")
    print("6. Test AI Assistant functionality")

if __name__ == "__main__":
    main()
