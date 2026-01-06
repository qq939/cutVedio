import time
import requests
import json
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALIYUN_API_KEY = os.getenv("ALIYUN_API_KEY")
DASH_SCOPE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis"

def create_task(character_url, video_url):
    """
    Submits a video generation task to Aliyun Bailian.
    Returns task_id if successful, None otherwise.
    """
    if not ALIYUN_API_KEY:
        logger.error("ALIYUN_API_KEY not found in environment variables.")
        return None

    headers = {
        "Authorization": f"Bearer {ALIYUN_API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable"
    }
    
    # Using the specific structure requested by user
    payload = {
        "model": "wan2.2-animate-mix", 
        "parameters": {
            "mode": "wan-std",
            "image_url": character_url,
            "video_url": video_url,
            "resolution": "1080p",
            "duration": 10
        }
    }
    
    try:
        logger.info(f"Submitting Aliyun task with char={character_url}, video={video_url}")
        response = requests.post(DASH_SCOPE_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            if 'output' in result and 'task_id' in result['output']:
                task_id = result['output']['task_id']
                logger.info(f"Aliyun task created: {task_id}")
                return task_id
            else:
                logger.error(f"Unexpected response structure: {result}")
                return None
        else:
            logger.error(f"Task creation failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Aliyun task submission error: {e}")
        return None

def check_task_status(task_id):
    """
    Checks the status of an Aliyun task.
    Returns (status, video_url/error_message).
    Status: 'PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED', 'UNKNOWN'
    """
    if not ALIYUN_API_KEY:
        return 'FAILED', 'Missing API Key'

    url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
    headers = {
        "Authorization": f"Bearer {ALIYUN_API_KEY}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            output = result.get('output', {})
            status = output.get('task_status', 'UNKNOWN')
            
            if status == 'SUCCEEDED':
                video_url = output.get('video_url')
                return 'SUCCEEDED', video_url
            elif status == 'FAILED':
                message = output.get('message', 'Unknown error')
                return 'FAILED', message
            else:
                return status, None
        else:
            logger.error(f"Check status failed: {response.status_code}")
            return 'UNKNOWN', f"HTTP {response.status_code}"
            
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        return 'UNKNOWN', str(e)
