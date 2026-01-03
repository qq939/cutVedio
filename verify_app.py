import requests
import time
import os
import glob

def verify_extraction():
    url = "https://v.douyin.com/zOWN6NkyUJo/"
    server_url = "http://127.0.0.1:5003/process"
    
    print(f"Sending request to {server_url} with URL: {url}")
    
    # Wait for server to be ready
    for i in range(10):
        try:
            requests.get("http://127.0.0.1:5003/")
            print("Server is ready.")
            break
        except requests.exceptions.ConnectionError:
            print(f"Waiting for server... ({i+1}/10)")
            time.sleep(2)
    
    try:
        start_time = time.time()
        response = requests.post(server_url, data={'url': url})
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        print(f"Time taken: {time.time() - start_time:.2f}s")
        
        # Check /tmp/vedio
        files = glob.glob('/tmp/vedio/*.jpg')
        print(f"Found {len(files)} images in /tmp/vedio")
        if len(files) > 0:
            print("First 5 files:", files[:5])
            print("VERIFICATION SUCCESS: Frames extracted.")
        else:
            print("VERIFICATION FAILED: No frames found.")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    verify_extraction()
