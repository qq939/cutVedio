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
    abs_path = os.path.abspath(SERVICE_ACCOUNT_FILE)
    print(f"DEBUG: Checking for service account file at: {abs_path}", flush=True)
    
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"DEBUG: Service account file NOT found at: {abs_path}", flush=True)
        # Try to list files in current directory to help debug
        print(f"DEBUG: Current working directory: {os.getcwd()}", flush=True)
        print(f"DEBUG: Files in current directory: {os.listdir('.')}", flush=True)
        return None
    
    try:
        print("DEBUG: Attempting to authenticate with Google Drive API...", flush=True)
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        print("DEBUG: Authentication credentials created successfully.", flush=True)
        return creds
    except Exception as e:
        print(f"DEBUG: Authentication failed: {e}", flush=True)
        return None

def upload_file(file_path, file_name, mime_type=None):
    """
    Uploads a file to Google Drive and returns the direct download URL.
    Updates existing file if found by name, otherwise creates new.
    """
    print(f"DEBUG: Starting upload process for {file_name}...", flush=True)
    creds = authenticate()
    if not creds:
        print("DEBUG: Upload aborted: No credentials available.", flush=True)
        return None

    try:
        print("DEBUG: Building Drive service...", flush=True)
        service = build('drive', 'v3', credentials=creds)

        # Check if file exists
        print(f"DEBUG: Checking if file '{file_name}' already exists in Drive...", flush=True)
        query = f"name = '{file_name}' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        file_metadata = {'name': file_name}
        media = MediaFileUpload(file_path, mimetype=mime_type)

        file_id = None
        if files:
            # Update existing file
            file_id = files[0]['id']
            print(f"DEBUG: Found existing file: {file_name} (ID: {file_id}). Updating...", flush=True)
            updated_file = service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            print(f"DEBUG: File updated successfully. ID: {updated_file.get('id')}", flush=True)
        else:
            # Create new file
            print(f"DEBUG: File '{file_name}' not found. Creating new file...", flush=True)
            created_file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            file_id = created_file.get('id')
            print(f"DEBUG: File created successfully. ID: {file_id}", flush=True)

        if file_id:
            # Make file public
            print(f"DEBUG: Setting public permissions for file ID: {file_id}...", flush=True)
            permission = {
                'type': 'anyone',
                'role': 'reader',
            }
            service.permissions().create(
                fileId=file_id,
                body=permission,
            ).execute()
            print("DEBUG: Public permissions set.", flush=True)

            # Construct direct download link
            direct_link = f"https://drive.google.com/uc?export=download&id={file_id}"
            print(f"DEBUG: Upload complete. Direct Link: {direct_link}", flush=True)
            return direct_link
            
    except Exception as e:
        print(f"DEBUG: Google Drive upload failed with error: {e}", flush=True)
        return None
