from flask import Blueprint, render_template, request, current_app, send_from_directory
import os
import json
from datetime import datetime
import glob

summary_bp = Blueprint('summary', __name__)

@summary_bp.route('/summary')
def view_summary():
    """View summary of a processed video."""
    video_filename = request.args.get('video')
    
    # Load stats if available (check for sidecar JSON first)
    stats = {}
    
    if video_filename:
        # Try to load sidecar JSON
        json_filename = f"{video_filename}.json"
        json_path = os.path.join(current_app.static_folder, 'processed', json_filename)
        
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                    stats = data.get('stats', {})
            except Exception as e:
                print(f"Error loading stats JSON: {e}")

    # Fallback to query params if stats missing
    if not stats:
        stats = {
            'unique_vehicles': request.args.get('unique', 0),
            'total_violations': request.args.get('violations', 0),
            'duration': request.args.get('duration', '0:00')
        }
    
    return render_template('summary.html', 
                          video_filename=video_filename,
                          stats=stats)

@summary_bp.route('/history')
def view_history():
    """List all processed videos."""
    processed_dir = os.path.join(current_app.static_folder, 'processed')
    
    videos = []
    if os.path.exists(processed_dir):
        # Find all mp4 files
        files = glob.glob(os.path.join(processed_dir, '*.mp4'))
        
        for f in files:
            # Get metadata (creation time, size)
            stat = os.stat(f)
            created = datetime.fromtimestamp(stat.st_ctime)
            size_mb = stat.st_size / (1024 * 1024)
            filename = os.path.basename(f)
            
            videos.append({
                'filename': filename,
                'created': created.strftime('%Y-%m-%d %H:%M'),
                'size': f"{size_mb:.1f} MB"
            })
    
    # Sort by newest first
    videos.sort(key=lambda x: x['created'], reverse=True)
    
    return render_template('history.html', videos=videos)
