import subprocess
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OBS_BASE_URL = "http://obs.dimond.top"

def upload_file(file_path, file_name, mime_type=None):
    """
    Upload file to OBS URL using curl --upload-file.
    """
    target_url = f"{OBS_BASE_URL}/{file_name}"
    try:
        print(f"DEBUG: Uploading {file_path} to {target_url}...", flush=True)
        logger.info(f"Starting upload: {file_path} -> {target_url}")
        
        if not os.path.exists(file_path):
            msg = f"File not found: {file_path}"
            print(f"DEBUG: {msg}", flush=True)
            logger.error(msg)
            return None

        # Use curl --upload-file as requested
        # Added -k for insecure/skip verify if needed
        command = ['curl', '-k', '--upload-file', file_path, target_url]
        print(f"DEBUG: Command: {' '.join(command)}", flush=True)
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"DEBUG: Upload successful: {target_url}", flush=True)
            logger.info(f"Upload successful: {target_url}")
            # print(f"DEBUG: Curl output: {result.stdout}", flush=True)
            return target_url
        else:
            print(f"DEBUG: Upload failed with exit code {result.returncode}", flush=True)
            print(f"DEBUG: Curl stderr: {result.stderr}", flush=True)
            print(f"DEBUG: Curl stdout: {result.stdout}", flush=True)
            logger.error(f"Upload failed. Code: {result.returncode}, Stderr: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"DEBUG: Upload error: {e}", flush=True)
        logger.error(f"Upload exception: {e}")
        return None
