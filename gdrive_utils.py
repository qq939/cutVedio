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
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        logger.error(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
        return None
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        return creds
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return None

def upload_file(file_path, file_name, mime_type=None):
    """
    Uploads a file to Google Drive and returns the direct download URL.
    Updates existing file if found by name, otherwise creates new.
    """
    creds = authenticate()
    if not creds:
        return None

    try:
        service = build('drive', 'v3', credentials=creds)

        # Check if file exists
        query = f"name = '{file_name}' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        file_metadata = {'name': file_name}
        media = MediaFileUpload(file_path, mimetype=mime_type)

        file_id = None
        if files:
            # Update existing file
            file_id = files[0]['id']
            logger.info(f"Updating existing file: {file_name} (ID: {file_id})")
            updated_file = service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
        else:
            # Create new file
            logger.info(f"Creating new file: {file_name}")
            created_file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            file_id = created_file.get('id')

        if file_id:
            # Make file public
            permission = {
                'type': 'anyone',
                'role': 'reader',
            }
            service.permissions().create(
                fileId=file_id,
                body=permission,
            ).execute()

            # Construct direct download link
            # Note: This link format is widely used but not officially documented as an API field.
            # Official way is webContentLink but it sometimes requires cookie.
            # 'https://drive.google.com/uc?export=download&id=' is good for direct access.
            direct_link = f"https://drive.google.com/uc?export=download&id={file_id}"
            logger.info(f"File uploaded successfully. Link: {direct_link}")
            return direct_link
            
    except Exception as e:
        logger.error(f"Google Drive upload failed: {e}")
        return None
