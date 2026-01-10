import jimeng_utils
import logging
import json
from volcengine.ApiInfo import ApiInfo

# Setup logging
logging.basicConfig(level=logging.INFO)

print("Testing jimeng_utils reproduction...")

# Mock keys
jimeng_utils.VOLC_ACCESS_KEY = "mock_ak"
jimeng_utils.VOLC_SECRET_KEY = "mock_sk"
jimeng_utils.visual_service.set_ak("mock_ak")
jimeng_utils.visual_service.set_sk("mock_sk")

versions_to_try = ["2025-08-20", "2025-11-21", "2025-01-01", "2024-01-01"]

for version in versions_to_try:
    print(f"Testing version: {version}")
    jimeng_utils.visual_service.api_info["MotionMimic"] = ApiInfo("POST", "/", {"Action": "MotionMimic", "Version": version}, {}, {})
    
    try:
        task_id = jimeng_utils.create_jimeng_task("http://example.com/image.png", "http://example.com/video.mp4")
        print(f"Version {version} Task ID: {task_id}")
    except Exception as e:
        print(f"Version {version} Error: {e}")
