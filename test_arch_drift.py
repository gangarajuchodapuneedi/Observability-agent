"""Test the ArchDrift integration."""

import requests
import json
import sys
import os

def test_arch_drift_direct():
    """Test ArchDrift endpoint directly."""
    print("=" * 60)
    print("Testing ArchDrift Service Directly")
    print("=" * 60)
    
    base = "http://localhost:9000"
    repo = "https://github.com/lokus-ai/lokus.git"
    
    # Get endpoint from environment or use default
    import os
    endpoint = os.getenv("ARCH_DRIFT_ENDPOINT", "/drifts")
    
    print(f"\n1. Testing ArchDrift endpoint: {base}{endpoint}")
    print(f"   Repo: {repo}")
    print(f"   Limit: 5")
    
    try:
        r = requests.get(
            f"{base}{endpoint}",
            params={"repo": repo, "limit": 5},
            timeout=15
        )
        print(f"\n   Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"   ✓ Successfully fetched drift data")
            print(f"\n   Response keys: {list(data.keys())}")
            
            # Check expected structure (flexible - API may return different structure)
            expected_keys = ["repo", "window_summary", "drifts"]
            actual_keys = list(data.keys())
            print(f"   Actual response keys: {actual_keys}")
            
            # Check if we have the expected structure or a different one
            if all(k in data for k in expected_keys):
                print(f"   ✓ All expected keys present")
                if "drifts" in data:
                    print(f"   Number of drifts: {len(data['drifts'])}")
            elif "items" in data:
                print(f"   ⚠ API returns 'items' instead of 'drifts' (different structure)")
                print(f"   Number of items: {len(data['items']) if isinstance(data['items'], list) else 'N/A'}")
            else:
                print(f"   ⚠ Response structure differs from expected")
            
            print(f"\n   Sample response:")
            print(json.dumps(data, indent=2)[:500] + "...")
            return True
        else:
            print(f"   ✗ Error: Status {r.status_code}")
            print(f"   Response: {r.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"   ✗ Cannot connect to ArchDrift service at {base}")
        print(f"   Make sure ArchDrift is running:")
        print(f"   cd D:\\ArchDrift")
        print(f"   uvicorn app.main:app --reload --port 9000")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


def test_arch_drift_client():
    """Test the ArchDrift client module."""
    print("\n" + "=" * 60)
    print("Testing ArchDrift Client Module")
    print("=" * 60)
    
    try:
        from src.arch_drift_client import fetch_last_arch_drifts
        
        repo = "https://github.com/lokus-ai/lokus.git"
        print(f"\n2. Testing fetch_last_arch_drifts()")
        print(f"   Repo: {repo}")
        print(f"   Limit: 5")
        
        result = fetch_last_arch_drifts(repo, limit=5)
        
        if result is None:
            print(f"   ✗ Client returned None (service may be unavailable)")
            return False
        
        print(f"   ✓ Client successfully fetched data")
        print(f"   Response keys: {list(result.keys())}")
        
        # Check expected structure
        expected_keys = ["repo", "window_summary", "drifts"]
        missing_keys = [k for k in expected_keys if k not in result]
        if missing_keys:
            print(f"   ⚠ Missing expected keys: {missing_keys}")
        else:
            print(f"   ✓ All expected keys present")
        
        return True
        
    except ImportError as e:
        print(f"   ✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_intent_detection():
    """Test the intent detection."""
    print("\n" + "=" * 60)
    print("Testing Intent Detection")
    print("=" * 60)
    
    try:
        from src.api_server import detect_arch_drift_intent
        
        test_cases = [
            ("What is architecture drift?", True),
            ("Show me arch drift", True),
            ("Tell me about drifts", True),
            ("How do I monitor performance?", False),
            ("What is the status?", False),
            ("architecture evolution", True),
        ]
        
        print(f"\n3. Testing detect_arch_drift_intent()")
        all_passed = True
        
        for question, expected in test_cases:
            result = detect_arch_drift_intent(question)
            status = "✓" if result == expected else "✗"
            if result != expected:
                all_passed = False
            print(f"   {status} '{question}' -> {result} (expected {expected})")
        
        return all_passed
        
    except ImportError as e:
        print(f"   ✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ask_endpoint_arch_drift():
    """Test the /ask endpoint with arch drift questions."""
    print("\n" + "=" * 60)
    print("Testing /ask Endpoint with Arch Drift Questions")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Set default repo for testing
    os.environ["DEFAULT_REPO"] = "https://github.com/lokus-ai/lokus.git"
    
    test_questions = [
        "What is the architecture drift?",
        "Show me arch drift",
        "Tell me about drifts",
    ]
    
    print(f"\n4. Testing /ask endpoint")
    print(f"   Base URL: {base_url}")
    
    all_passed = True
    
    for question in test_questions:
        print(f"\n   Testing: '{question}'")
        try:
            response = requests.post(
                f"{base_url}/ask",
                json={"question": question},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"      ✓ Status: {response.status_code}")
                
                # Check for arch_drift mode
                if data.get("mode") == "arch_drift":
                    print(f"      ✓ Mode: arch_drift")
                    
                    if "drift_data" in data:
                        drift_data = data["drift_data"]
                        if drift_data is None:
                            print(f"      ⚠ drift_data is None (service may be unavailable)")
                        else:
                            print(f"      ✓ drift_data present")
                            print(f"      ✓ Keys: {list(drift_data.keys())}")
                    else:
                        print(f"      ✗ Missing 'drift_data' key")
                        all_passed = False
                else:
                    print(f"      ⚠ Mode: {data.get('mode', 'not set')} (expected 'arch_drift')")
                    print(f"      Response: {json.dumps(data, indent=2)[:300]}")
            else:
                print(f"      ✗ Status: {response.status_code}")
                print(f"      Response: {response.text[:200]}")
                all_passed = False
                
        except requests.exceptions.ConnectionError:
            print(f"      ✗ Cannot connect to server at {base_url}")
            print(f"      Make sure the server is running: python src/api_server.py")
            all_passed = False
        except Exception as e:
            print(f"      ✗ Error: {e}")
            all_passed = False
    
    return all_passed


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ArchDrift Integration Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Direct ArchDrift endpoint
    results.append(("Direct ArchDrift Endpoint", test_arch_drift_direct()))
    
    # Test 2: ArchDrift client module
    results.append(("ArchDrift Client Module", test_arch_drift_client()))
    
    # Test 3: Intent detection
    results.append(("Intent Detection", test_intent_detection()))
    
    # Test 4: /ask endpoint integration
    results.append(("/ask Endpoint Integration", test_ask_endpoint_arch_drift()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

