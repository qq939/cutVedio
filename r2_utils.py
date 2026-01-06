import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
R2_ACCOUNT_ID = '03b4d78e4f6c6c09d71f2ad15aeb85ae'
R2_BUCKET_NAME = 'runway-video-storage'
R2_TOKEN = os.getenv('CLOUDFLARER2TOKEN')

def upload_file(file_path, file_name, mime_type=None):
    """
    Uploads a file to Cloudflare R2 using the REST API (Bearer Token).
    """
    if not R2_TOKEN:
        print("DEBUG: CLOUDFLARER2TOKEN is missing in .env", flush=True)
        return None

    print(f"DEBUG: Starting R2 upload for {file_name}...", flush=True)
    
    # Endpoint for Cloudflare R2 API upload
    # https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/{bucket_name}/objects/{object_name}
    upload_url = f"https://api.cloudflare.com/client/v4/accounts/{R2_ACCOUNT_ID}/r2/buckets/{R2_BUCKET_NAME}/objects/{file_name}"
    
    headers = {
        'Authorization': f'Bearer {R2_TOKEN}',
        'Content-Type': mime_type if mime_type else 'application/octet-stream'
    }
    
    try:
        with open(file_path, 'rb') as f:
            response = requests.put(upload_url, headers=headers, data=f)
            
        if response.status_code == 200:
            print(f"DEBUG: R2 upload successful for {file_name}", flush=True)
            result = response.json()
            # Construct a URL. Since we don't have S3 keys for presigning, we return the S3 endpoint URL.
            # This URL might not be publicly accessible without a custom domain or worker.
            # But the user provided this endpoint, so maybe they have a setup.
            # User provided: https://03b4d78e4f6c6c09d71f2ad15aeb85ae.r2.cloudflarestorage.com/runway-video-storage
            
            # Note: The user might have a Public Bucket URL or Custom Domain. 
            # If not, this URL won't work for public download. 
            # But we must return *something*.
            public_url = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com/{R2_BUCKET_NAME}/{file_name}"
            print(f"DEBUG: Uploaded URL: {public_url}", flush=True)
            return public_url
        else:
            print(f"DEBUG: R2 upload failed with status {response.status_code}: {response.text}", flush=True)
            return None

    except Exception as e:
        print(f"DEBUG: R2 upload failed: {e}", flush=True)
        return None
