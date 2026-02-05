from flask import request, jsonify, current_app, render_template, redirect, url_for
from app.routes import upload_bp
from app import db
from app.models import Violation
from app.ai.pipeline import VideoPipeline
import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mkv'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@upload_bp.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file part'}), 400
    
    file = request.files['video']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Generate unique filename to prevent overwrites
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        try:
            # Ensure directories exist
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Save video file
            file.save(save_path)
            
            print(f"✅ Video uploaded: {unique_filename}")
            
            # Check if ROI config exists for this video
            video_name = os.path.splitext(filename)[0]
            roi_config_path = f"config/roi/{video_name}.json"
            
            if not os.path.exists(roi_config_path):
                # Use default config if exists
                roi_config_path = "config/roi/traffic_video_modified.json"
            
            # Return redirect URL to live processing page
            live_url = url_for('upload.live_processing', 
                             video_path=save_path,
                             roi_config_path=roi_config_path if os.path.exists(roi_config_path) else '')
            
            return jsonify({
                'message': 'Video uploaded successfully',
                'filename': unique_filename,
                'redirect_url': live_url
            }), 201
            
        except Exception as e:
            print(f"❌ Error uploading video: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Upload failed: {str(e)}'}), 500
    
    return jsonify({'error': 'File type not allowed'}), 400


@upload_bp.route('/live')
def live_processing():
    """Render live processing page."""
    return render_template('live_processing.html')
