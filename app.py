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
import obs_utils
import comfy_utils

load_dotenv()

app = Flask(__name__)

# Upload configuration
VIDEO_UPLOAD_URL = "http://obs.dimond.top/reference.mp4"
CHARACTER_UPLOAD_URL = "http://obs.dimond.top/character.png"

# Directory setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_FOLDER = os.path.join(BASE_DIR, 'tmp', 'images')
VIDEO_FOLDER = os.path.join(BASE_DIR, 'tmp', 'video')
ULTRA_VIDEO_FOLDER = os.path.join(BASE_DIR, 'tmp', 'ultraVideo')

for folder in [IMAGE_FOLDER, VIDEO_FOLDER, ULTRA_VIDEO_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'ok', 'message': 'Server is running'})

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

@app.route('/ultraVideo/<path:filename>')
def serve_ultra_video(filename):
    response = send_from_directory(ULTRA_VIDEO_FOLDER, filename)
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
                # Use domcontentloaded to return faster, as we don't need full load (images etc)
                # Reduce timeout to 30s
                page.goto(url, timeout=30000, wait_until='domcontentloaded') 
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
                with open('urls.txt', 'a') as f:
                    f.write(video_src + "\n")
                
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
        try:
            logger.info("Attempting download with cookies...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return filename
        except Exception as cookie_error:
            logger.warning(f"Download with cookies failed: {cookie_error}. Retrying without cookies...")
            # Remove cookies and retry
            if 'cookiesfrombrowser' in ydl_opts:
                del ydl_opts['cookiesfrombrowser']
            
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

def convert_and_upload_character(source_path):
    """
    Convert image to png and upload to OBS.
    """
    try:
        if not os.path.exists(source_path):
             logger.error(f"Source file not found: {source_path}")
             return None
             
        # Load and convert image
        img = Image.open(source_path)
        # Convert to RGBA if necessary (webp can support transparency) or RGB
        img = img.convert("RGBA") 
        
        # Save to temporary png
        temp_png = os.path.join(BASE_DIR, 'tmp', 'character.png')
        img.save(temp_png, 'PNG')
        
        # Upload to OBS
        obs_url = obs_utils.upload_file(temp_png, 'character.png', mime_type='image/png')
        
        # Clean up
        if os.path.exists(temp_png):
            os.remove(temp_png)
            
        return obs_url
    except Exception as e:
        logger.error(f"Character conversion/upload error: {e}")
        return None

import re

@app.route('/manual_upload/character_image', methods=['POST'])
def manual_upload_character_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
            
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if file:
            # Use temp file instead of persistent face/lulu.webp
            temp_dir = os.path.join(BASE_DIR, 'tmp')
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
                
            # We want to convert to PNG and name it lulu.png (conceptually for OBS)
            # But locally we just need a temp file.
            temp_path = os.path.join(temp_dir, 'lulu_temp.png')
            
            try:
                img = Image.open(file)
                # Convert to RGBA for PNG
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGBA')
                    
                img.save(temp_path, 'PNG')
                logger.info(f"Uploaded image converted to PNG: {temp_path}")
                
                # Upload to OBS as character.png
                obs_url = obs_utils.upload_file(temp_path, 'character.png', mime_type='image/png')
                
                # Clean up
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
                if obs_url:
                    return jsonify({'message': 'Image uploaded to OBS as character.png successfully', 'url': obs_url})
                else:
                    return jsonify({'error': 'Failed to upload to OBS'}), 500
                    
            except Exception as convert_error:
                logger.error(f"Image conversion/upload error: {convert_error}")
                return jsonify({'error': f'Failed to process image: {convert_error}'}), 500
                
    except Exception as e:
        logger.error(f"Upload image error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_video', methods=['POST'])
def api_generate_video():
    try:
        data = request.json
        # comfy_utils needs local paths, not URLs.
        # But our frontend sends URLs like /images/lulu.webp or OBS URLs?
        # Let's check frontend.
        # Frontend sends:
        # character_url: data.upload_urls.character (OBS URL)
        # video_url: data.upload_urls.video (OBS URL)
        
        # However, ComfyUI needs to upload files from LOCAL server to ComfyUI server.
        # So we should use the local file paths if available.
        # But api_generate_video is called from frontend which has URLs.
        
        # We need to map these URLs back to local files or re-download them.
        # Since we are on the same server, we can deduce the local path.
        
        # character_url usually is http://.../character.png (OBS)
        # But we also have it locally at face/lulu.webp or tmp/character.png
        # Let's use the standard local paths.
        
        character_path = os.path.join(BASE_DIR, 'face', 'lulu.webp')
        
        # For video, we need to find the latest downloaded video in VIDEO_FOLDER
        # Or pass the filename from frontend?
        # The frontend sends 'video_url' which is OBS URL.
        # But we processed the video and saved it in tmp/video/
        
        # Let's try to find the video file in tmp/video/
        # Just pick the latest one or the one that matches the OBS upload?
        # Simple approach: Pick the latest mp4 in tmp/video/
        
        files = glob.glob(os.path.join(VIDEO_FOLDER, '*.*'))
        video_files = [f for f in files if not os.path.basename(f).startswith('.')]
        if not video_files:
             return jsonify({'error': 'No local video file found'}), 400
             
        video_files.sort(key=os.path.getmtime, reverse=True)
        video_path = video_files[0]
        
        logger.info(f"Submitting ComfyUI job with: Char={character_path}, Video={video_path}")
        
        task_id, error = comfy_utils.submit_job(character_path, video_path)
        
        if task_id:
            return jsonify({'message': 'Task started', 'task_id': task_id})
        else:
            return jsonify({'error': f'Failed to start ComfyUI task: {error}'}), 500
            
    except Exception as e:
        logger.error(f"Generate video API error: {e}")
        return jsonify({'error': str(e)}), 500

from datetime import datetime

@app.route('/api/task_status/<task_id>', methods=['GET'])
def api_task_status(task_id):
    try:
        logger.info(f"Checking status for task_id: {task_id}")
        # Log request details
        logger.info(f"Request Headers: {request.headers}")
        
        status, result = comfy_utils.check_status(task_id)
        logger.info(f"Status result for {task_id}: {status}, {result}")
        
        # If succeeded, result contains file_info dict
        if status == 'SUCCEEDED' and isinstance(result, dict):
            try:
                # Download result to ULTRA_VIDEO_FOLDER
                local_path = comfy_utils.download_result(result, ULTRA_VIDEO_FOLDER)
                
                if local_path:
                    filename = os.path.basename(local_path)
                    
                    # Upload to OBS with new naming convention
                    # Naming: 【YYYY_MM_DD_HH_MM_SS】new.mp4
                    now = datetime.now()
                    obs_filename = now.strftime("【%Y_%m_%d_%H_%M_%S】new.mp4")
                    
                    logger.info(f"Uploading generated video to OBS as: {obs_filename}")
                    try:
                        obs_utils.upload_file(local_path, obs_filename, mime_type='video/mp4')
                        logger.info(f"Successfully uploaded generated video to OBS: {obs_filename}")
                    except Exception as obs_error:
                        logger.error(f"Failed to upload generated video to OBS: {obs_error}")
                        # We don't fail the request if OBS upload fails, just log it
                    
                    # Return the local URL
                    local_url = f"/ultraVideo/{filename}"
                    return jsonify({'status': status, 'result': local_url})
                else:
                    return jsonify({'status': 'FAILED', 'result': 'Download failed'})
                
            except Exception as download_error:
                logger.error(f"Error downloading generated video: {download_error}")
                return jsonify({'status': 'FAILED', 'result': str(download_error)})

        return jsonify({'status': status, 'result': result})
    except Exception as e:
        logger.error(f"Task status API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/comfy/upload_character', methods=['POST'])
def api_comfy_upload_character():
    try:
        character_path = os.path.join(BASE_DIR, 'face', 'lulu.webp')
        if not os.path.exists(character_path):
             return jsonify({'error': 'Character file not found'}), 404
             
        res = comfy_utils.client.upload_file(character_path, overwrite=True)
        if res:
            return jsonify({'message': 'Character uploaded to ComfyUI', 'filename': res.get('name')})
        else:
            return jsonify({'error': 'Failed to upload character'}), 500
    except Exception as e:
        logger.error(f"Comfy upload character error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/comfy/upload_video', methods=['POST'])
def api_comfy_upload_video():
    try:
        files = glob.glob(os.path.join(VIDEO_FOLDER, '*.*'))
        video_files = [f for f in files if not os.path.basename(f).startswith('.')]
        if not video_files:
             return jsonify({'error': 'No local video file found'}), 404
             
        video_files.sort(key=os.path.getmtime, reverse=True)
        video_path = video_files[0]
        
        res = comfy_utils.client.upload_file(video_path, overwrite=True)
        if res:
            return jsonify({'message': 'Video uploaded to ComfyUI', 'filename': res.get('name')})
        else:
            return jsonify({'error': 'Failed to upload video'}), 500
    except Exception as e:
        logger.error(f"Comfy upload video error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/comfy/execute', methods=['POST'])
def api_comfy_execute():
    try:
        data = request.json or {}
        
        # Check for cancel request
        cancel_task_id = data.get('cancel_task_id')
        if cancel_task_id:
            logger.info(f"Cancelling previous task: {cancel_task_id}")
            result = comfy_utils.cancel_job(cancel_task_id)
            logger.info(f"Cancellation result for {cancel_task_id}: {result}")
            print(f"DEBUG: Cancelled task {cancel_task_id}, result: {result}", flush=True)
            
        # We assume files are already uploaded and we know their names or use defaults?
        # comfy_utils.queue_workflow_template needs filenames.
        # But here we don't know the exact filenames ComfyUI assigned unless frontend sends them.
        # But typically ComfyUI keeps the filename.
        # Let's re-resolve filenames from local paths as best guess or use params.
        
        # Option: Frontend sends filenames if available, else we guess.
        char_filename = data.get('char_filename')
        video_filename = data.get('video_filename')
        prompt_text = data.get('prompt_text')
        
        if not char_filename:
             char_filename = "lulu.webp" # Default
        
        if not video_filename:
             # Guess from local video
             files = glob.glob(os.path.join(VIDEO_FOLDER, '*.*'))
             video_files = [f for f in files if not os.path.basename(f).startswith('.')]
             if video_files:
                 video_files.sort(key=os.path.getmtime, reverse=True)
                 video_filename = os.path.basename(video_files[0])
        
        if not char_filename or not video_filename:
             return jsonify({'error': 'Could not determine filenames'}), 400
             
        task_id, error = comfy_utils.queue_workflow_template(char_filename, video_filename, prompt_text=prompt_text)
        
        if task_id:
            return jsonify({'message': 'Task queued', 'task_id': task_id})
        else:
            return jsonify({'error': f'Failed to queue task: {error}'}), 500
            
    except Exception as e:
        logger.error(f"Comfy execute error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/comfy/status', methods=['GET'])
def api_comfy_status():
    try:
        is_connected = comfy_utils.client.check_connection()
        return jsonify({'status': 'connected' if is_connected else 'disconnected'})
    except Exception as e:
        logger.error(f"Comfy status check error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/overall', methods=['POST'])
def api_overall():
    try:
        # Check if video file is present in request
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
            
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        logger.info(f"Overall process started with file: {file.filename}")
        
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
                
        # Save uploaded file
        ext = os.path.splitext(file.filename)[1]
        if not ext:
            ext = '.mp4'
        
        filename = f"uploaded_video{ext}"
        video_path = os.path.join(VIDEO_FOLDER, filename)
        file.save(video_path)
        
        logger.info(f"Saved uploaded video to {video_path}")
        
        # Run pipeline
        result, status_code = _run_processing_pipeline(video_path, file.filename)
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Overall API error: {e}")
        return jsonify({'error': str(e)}), 500

def trim_video(input_path, output_path, duration=9):
    """
    Trim video to the first `duration` seconds using ffmpeg.
    """
    try:
        # ffmpeg -y -i input.mp4 -t 9 -c copy output.mp4
        # -y: overwrite output
        # -i: input
        # -t: duration
        # -c copy: copy streams (fast, no re-encoding)
        # Note: -c copy might be inaccurate for cutting, but fast. 
        # For precise cutting, we might need re-encoding or at least -c:v libx264
        # Let's try re-encoding for safety and compatibility with ComfyUI/OBS if codec is weird.
        # But re-encoding is slow.
        # Let's try -c copy first, if it fails or produces bad video, switch to re-encoding.
        # Actually, for "first 9 seconds", -t before -i is faster but less accurate seek. -t after -i is accurate.
        
        command = [
            'ffmpeg', '-y', 
            '-i', input_path, 
            '-t', str(duration), 
            '-c:v', 'libx264', # Re-encode video to ensure compatibility
            '-c:a', 'aac',     # Re-encode audio
            '-strict', 'experimental',
            output_path
        ]
        
        logger.info(f"Trimming video: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Video trimmed successfully: {output_path}")
            return True
        else:
            logger.error(f"FFmpeg failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Trim video error: {e}")
        return False

def _run_processing_pipeline(video_path, source_name):
    """
    Common pipeline for processing a video file (local path).
    1. Trim video to 9 seconds.
    2. Upload character to OBS.
    3. Upload trimmed video to OBS.
    4. Submit to ComfyUI.
    5. Extract frames.
    6. Return result dict.
    """
    try:
        # 0. Trim Video
        logger.info(f"Trimming video {video_path} to 9 seconds...")
        # Create a new filename for trimmed video
        dir_name = os.path.dirname(video_path)
        base_name = os.path.basename(video_path)
        name, ext = os.path.splitext(base_name)
        trimmed_filename = f"{name}_trimmed{ext}"
        trimmed_path = os.path.join(dir_name, trimmed_filename)
        
        if trim_video(video_path, trimmed_path, duration=9):
            logger.info(f"Using trimmed video: {trimmed_path}")
            # Use trimmed video for subsequent steps
            video_path = trimmed_path
        else:
            logger.warning("Trimming failed, using original video.")

        # 1. Convert and upload character image (face/lulu.webp -> OBS)
        print("DEBUG: Starting character upload...", flush=True)
        character_path = os.path.join(BASE_DIR, 'face', 'lulu.webp')
        character_url = convert_and_upload_character(character_path)
        print(f"DEBUG: Character upload result: {character_url}", flush=True)
        logger.info(f"Character uploaded to: {character_url}")
        
        # 2. Upload video to OBS
        video_filename = os.path.basename(video_path)
        print(f"DEBUG: Starting video upload to OBS ({video_filename})...", flush=True)
        video_obs_url = obs_utils.upload_file(video_path, 'reference.mp4', mime_type='video/mp4')
        print(f"DEBUG: Video upload result: {video_obs_url}", flush=True)
        logger.info(f"Video uploaded to: {video_obs_url}")
        
        # 3. Trigger Aliyun Image2Video Task (Async via frontend)
        print("DEBUG: Auto-submitting to ComfyUI via OBS URLs...", flush=True)
        if character_url and video_obs_url:
            task_id, error = comfy_utils.submit_job_with_urls(character_url, video_obs_url)
        else:
            task_id, error = None, "Missing OBS URLs"
            
        if task_id:
            logger.info(f"Auto-submitted ComfyUI task: {task_id}")
        else:
            logger.error(f"Failed to auto-submit ComfyUI task: {error}")

        # 4. Extract frames
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
             return {'error': 'Could not open video file'}, 400
             
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
        
        # Clean up local video file to avoid storage in video folder
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                logger.info(f"Removed local video file: {video_path}")
            # Also remove original if it was different (e.g. if we trimmed)
            # But we need to be careful if video_path was reassigned.
            # The original passed to this function was the raw upload/download.
            # If we trimmed, video_path is trimmed_path.
            # We should clean up the original too if it's in VIDEO_FOLDER.
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up video file: {cleanup_error}")
        
        return {
            'message': f'Successfully extracted {saved_count} frames. Uploaded to OBS.',
            'images': saved_files,
            'video_url': video_obs_url if video_obs_url else f"/video/{video_filename}",
            'original_url': source_name,
            'task_id': task_id,
            'upload_urls': {
                'character': character_url,
                'video': video_obs_url
            }
        }, 200

    except Exception as e:
        logger.error(f"Pipeline processing failed: {e}")
        return {'error': str(e)}, 500

@app.route('/process_upload', methods=['POST'])
def process_upload_video():
    print("DEBUG: Received process_upload request", flush=True)
    
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
        
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    try:
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
                
        # Save uploaded file
        # Use a safe filename or keep original? Let's use standard name to avoid issues?
        # But we need extension.
        ext = os.path.splitext(file.filename)[1]
        if not ext:
            ext = '.mp4'
        
        filename = f"uploaded_video{ext}"
        video_path = os.path.join(VIDEO_FOLDER, filename)
        file.save(video_path)
        
        logger.info(f"Saved uploaded video to {video_path}")
        
        result, status_code = _run_processing_pipeline(video_path, file.filename)
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Process upload failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process_video():
    print("DEBUG: Received process_video request", flush=True)
    raw_input = request.form.get('url')
    if not raw_input:
        print("DEBUG: No input provided", flush=True)
        return jsonify({'error': 'No input provided'}), 400

    # Extract URL from input text using regex
    # Matches http:// or https:// followed by non-whitespace characters
    url_match = re.search(r'(https?://[^\s]+)', raw_input)
    if url_match:
        video_url = url_match.group(1)
        print(f"DEBUG: Extracted URL: {video_url} from input: {raw_input}", flush=True)
        logger.info(f"Extracted URL: {video_url} from input: {raw_input}")
    else:
        # If no URL found, assume the input is the URL itself (fallback)
        video_url = raw_input.strip()
        print(f"DEBUG: No URL pattern found, using raw input: {video_url}", flush=True)
        logger.warning(f"No URL pattern found, using raw input: {video_url}")

    downloaded_video_path = None
    try:
        # Clear previous frames
        print("DEBUG: Clearing previous frames...", flush=True)
        for f in os.listdir(IMAGE_FOLDER):
            file_path = os.path.join(IMAGE_FOLDER, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        # Clear previous videos
        print("DEBUG: Clearing previous videos...", flush=True)
        for f in os.listdir(VIDEO_FOLDER):
            file_path = os.path.join(VIDEO_FOLDER, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        # Download video using yt-dlp to VIDEO_FOLDER
        print(f"DEBUG: Starting video download from {video_url}...", flush=True)
        downloaded_video_path = download_video(video_url, VIDEO_FOLDER)
        print(f"DEBUG: Video downloaded to {downloaded_video_path}", flush=True)
        
        result, status_code = _run_processing_pipeline(downloaded_video_path, video_url)
        return jsonify(result), status_code

    except Exception as e:
        # Clean up if error
        if downloaded_video_path and os.path.exists(downloaded_video_path):
             pass # Keep it for debugging or it might be partial
        logger.error(f"Process failed: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use 5003 to avoid conflict
    app.run(host='0.0.0.0', debug=True, port=5020)
