import gdrive_utils
import os

def test_auth():
    print("Testing authentication...")
    creds = gdrive_utils.authenticate()
    if creds:
        print("Authentication successful.")
    else:
        print("Authentication failed.")
        return

    print("Testing upload...")
    # Create a dummy file
    with open("test_upload.txt", "w") as f:
        f.write("Hello Google Drive")
    
    try:
        link = gdrive_utils.upload_file("test_upload.txt", "test_upload.txt", "text/plain")
        if link:
            print(f"Upload successful. Link: {link}")
        else:
            print("Upload failed (no link returned).")
    except Exception as e:
        print(f"Upload raised exception: {e}")
    finally:
        if os.path.exists("test_upload.txt"):
            os.remove("test_upload.txt")

if __name__ == "__main__":
    test_auth()
