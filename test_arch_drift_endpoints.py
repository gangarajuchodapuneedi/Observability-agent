"""Diagnostic script to find the correct ArchDrift endpoint."""

import requests
import json

def discover_endpoints():
    """Try different endpoint paths to find the correct one."""
    base = "http://localhost:9000"
    repo = "https://github.com/lokus-ai/lokus.git"
    
    # Common FastAPI endpoint patterns
    endpoints_to_try = [
        "/api/drifts",
        "/drifts",
        "/api/v1/drifts",
        "/drift",
        "/api/drift",
    ]
    
    print("=" * 60)
    print("ArchDrift Endpoint Discovery")
    print("=" * 60)
    print(f"Base URL: {base}")
    print(f"Repo: {repo}")
    print(f"\nTrying different endpoint paths...\n")
    
    for endpoint in endpoints_to_try:
        url = f"{base}{endpoint}"
        print(f"Testing: {url}")
        try:
            resp = requests.get(
                url,
                params={"repo": repo, "limit": 5},
                timeout=5
            )
            print(f"  Status: {resp.status_code}")
            
            if resp.status_code == 200:
                print(f"  ✓ SUCCESS! Found working endpoint: {endpoint}")
                data = resp.json()
                print(f"  Response keys: {list(data.keys())}")
                return endpoint
            elif resp.status_code == 404:
                print(f"  ✗ Not Found")
            else:
                print(f"  ⚠ Status {resp.status_code}: {resp.text[:100]}")
        except requests.exceptions.ConnectionError:
            print(f"  ✗ Cannot connect (service may not be running)")
            return None
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\n✗ None of the tested endpoints worked.")
    print(f"\nTry checking:")
    print(f"  1. ArchDrift service docs for the correct endpoint")
    print(f"  2. FastAPI auto-generated docs at: {base}/docs")
    print(f"  3. OpenAPI schema at: {base}/openapi.json")
    return None


def check_fastapi_docs():
    """Check FastAPI auto-generated documentation."""
    base = "http://localhost:9000"
    
    print("\n" + "=" * 60)
    print("Checking FastAPI Documentation")
    print("=" * 60)
    
    endpoints = [
        "/docs",
        "/openapi.json",
        "/redoc",
    ]
    
    for endpoint in endpoints:
        url = f"{base}{endpoint}"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                print(f"✓ {endpoint} is accessible")
                if endpoint == "/openapi.json":
                    try:
                        schema = resp.json()
                        paths = schema.get("paths", {})
                        print(f"\nAvailable endpoints:")
                        for path in paths.keys():
                            print(f"  {path}")
                    except:
                        pass
            else:
                print(f"✗ {endpoint} returned {resp.status_code}")
        except Exception as e:
            print(f"✗ {endpoint} error: {e}")


if __name__ == "__main__":
    endpoint = discover_endpoints()
    check_fastapi_docs()
    
    if endpoint:
        print(f"\n" + "=" * 60)
        print(f"Found working endpoint: {endpoint}")
        print(f"\nTo use this endpoint, set the environment variable:")
        print(f'  set ARCH_DRIFT_ENDPOINT={endpoint}')
        print(f"\nOr update src/arch_drift_client.py line 9:")
        print(f'  ARCH_DRIFT_ENDPOINT = os.getenv("ARCH_DRIFT_ENDPOINT", "{endpoint}")')
        print("=" * 60)

