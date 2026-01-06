import requests
import sys

def test_ping():
    print("Testing server connectivity...")
    try:
        resp = requests.get('http://127.0.0.1:5003/ping', timeout=5)
        print(f"Ping Status: {resp.status_code}")
        print(f"Ping Response: {resp.text}")
    except Exception as e:
        print(f"Ping failed: {e}")

def test_process():
    print("\nTesting process endpoint (simulated)...")
    try:
        # Use a dummy URL that won't trigger heavy processing if validation fails, 
        # or use a real one if validation is strict.
        # Based on regex, it needs http/https.
        data = {'url': 'https://www.example.com/test_video'}
        print("Sending POST /process...")
        resp = requests.post('http://127.0.0.1:5003/process', data=data, timeout=60) # 60s timeout
        print(f"Process Status: {resp.status_code}")
        # Truncate response if too long
        print(f"Process Response: {resp.text[:200]}...")
    except Exception as e:
        print(f"Process request failed: {e}")

if __name__ == "__main__":
    test_ping()
    test_process()
