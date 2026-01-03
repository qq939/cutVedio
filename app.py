import os
import cv2
import time
import glob
import yt_dlp
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from playwright.sync_api import sync_playwright

app = Flask(__name__)
UPLOAD_FOLDER = '/tmp/vedio'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def get_douyin_video_url(url):
    """
    Use Playwright to get the actual video URL from Douyin page.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            logger.info(f"Navigating to {url}")
            page.goto(url)
            
            # Wait for video element
            try:
                # Douyin usually puts video in a video tag or within a specific container
                # Wait for the video tag to be present
                page.wait_for_selector('video', timeout=15000)
                
                # Get src from video tag
                video_src = page.eval_on_selector('video', 'el => el.src')
                # Sometimes src is blob, we might need to look for source tags or intercept network requests
                
                if video_src.startswith('blob:'):
                    logger.info("Blob URL detected, trying to find real URL from network requests")
                    # If blob, we might need to intercept network requests (more complex)
                    # For simple cases, let's try to see if there are other attributes
                    # Or check for specific douyin video patterns in network
                    pass
                else:
                    logger.info(f"Found video src: {video_src}")
                    browser.close()
                    return video_src

            except Exception as e:
                logger.warning(f"Could not find video element directly: {e}")
            
            browser.close()
            return None
    except Exception as e:
        logger.error(f"Playwright error: {e}")
        return None

def download_video(url, output_dir):
    """
    Download video using yt-dlp.
    Returns the path to the downloaded video file.
    """
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
        'quiet': True,
        'noplaylist': True,
        'cookiesfrombrowser': ('chrome',), 
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        logger.error(f"yt-dlp failed: {e}")
        # Fallback for Douyin if yt-dlp fails
        if 'douyin' in url:
            logger.info("Attempting Playwright fallback for Douyin...")
            direct_url = get_douyin_video_url(url)
            if direct_url:
                logger.info(f"Found direct URL: {direct_url}")
                # Download direct URL using requests or curl, or just let yt-dlp try downloading that direct link
                # Using yt-dlp on direct link is often safer
                try:
                    ydl_opts.pop('cookiesfrombrowser', None) # Direct URL might not need cookies
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(direct_url, download=True)
                        filename = ydl.prepare_filename(info)
                        return filename
                except Exception as inner_e:
                     logger.error(f"Failed to download direct URL: {inner_e}")
                     raise e
            else:
                raise e
        else:
            raise e

@app.route('/process', methods=['POST'])
def process_video():
    video_url = request.form.get('url')
    if not video_url:
        return jsonify({'error': 'No URL provided'}), 400

    downloaded_video_path = None
    try:
        # Clear previous frames
        for f in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        # Download video using yt-dlp
        downloaded_video_path = download_video(video_url, UPLOAD_FOLDER)
        
        cap = cv2.VideoCapture(downloaded_video_path)
        if not cap.isOpened():
             return jsonify({'error': 'Could not open downloaded video'}), 400
             
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
             fps = 30 
             
        # Extract frame every 1 second
        frame_interval = int(fps) 
        frame_count = 0
        saved_count = 0
        saved_files = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                filename = f"frame_{saved_count}.jpg"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                cv2.imwrite(filepath, frame)
                saved_files.append(filename)
                saved_count += 1
            
            frame_count += 1
            
            # Safety break
            if saved_count > 100: 
                break

        cap.release()
        
        # Clean up the downloaded video file
        if downloaded_video_path and os.path.exists(downloaded_video_path):
            os.remove(downloaded_video_path)
        
        return jsonify({
            'message': f'Successfully extracted {saved_count} frames.',
            'images': saved_files
        })

    except Exception as e:
        # Clean up if error
        if downloaded_video_path and os.path.exists(downloaded_video_path):
            try:
                os.remove(downloaded_video_path)
            except:
                pass
        return jsonify({'error': str(e)}), 500

@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    # Use 5002 to avoid conflict
    app.run(debug=True, port=5002)
