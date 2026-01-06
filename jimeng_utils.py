import json
import time
import os
import logging
from volcenginesdkcore.rest import ApiException
from volcenginesdkvisual.api import VisualService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
VOLC_ACCESS_KEY = os.getenv("VOLC_ACCESSKEY")
VOLC_SECRET_KEY = os.getenv("VOLC_SECRETKEY")

# Define the service
visual_service = VisualService()
visual_service.set_ak(VOLC_ACCESS_KEY)
visual_service.set_sk(VOLC_SECRET_KEY)

def create_jimeng_task(image_url, video_url):
    """
    Submits an Action Mimicry task to Volcengine Jimeng API.
    """
    if not VOLC_ACCESS_KEY or not VOLC_SECRET_KEY:
        logger.error("VOLC_ACCESSKEY or VOLC_SECRETKEY not found.")
        return None

    # Action: MotionMimic
    action_name = "MotionMimic" 
    
    # Construct the request body
    # Based on documentation input: image + video
    req_body = {
        "req_key": "motion_mimic",
        "binary_data_base64": [],
        "image_urls": [image_url],
        "video_urls": [video_url],
    }
    
    try:
        logger.info(f"Submitting Jimeng task (Action={action_name})...")
        
        # Prepare params
        params = dict()
        
        # Call the API
        resp = visual_service.common_json_handler(action_name, params, req_body)
        
        logger.info(f"Jimeng response: {resp}")
        
        # Check response structure
        if resp and "data" in resp and "task_id" in resp["data"]:
            return resp["data"]["task_id"]
        elif resp and "code" in resp and resp["code"] != 10000:
             logger.error(f"Jimeng API error: {resp}")
             return None
        
        return None

    except ApiException as e:
        logger.error(f"Volcengine API Exception: {e}")
        return None
    except Exception as e:
        logger.error(f"Jimeng task submission error: {e}")
        return None

def check_task_status(task_id):
    """
    Checks the status of a Jimeng task.
    """
    if not VOLC_ACCESS_KEY or not VOLC_SECRET_KEY:
        return 'FAILED', 'Missing API Key'

    req_body = {
        "task_id": task_id
    }
    
    try:
        resp = visual_service.common_json_handler("GetVisualTask", dict(), req_body)
        
        if resp and "data" in resp:
            data = resp["data"]
            status = data.get("status") # e.g. "ProcessSuccess", "Processing", "ProcessFail"
            
            if status == "ProcessSuccess":
                # Result usually in 'resp_data' which might be a JSON string or dict
                res_data = data.get("resp_data")
                if isinstance(res_data, str):
                    try:
                        res_data = json.loads(res_data)
                    except:
                        pass
                
                # Extract video URL
                # Structure depends on the specific algorithm
                video_url = None
                if isinstance(res_data, dict) and "video_url" in res_data:
                    video_url = res_data["video_url"]
                
                return 'SUCCEEDED', video_url
            elif status == "ProcessFail":
                return 'FAILED', data.get("fail_reason", "Unknown failure")
            else:
                return 'RUNNING', None
        else:
            return 'UNKNOWN', str(resp)
            
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        return 'UNKNOWN', str(e)
