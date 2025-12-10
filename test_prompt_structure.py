"""Test the exact prompt structure we're using."""

import requests
import time
from src.llm_client import build_observability_prompt, call_ollama_generate

def test():
    print("Testing prompt structure...")
    
    # Build the exact prompt we use
    question = "What metrics should I track?"
    context = "- Web result 1 for: What metrics should I track?\n- Web result 2 for: What metrics should I track?\n- Memory result 1 for: What metrics should I track?"
    
    prompt = build_observability_prompt(question, context)
    print(f"\nPrompt length: {len(prompt)} characters")
    print(f"\nFirst 500 chars of prompt:")
    print(prompt[:500])
    print("\n...")
    print(f"\nLast 200 chars of prompt:")
    print(prompt[-200:])
    
    # Test with Ollama directly
    print("\n\nTesting with Ollama...")
    print("=" * 60)
    
    start = time.time()
    try:
        answer, latency = call_ollama_generate(prompt)
        print(f"\n✓ SUCCESS! Response received in {latency:.2f} seconds")
        print(f"\nAnswer (first 500 chars):")
        print(answer[:500])
        return True
    except Exception as e:
        elapsed = time.time() - start
        print(f"\n✗ FAILED after {elapsed:.2f} seconds")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    test()
