import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'service_account.json'

def authenticate():
    """Authenticates using service account."""
    logger.info(f"Checking for service account file at: {os.path.abspath(SERVICE_ACCOUNT_FILE)}")
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        logger.error(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
        return None
    
    try:
        logger.info("Attempting to authenticate with Google Drive API...")
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        logger.info("Authentication credentials created successfully.")
        return creds
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return None

def upload_file(file_path, file_name, mime_type=None):
    """
    Uploads a file to Google Drive and returns the direct download URL.
    Updates existing file if found by name, otherwise creates new.
    """
    logger.info(f"Starting upload process for {file_name}...")
    creds = authenticate()
    if not creds:
        logger.error("Upload aborted: No credentials available.")
        return None

    try:
        logger.info("Building Drive service...")
        service = build('drive', 'v3', credentials=creds)

        # Check if file exists
        logger.info(f"Checking if file '{file_name}' already exists in Drive...")
        query = f"name = '{file_name}' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        file_metadata = {'name': file_name}
        media = MediaFileUpload(file_path, mimetype=mime_type)

        file_id = None
        if files:
            # Update existing file
            file_id = files[0]['id']
            logger.info(f"Found existing file: {file_name} (ID: {file_id}). Updating...")
            updated_file = service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            logger.info(f"File updated successfully. ID: {updated_file.get('id')}")
        else:
            # Create new file
            logger.info(f"File '{file_name}' not found. Creating new file...")
            created_file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            file_id = created_file.get('id')
            logger.info(f"File created successfully. ID: {file_id}")

        if file_id:
            # Make file public
            logger.info(f"Setting public permissions for file ID: {file_id}...")
            permission = {
                'type': 'anyone',
                'role': 'reader',
            }
            service.permissions().create(
                fileId=file_id,
                body=permission,
            ).execute()
            logger.info("Public permissions set.")

            # Construct direct download link
            direct_link = f"https://drive.google.com/uc?export=download&id={file_id}"
            logger.info(f"Upload complete. Direct Link: {direct_link}")
            return direct_link
            
    except Exception as e:
        logger.error(f"Google Drive upload failed with error: {e}", exc_info=True)
        return None
