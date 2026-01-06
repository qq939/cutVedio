import time
import sys
import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

def run_aliyun_task(character_url="http://obs.dimond.top/character.png", video_url="http://obs.dimond.top/reference.mp4"):
    print(f"Starting Aliyun Image2Video task with:")
    print(f"  Character: {character_url}")
    print(f"  Video: {video_url}")
    
    api_key = os.getenv("ALIYUN_API_KEY")
    if not api_key:
        print("Error: ALIYUN_API_KEY not found in environment variables.")
        return None

    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable" # Enable async processing
    }
    data = {
        "model": "wan2.2-animate-mix", # Updated model name based on user request "wan2.2" might be typo, usually it is wanx or similar. 
        # But user provided specific config: "model": "wan2.2-animate-mix"
        # Let's use exactly what user provided.
        "model": "wan2.2-animate-mix", # Wait, I should check valid models. 
        # User said: "model": "wan2.2-animate-mix". I will use that.
        # Actually, standard DashScope models are like "wanx-v1" etc.
        # User snippet: "model": "wan2.2-animate-mix", "mode": "wan-std"
        # I will trust the user provided snippet first.
    }
    
    # User strictly requested "wan2.2-animate-mix" and specific structure in previous prompt.
    # We will follow that structure.
    final_data = {
        "model": "wan2.2-animate-mix", 
        "input": {"image_url": character_url,
            "video_url": video_url},
        "parameters": {
            "mode": "wan-std",
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=final_data)
        
        if response.status_code == 200:
            result = response.json()
            if 'output' in result and 'task_id' in result['output']:
                task_id = result['output']['task_id']
                print(f"Task created successfully. Task ID: {task_id}")
                return wait_for_task(task_id, headers)
            else:
                print(f"Unexpected response structure: {result}")
                return None
        else:
            print(f"Task creation failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Aliyun task failed: {e}")
        return None

def wait_for_task(task_id, headers):
    print(f"Waiting for task {task_id} to complete...")
    url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
    
    while True:
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                result = response.json()
                status = result.get('output', {}).get('task_status', '')
                
                if status == 'SUCCEEDED':
                    print("Task SUCCEEDED!")
                    video_url = result.get('output', {}).get('video_url', '')
                    print(f"Result Video URL: {video_url}")
                    return video_url
                elif status == 'FAILED':
                    print(f"Task FAILED: {result.get('output', {}).get('message')}")
                    return None
                else:
                    print(f"Task Status: {status}. Waiting 5s...")
                    time.sleep(5)
            else:
                print(f"Check status failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error checking status: {e}")
            return None

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        char_url = sys.argv[1]
        vid_url = sys.argv[2]
        run_aliyun_task(char_url, vid_url)
    else:
        run_aliyun_task()