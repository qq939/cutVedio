import os
import r2_utils
from dotenv import load_dotenv

load_dotenv()

def test_r2():
    print("Testing R2 upload (REST API)...")
    
    # Check env vars
    token = os.getenv('CLOUDFLARER2TOKEN')
    print(f"CLOUDFLARER2TOKEN present: {bool(token)}")
    if token:
        print(f"Token length: {len(token)}")
    
    # Create dummy file
    filename = "test_r2_rest.txt"
    with open(filename, "w") as f:
        f.write("Hello Cloudflare R2 REST API")
    
    try:
        url = r2_utils.upload_file(filename, filename, "text/plain")
        if url:
            print(f"Upload successful. URL: {url}")
        else:
            print("Upload failed.")
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    test_r2()
