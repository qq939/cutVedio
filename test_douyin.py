from douyin_utils import DouyinUtils
import os

def test_douyin():
    url = "https://v.douyin.com/zOWN6NkyUJo/"
    utils = DouyinUtils()
    print(f"Testing URL: {url}")
    
    real_url = utils.get_video_url(url)
    if real_url:
        print(f"Success! Real URL found: {real_url}")
    else:
        print("Failed to get real URL")

if __name__ == "__main__":
    test_douyin()
