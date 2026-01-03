from playwright.sync_api import sync_playwright
import time

def test_playwright():
    url = "https://v.douyin.com/zOWN6NkyUJo/"
    print(f"Testing Playwright with URL: {url}")
    
    with sync_playwright() as p:
        # Use headless=True for server environment
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        
        try:
            print("Navigating...")
            page.goto(url)
            print("Page loaded, waiting for video...")
            
            # Wait longer
            page.wait_for_selector('video', timeout=15000)
            print("Video selector found.")
            
            video_src = page.eval_on_selector('video', 'el => el.src')
            print(f"Video SRC: {video_src}")
            
            if video_src.startswith('blob:'):
                print("Blob detected.")
            else:
                print("Direct link found.")
                
        except Exception as e:
            print(f"Error: {e}")
            # print(page.content()) # Print content if needed
            
        finally:
            browser.close()

if __name__ == "__main__":
    test_playwright()
