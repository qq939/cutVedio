import gdrive_utils
import os

def test_upload_folder():
    print("Testing upload to specific folder...")
    
    # Create a dummy file
    filename = "test_folder_upload.txt"
    with open(filename, "w") as f:
        f.write("Hello Google Drive Folder!")
    
    try:
        link = gdrive_utils.upload_file(filename, filename, "text/plain")
        if link:
            print(f"Upload successful. Link: {link}")
        else:
            print("Upload failed.")
    except Exception as e:
        print(f"Upload raised exception: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    test_upload_folder()
