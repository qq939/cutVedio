import os
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
TARGET_FOLDER_ID = '1MvK_nCmctk1KjtXrcDoc1ZKmQEZ5lRwD'

def authenticate():
    """Authenticates using OAuth 2.0 (User Account)."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE):
        print("DEBUG: Found existing token.json, attempting to load credentials...", flush=True)
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("DEBUG: Credentials expired, refreshing...", flush=True)
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"DEBUG: Failed to refresh token: {e}", flush=True)
                creds = None
        
        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"DEBUG: Credentials file '{CREDENTIALS_FILE}' not found.", flush=True)
                return None
            
            print("DEBUG: Starting new OAuth flow...", flush=True)
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                # run_local_server will open a browser window
                creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                print("DEBUG: Saving new credentials to token.json...", flush=True)
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"DEBUG: OAuth flow failed: {e}", flush=True)
                return None
                
    return creds

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

        # Check if file exists in the specific folder
        print(f"DEBUG: Checking if file '{file_name}' already exists in Drive folder {TARGET_FOLDER_ID}...", flush=True)
        query = f"name = '{file_name}' and '{TARGET_FOLDER_ID}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        file_metadata = {
            'name': file_name,
            'parents': [TARGET_FOLDER_ID]
        }
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
        if "storageQuotaExceeded" in str(e):
             print(f"DEBUG: Storage quota exceeded for folder {TARGET_FOLDER_ID} (https://drive.google.com/drive/folders/{TARGET_FOLDER_ID}).", flush=True)
             print("DEBUG: Please clean up the Google Drive or the target folder.", flush=True)
        return None
