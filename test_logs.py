import gdrive_utils
import os

def test_logs():
    print("Testing logging of target folder...")
    filename = "test_log_upload.txt"
    with open(filename, "w") as f:
        f.write("Log Test")
    
    try:
        # This might fail with quota error, but we just want to see the logs
        gdrive_utils.upload_file(filename, filename, "text/plain")
    except Exception as e:
        print(f"Caught exception: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    test_logs()
