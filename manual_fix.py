import comfy_utils
import obs_utils
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TASK_ID = "7136715d-cdbd-40e5-b598-696dec7e11d8"
ULTRA_VIDEO_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp', 'ultraVideo')

if not os.path.exists(ULTRA_VIDEO_FOLDER):
    os.makedirs(ULTRA_VIDEO_FOLDER)

print(f"Checking status for task {TASK_ID}...")
status, result = comfy_utils.check_status(TASK_ID)
print(f"Status: {status}")
print(f"Result: {result}")

if status == 'SUCCEEDED' and isinstance(result, dict):
    print("Downloading result...")
    local_path = comfy_utils.download_result(result, ULTRA_VIDEO_FOLDER)
    print(f"Downloaded to: {local_path}")
    
    if local_path:
        # Upload to OBS
        now = datetime.now()
        obs_filename = now.strftime("【%Y_%m_%d_%H_%M_%S】new.mp4")
        print(f"Uploading to OBS as {obs_filename}...")
        
        url = obs_utils.upload_file(local_path, obs_filename, mime_type='video/mp4')
        print(f"Upload Result URL: {url}")
    else:
        print("Download failed.")
else:
    print("Task not succeeded or invalid result.")
