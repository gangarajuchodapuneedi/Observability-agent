import requests
import json

BASE_URL = "http://localhost:8000"

def ask(q: str):
    r = requests.post(f"{BASE_URL}/ask", json={"question": q}, timeout=60)
    print("Q:", q)
    print("Status:", r.status_code)
    try:
        data = r.json()
    except Exception as e:
        print("JSON parse error:", e)
        print("Raw:", r.text[:500])
        print("-" * 60)
        return
    print(json.dumps(data, indent=2))
    print("-" * 60)

def main():
    ask("What is logging?")
    ask("Show me the last 5 architecture drifts")
    ask("Show me the architecture drift timeline")

if __name__ == "__main__":
    main()
