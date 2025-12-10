"""Test script to verify Ollama connection."""

import requests
import json
import os
import sys

def test_ollama_connection():
    """Test if Ollama is accessible and can generate responses."""
    print("=" * 60)
    print("Testing Ollama Connection")
    print("=" * 60)
    
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "tinyllama")
    
    # Test 1: Check if Ollama API is accessible
    print(f"\n1. Testing Ollama API at {ollama_host}...")
    try:
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"   ✓ Ollama is running")
            print(f"   ✓ Available models: {[m.get('name') for m in models]}")
        else:
            print(f"   ✗ Ollama returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ✗ Cannot connect to Ollama at {ollama_host}")
        print(f"   Make sure Ollama is running: ollama serve")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 2: Try to generate a response
    print(f"\n2. Testing model generation with '{ollama_model}'...")
    try:
        url = f"{ollama_host}/api/generate"
        payload = {
            "model": ollama_model,
            "prompt": "Say hello in one word",
            "stream": False
        }
        print(f"   Calling: {url}")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=30)
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "response" in data:
                answer = data["response"]
                print(f"   ✓ Success! Response: {answer[:100]}")
                return True
            else:
                print(f"   ✗ Response missing 'response' field")
                print(f"   Full response: {json.dumps(data, indent=2)}")
                return False
        else:
            print(f"   ✗ Error status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ✗ Request timed out after 30 seconds")
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
    success = test_ollama_connection()
    print("\n" + "=" * 60)
    if success:
        print("✓ All tests passed! Ollama is working correctly.")
        sys.exit(0)
    else:
        print("✗ Tests failed. Check the errors above.")
        sys.exit(1)
