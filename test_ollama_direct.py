"""Test Ollama API directly with a simple prompt."""

import requests
import json
import time

def test_simple():
    print("Testing Ollama API directly...")
    
    # Test 1: Very simple prompt
    print("\n1. Testing with simple prompt...")
    payload = {
        "model": "llama2:7b",
        "prompt": "Say hello in one word",
        "stream": False,
        "options": {
            "num_predict": 10
        }
    }
    
    start = time.time()
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=30
        )
        elapsed = time.time() - start
        print(f"   Status: {response.status_code}, Time: {elapsed:.2f}s")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data.get('response', 'No response')[:100]}")
            return True
    except Exception as e:
        print(f"   Error: {e}")
        return False
    
    # Test 2: With our structured prompt format
    print("\n2. Testing with structured prompt format...")
    structured_prompt = """You are an observability assistant.

User question: What metrics should I track?

Answer in this format:
**Question**
[question]

**1. Short Answer (1–3 lines)**
[answer]

**2. When / Why You Use This**
- [case 1]
- [case 2]
- [case 3]

**3. How To Do It (Practical Steps)**
1. [step 1]
2. [step 2]
3. [step 3]

**4. Quick Checklist (Ready-To-Use)**
- [ ] [check 1]
- [ ] [check 2]
- [ ] [check 3]

**5. Optional Extras (Only if needed)**
- Common pitfalls:
  - [pitfall 1]
  - [pitfall 2]
- Good next steps:
  - [step 1]
  - [step 2]

Start with **Question** followed by the question. No repetition.

Answer:"""
    
    payload2 = {
        "model": "llama2:7b",
        "prompt": structured_prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 1.0,
            "num_predict": 350,
            "repeat_penalty": 1.3
        }
    }
    
    start = time.time()
    try:
        print(f"   Prompt length: {len(structured_prompt)} characters")
        print(f"   Sending request...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload2,
            timeout=180
        )
        elapsed = time.time() - start
        print(f"   Status: {response.status_code}, Time: {elapsed:.2f}s")
        if response.status_code == 200:
            data = response.json()
            answer = data.get('response', 'No response')
            print(f"   Response length: {len(answer)} characters")
            print(f"   First 200 chars: {answer[:200]}")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print(f"   Timed out after 180 seconds")
        return False
    except Exception as e:
        print(f"   Error: {e}")
        return False

if __name__ == "__main__":
    test_simple()
