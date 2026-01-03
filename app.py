import os
import cv2
import time
import glob
import yt_dlp
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)
UPLOAD_FOLDER = '/tmp/vedio'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

def download_video(url, output_dir):
    """
    Download video using yt-dlp.
    Returns the path to the downloaded video file.
    """
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
        'quiet': True,
        'noplaylist': True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename

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
        # We download to UPLOAD_FOLDER temporarily, but maybe better to use a temp file
        # to avoid mixing with frames. Let's use UPLOAD_FOLDER for simplicity but clean up.
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
            os.remove(downloaded_video_path)
        return jsonify({'error': str(e)}), 500

@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
