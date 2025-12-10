"""Test the full API server with Ollama integration."""

import requests
import json
import sys

def test_api():
    print("=" * 60)
    print("Testing Observability Agent API")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"   ✓ Server is running")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ✗ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ✗ Cannot connect to server at {base_url}")
        print(f"   Make sure the server is running: .\\start_server.bat")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 2: Ask a question
    print("\n2. Testing /ask endpoint with Ollama...")
    try:
        question = "How do I troubleshoot slow database queries?"
        body = {"question": question}
        
        print(f"   Question: {question}")
        print(f"   Sending request...")
        
        response = requests.post(
            f"{base_url}/ask",
            json=body,
            timeout=200  # Allow time for LLM generation (server uses 180s)
        )
        
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "")
            score = result.get("score")
            source = result.get("source")
            
            print(f"   ✓ Request successful!")
            print(f"   Score: {score}")
            print(f"   Source: {source}")
            print(f"   Answer (first 300 chars): {answer[:300]}...")
            
            if source == "ollama":
                print(f"\n   ✓✓✓ SUCCESS! LLM integration is working!")
                return True
            elif source == "fallback":
                print(f"\n   ⚠ Got fallback response - Ollama might not be accessible")
                print(f"   Check server logs for error details")
                return False
            else:
                print(f"\n   ? Unknown source: {source}")
                return False
        else:
            print(f"   ✗ Error status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ✗ Request timed out after 200 seconds")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ✗ Connection error: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api()
    print("\n" + "=" * 60)
    if success:
        print("✓ All API tests passed! LLM integration is working!")
        sys.exit(0)
    else:
        print("✗ Tests failed. Check the errors above and server logs.")
        sys.exit(1)
