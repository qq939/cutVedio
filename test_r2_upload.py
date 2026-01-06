import os
import r2_utils
from dotenv import load_dotenv

load_dotenv()

def test_r2_upload():
    print("Testing R2 Upload...")
    
    # Create a dummy file
    test_file = "test_r2_upload.txt"
    with open(test_file, "w") as f:
        f.write("This is a test file for R2 upload.")
        
    try:
        url = r2_utils.upload_file(test_file, test_file, mime_type="text/plain")
        if url:
            print(f"Success! File uploaded to: {url}")
        else:
            print("Failed to upload file.")
    except Exception as e:
        print(f"Error during upload: {e}")
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    test_r2_upload()
