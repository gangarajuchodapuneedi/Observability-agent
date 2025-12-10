"""Test the LLM client directly."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.llm_client import call_ollama_generate, build_observability_prompt, LLMError

def test():
    print("Testing LLM Client...")
    print("=" * 60)
    
    # Test prompt building
    print("\n1. Testing prompt building...")
    prompt = build_observability_prompt("How do I troubleshoot slow queries?")
    print(f"   Prompt length: {len(prompt)} characters")
    print(f"   First 200 chars: {prompt[:200]}...")
    
    # Test Ollama call
    print("\n2. Testing Ollama API call...")
    try:
        answer, latency = call_ollama_generate("Say hello in one word")
        print(f"   ✓ Success!")
        print(f"   Latency: {latency:.2f} seconds")
        print(f"   Answer: {answer[:200]}")
        return True
    except LLMError as e:
        print(f"   ✗ LLM Error: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test()
    if success:
        print("\n✓ LLM Client test passed!")
    else:
        print("\n✗ LLM Client test failed!")
    sys.exit(0 if success else 1)
