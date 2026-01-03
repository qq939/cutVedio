import os
import cv2
import time
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)
UPLOAD_FOLDER = '/tmp/vedio'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_video():
    video_url = request.form.get('url')
    if not video_url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        # Clear previous frames
        for f in os.listdir(UPLOAD_FOLDER):
            os.remove(os.path.join(UPLOAD_FOLDER, f))
        
        cap = cv2.VideoCapture(video_url)
        if not cap.isOpened():
             return jsonify({'error': 'Could not open video URL'}), 400
             
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
             # Fallback if FPS cannot be determined
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
            
            # Safety break to prevent infinite loops on streams or too long videos
            if saved_count > 100: 
                break

        cap.release()
        
        return jsonify({
            'message': f'Successfully extracted {saved_count} frames.',
            'images': saved_files
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
