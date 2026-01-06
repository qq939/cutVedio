import os
import shutil
from app import download_video

VIDEO_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp', 'test_video')
if not os.path.exists(VIDEO_FOLDER):
    os.makedirs(VIDEO_FOLDER)

def test_download():
    url = "https://www.douyin.com/video/7562905326119587122"
    print(f"Testing download for: {url}")
    try:
        filename = download_video(url, VIDEO_FOLDER)
        print(f"Download successful: {filename}")
    except Exception as e:
        print(f"Download failed: {e}")

if __name__ == "__main__":
    test_download()
