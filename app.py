import os
import cv2
import time
import glob
import yt_dlp
import logging
import requests
import subprocess
from PIL import Image
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_from_directory
from playwright.sync_api import sync_playwright

load_dotenv()

app = Flask(__name__)

# Upload configuration
VIDEO_UPLOAD_URL = "http://obs.dimond.top/reference.mp4"
CHARACTER_UPLOAD_URL = "http://obs.dimond.top/character.png"

# Directory setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_FOLDER = os.path.join(BASE_DIR, 'tmp', 'images')
VIDEO_FOLDER = os.path.join(BASE_DIR, 'tmp', 'video')

for folder in [IMAGE_FOLDER, VIDEO_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/images/<path:filename>')
def serve_image(filename):
    response = send_from_directory(IMAGE_FOLDER, filename)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

@app.route('/video/<path:filename>')
def serve_video(filename):
    response = send_from_directory(VIDEO_FOLDER, filename)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

def get_douyin_video_url(url):
    """
    Use Playwright to get the actual video URL from Douyin page.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # Use mobile user agent to potentially get a simpler version or bypass some checks
            context = browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
            )
            page = context.new_page()
            
            logger.info(f"Navigating to {url}")
            try:
                page.goto(url, timeout=60000) # Increase timeout to 60 seconds
            except Exception as e:
                logger.warning(f"Page navigation timed out or failed: {e}")
                # Try to continue anyway, maybe it partially loaded
            
            # Wait for video element
            try:
                logger.info("Waiting for video element...")
                # Douyin usually puts video in a video tag or within a specific container
                # Wait for the video tag to be present
                page.wait_for_selector('video', timeout=15000)
                
                # Wait for src attribute to be present and non-empty
                try:
                    page.wait_for_function("document.querySelector('video') && document.querySelector('video').src && document.querySelector('video').src.length > 0", timeout=10000)
                except Exception as e:
                    logger.warning(f"Timeout waiting for video src to be non-empty: {e}")

                # Get src from video tag
                video_src = page.eval_on_selector('video', 'el => el.src')
                
                logger.info(f"Found video src: {video_src}")
                
                if not video_src:
                    logger.error("Video src is still empty after waiting.")
                    # Try to extract from script tags if video src is empty
                    try:
                         # Check for RENDER_DATA or other hydration data
                         page_content = page.content()
                         pass
                    except:
                         pass
                    
                    page.screenshot(path=os.path.join(IMAGE_FOLDER, 'debug.png'))
                    browser.close()
                    return None

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
                logger.warning(f"Could not find video element directly or timeout: {e}")
            
            browser.close()
            return None
    except Exception as e:
        logger.error(f"Playwright error: {e}")
        return None

class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        # We handle errors manually, so we can suppress them here or log as warning
        # Check if it's the known Douyin cookie error
        if "Fresh cookies" in msg:
            pass # Suppress this specific error log as we expect it
        else:
            logger.warning(f"yt-dlp error: {msg}")

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
        'logger': MyLogger(), # Use custom logger to suppress scary errors
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        # Fallback for Douyin if yt-dlp fails
        if 'douyin' in url:
            logger.info("Standard yt-dlp download failed (expected), attempting Playwright fallback for Douyin...")
            direct_url = get_douyin_video_url(url)
            if direct_url:
                logger.info(f"Found direct URL: {direct_url}")
                # Download direct URL using requests or curl, or just let yt-dlp try downloading that direct link
                # Using yt-dlp on direct link is often safer
                try:
                    ydl_opts.pop('cookiesfrombrowser', None) # Direct URL might not need cookies
                    # We can keep the logger or use default one for the second attempt. 
                    # Let's keep it to stay quiet.
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(direct_url, download=True)
                        filename = ydl.prepare_filename(info)
                        return filename
                except Exception as inner_e:
                     logger.error(f"Failed to download direct URL: {inner_e}")
                     raise e
            else:
                logger.error(f"Fallback failed to get direct URL. Original error: {e}")
                raise e
        else:
            logger.error(f"yt-dlp failed: {e}")
            raise e

def upload_to_obs(file_path, url):
    """
    Upload file to OBS URL using curl.
    """
    try:
        logger.info(f"Uploading {file_path} to {url}")
        # Use curl --upload-file as requested
        # Added -k for insecure/skip verify if needed (consistent with previous verify=False)
        # Added -v for verbose output if debugging needed, or remove for production
        command = ['curl', '-k', '--upload-file', file_path, url]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Curl usually returns 0 on success, but check http code if possible?
            # With --upload-file, if server returns error, curl might still exit 0 depending on version/flags.
            # But usually it's fine.
            logger.info(f"Upload successful: {url}")
            logger.info(f"Curl output: {result.stdout}")
            return True
        else:
            logger.error(f"Upload failed with exit code {result.returncode}")
            logger.error(f"Curl stderr: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return False

def convert_and_upload_character(source_path, target_url):
    """
    Convert image to png and upload.
    """
    try:
        if not os.path.exists(source_path):
             logger.error(f"Source file not found: {source_path}")
             return False
             
        # Load and convert image
        img = Image.open(source_path)
        # Convert to RGBA if necessary (webp can support transparency) or RGB
        img = img.convert("RGBA") 
        
        # Save to temporary png
        temp_png = os.path.join(BASE_DIR, 'tmp', 'character.png')
        img.save(temp_png, 'PNG')
        
        # Upload
        success = upload_to_obs(temp_png, target_url)
        
        # Clean up
        if os.path.exists(temp_png):
            os.remove(temp_png)
            
        return success
    except Exception as e:
        logger.error(f"Character conversion/upload error: {e}")
        return False

@app.route('/process', methods=['POST'])
def process_video():
    video_url = request.form.get('url')
    if not video_url:
        return jsonify({'error': 'No URL provided'}), 400

    downloaded_video_path = None
    try:
        # 1. Convert and upload character image (face/lulu.webp -> CHARACTER_UPLOAD_URL)
        character_path = os.path.join(BASE_DIR, 'face', 'lulu.webp')
        convert_and_upload_character(character_path, CHARACTER_UPLOAD_URL)
        
        # Clear previous frames
        for f in os.listdir(IMAGE_FOLDER):
            file_path = os.path.join(IMAGE_FOLDER, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        # Clear previous videos
        for f in os.listdir(VIDEO_FOLDER):
            file_path = os.path.join(VIDEO_FOLDER, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        # Download video using yt-dlp to VIDEO_FOLDER
        downloaded_video_path = download_video(video_url, VIDEO_FOLDER)
        
        # 2. Upload downloaded video to VIDEO_UPLOAD_URL
        upload_to_obs(downloaded_video_path, VIDEO_UPLOAD_URL)
        
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
                filepath = os.path.join(IMAGE_FOLDER, filename)
                cv2.imwrite(filepath, frame)
                # Return URL path
                saved_files.append(f"/images/{filename}")
                saved_count += 1
            
            frame_count += 1
            
            # Safety break
            if saved_count > 100: 
                break

        cap.release()
        
        # Do not delete the downloaded video file, we want to display it
        video_filename = os.path.basename(downloaded_video_path)
        
        return jsonify({
            'message': f'Successfully extracted {saved_count} frames.',
            'images': saved_files,
            'video_url': f"/video/{video_filename}",
            'original_url': video_url
        })

    except Exception as e:
        # Clean up if error
        if downloaded_video_path and os.path.exists(downloaded_video_path):
             pass # Keep it for debugging or it might be partial
        logger.error(f"Process failed: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use 5003 to avoid conflict
    app.run(debug=True, port=5003)
