import os
import boto3
import logging
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
R2_ACCOUNT_ID = '03b4d78e4f6c6c09d71f2ad15aeb85ae'
R2_BUCKET_NAME = 'runway-video-storage'
R2_ENDPOINT_URL = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
R2_TOKEN = os.getenv('CLOUDFLARER2TOKEN')
R2_ACCESS_KEY_ID = os.getenv('CLOUDFLARER2ACCESSKEYID') # We hope this exists or we need to ask

def get_s3_client():
    """Initializes and returns a boto3 S3 client for Cloudflare R2."""
    if not R2_TOKEN:
        logger.error("CLOUDFLARER2TOKEN is missing in .env")
        return None
    
    # Check if we have an Access Key ID. If not, we might be in trouble unless TOKEN is enough (unlikely for boto3)
    # or the user put the Access Key ID in a different variable.
    # For now, let's try to use R2_TOKEN as Secret Access Key and check if R2_ACCESS_KEY_ID is available.
    
    access_key = R2_ACCESS_KEY_ID
    secret_key = R2_TOKEN
    
    if not access_key:
        logger.warning("CLOUDFLARER2ACCESSKEYID is missing in .env. R2 upload might fail if Access Key ID is required.")
        # Some users might put "ID:Secret" in one token?
        if ':' in R2_TOKEN:
            parts = R2_TOKEN.split(':', 1)
            access_key = parts[0]
            secret_key = parts[1]
            logger.info("Parsed Access Key ID and Secret Key from CLOUDFLARER2TOKEN.")
        else:
            # Fallback: maybe the user thinks the token is all that's needed.
            # We can't proceed with boto3 without an ID.
            logger.error("Cannot initialize R2 client: Access Key ID is missing.")
            return None

    try:
        s3 = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        return s3
    except Exception as e:
        logger.error(f"Failed to initialize R2 client: {e}")
        return None

def upload_file(file_path, file_name, mime_type=None):
    """
    Uploads a file to Cloudflare R2 and returns the public URL (if configured) or presigned URL.
    """
    s3 = get_s3_client()
    if not s3:
        return None

    print(f"DEBUG: Starting R2 upload for {file_name}...", flush=True)
    
    try:
        extra_args = {}
        if mime_type:
            extra_args['ContentType'] = mime_type

        # Check if file exists (optional, but good for debug)
        # s3.head_object(Bucket=R2_BUCKET_NAME, Key=file_name) 

        s3.upload_file(
            file_path,
            R2_BUCKET_NAME,
            file_name,
            ExtraArgs=extra_args
        )
        
        print(f"DEBUG: R2 upload successful for {file_name}", flush=True)
        
        # R2 buckets are usually private by default. 
        # If the user has a custom domain or public access, we construct the URL.
        # The user provided endpoint: https://03b4d78e4f6c6c09d71f2ad15aeb85ae.r2.cloudflarestorage.com/runway-video-storage
        # Public access URL might be different. 
        # If the bucket is public, it might be reachable at a custom domain or the R2.dev subdomain.
        # For now, let's try to return a public URL structure if we know it, or a presigned URL.
        
        # Assumption: If the user is using this for RunwayML, it probably needs a publicly accessible URL.
        # Let's generate a presigned URL which is safer and works for private buckets too.
        # However, RunwayML might need a direct link. 
        # The user said: "https://...r2.cloudflarestorage.com/runway-video-storage"
        # Let's check if we can construct a public URL.
        
        # Strategy: Generate a presigned URL valid for 1 hour (or more).
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': R2_BUCKET_NAME, 'Key': file_name},
            ExpiresIn=3600 * 24 # 24 hours
        )
        
        print(f"DEBUG: Generated R2 Presigned URL: {presigned_url}", flush=True)
        return presigned_url

    except Exception as e:
        print(f"DEBUG: R2 upload failed: {e}", flush=True)
        return None
