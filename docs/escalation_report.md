# Escalation Handoff Report

**Generated:** 2026-02-09
**Original Issue:** Video Playback & Portability (Clipping + Codec)

---

## PART 1: THE DAMAGE REPORT

### 1.1 Original Goal
The user wanted to:
1.  **Fix "Black Screen" Videos:** Ensure processed videos and violation clips play correctly in the browser.
2.  **Generate Violation Clips:** Automatically extract a 5-second clip (2.5s before/after) for each violation.
3.  **Ensure Portability:** Make sure the solution works on other machines, specifically regarding `ffmpeg` dependencies.

### 1.2 Observed Failure / Error
-   **Playback Issues:** The user reported "video is not playing back" even after the fixes. This is likely because the server process wasn't restarted to load the new code, OR because the browser doesn't support the codec of the existing/new videos.
-   **Portability Concerns:** The user is worried that "it's my personal configuration since it's ffmpeg I have on my pc" and wants to ensure it works elsewhere.
-   **Installation Stalls:** During implementation, `pip install moviepy` took an excessively long time/timed out, forcing a fallback to a hybrid approach that might be fragile on systems without pre-installed FFmpeg.

### 1.3 Failed Approach
-   **Hybrid Clipper:** Implemented `app/utils/video_clip.py` to try `moviepy` first (for portability) and fall back to system `ffmpeg` (via `subprocess`).
-   **Codec Fix:** Updated `app/ai/video_annotator.py` to convert videos to H.264 using system `ffmpeg`.
-   **Dependence on Restart:** The solution heavily relies on the user restarting the Flask server to take effect, which is a friction point and source of confusion.
-   **Dependency Hell:** `moviepy` brings in `imageio-ffmpeg`, which attempts to download a binary. This failed/stalled in the user's environment, leading to a potentially incomplete setup.

### 1.4 Key Files Involved
-   `app/utils/video_clip.py` (The hybrid clipper logic)
-   `app/ai/pipeline.py` (Integration of clipping into the main loop)
-   `app/ai/video_annotator.py` (Video generation and codec conversion)
-   `app/routes/violations.py` (Route handler with existence/size checks)
-   `app/routes/admin.py` (Reset DB logic that now deletes files)
-   `requirements.txt` (Added `moviepy`)

### 1.5 Best-Guess Diagnosis
1.  **Codec:** The "black screen" is almost certainly due to OpenCV defaulting to `mp4v`. The fix (converting to `libx264` via ffmpeg) is correct but might not be running if the server wasn't restarted or if `ffmpeg` isn't in the system PATH of the intended deployment target.
2.  **Portability:** The user is right to be concerned. If a target machine doesn't have `ffmpeg` installed globally AND `moviepy` fails to install its binary (as it did here initially), the clipping and conversion will fail. Redundancy is good, but a guaranteed binary strategy is better.
3.  **Flow:** The "Reset DB" feature was disconnected from file deletion, causing "ghost" history. This is fixed in `admin.py` but requires verification.

---

## PART 2: FULL FILE CONTENTS (Self-Contained)

### File: `app/utils/video_clip.py`
```python
import os
import uuid
import subprocess

try:
    from moviepy.editor import VideoFileClip
    HAS_MOVIEPY = True
except ImportError:
    HAS_MOVIEPY = False

def extract_clip(source_path, output_folder, violation_time_seconds, duration=5.0):
    """
    Extracts a clip around the violation time.
    Tries moviepy first, falls back to system ffmpeg.
    
    Args:
        source_path (str): Path to the full source video.
        output_folder (str): Folder to save the clip.
        violation_time_seconds (float): Time of violation in seconds.
        duration (float): Total duration of the clip (default 5s).
        
    Returns:
        str: Filename of the generated clip, or None if failed.
    """
    try:
        # Calculate start and end times
        half_duration = duration / 2
        start_time = max(0, violation_time_seconds - half_duration)
        
        # Generate unique filename
        filename = f"clip_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(output_folder, filename)

        if HAS_MOVIEPY:
            print("Using moviepy for clipping...")
            with VideoFileClip(source_path) as video:
                # Ensure we don't go past end
                end_time = min(video.duration, start_time + duration)
                clip = video.subclip(start_time, end_time)
                
                clip.write_videofile(
                    output_path, 
                    codec='libx264', 
                    audio_codec='aac', 
                    temp_audiofile=f'temp-audio-{uuid.uuid4().hex[:8]}.m4a',
                    remove_temp=True,
                    logger=None
                )
                return filename
        else:
            print("Using system ffmpeg for clipping...")
            # Fallback to subprocess
            cmd = [
                'ffmpeg', '-y',
                '-ss', str(start_time),
                '-i', source_path,
                '-t', str(duration),
                '-c:v', 'libx264',
                '-c:a', 'aac',
                output_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"Clip created successfully: {output_path}")
                return filename
            else:
                print("ffmpeg command failed to create output file.")
                return None
            
    except Exception as e:
        print(f"Error extracting clip: {e}")
        return None
```

### File: `app/ai/pipeline.py`
```python
import cv2
from app import db
from app.models import Violation
from app.ai.detector import VehicleDetector
from app.ai.red_light import RedLightSystem
from app.ai.speed import SpeedSystem
from app.ai.lane import LaneSystem
from app.ai.anpr import ANPR_System
from app.ai.vehicle_tracker import VehicleTracker
from app.utils.video import save_frame
import os
import uuid
from datetime import datetime

class VideoPipeline:
    def __init__(self, config):
        """
        Initialize the processing pipeline.
        """
        self.config = config
        self.detector = VehicleDetector() # Loads YOLO
        self.red_light = RedLightSystem()
        self.speed = SpeedSystem()
        self.lane = LaneSystem()
        self.anpr = ANPR_System()
        self.tracker = VehicleTracker(iou_threshold=0.3, max_missing_frames=10)
        
        # Load ROIs from config if available
        # self.red_light.set_roi(config.STOP_LINE_ROI)
        # self.lane.set_rois(config.LANE_ROIS)
        
    def process_video(self, video_path):
        """
        Process a video file end-to-end.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"error": "Could not open video"}
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        self.speed.update_fps(fps)
        
        frame_count = 0
        violations_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            
            # 1. Detect signal state (Red/Green)
            signal_state = self.red_light.detect_signal_state(frame)
            
            # 2. Detect vehicles
            detections = self.detector.detect(frame)
            
            # Update tracker (VehicleTracker takes raw detections list directly)
            # Detections format: [{'bbox': [x1,y1,x2,y2], 'class_name': 'car', 'confidence': 0.8}, ...]
            tracked_objects = self.tracker.update(detections, frame_count)
            
            for obj in tracked_objects:
                object_id = obj['id']
                bbox = obj['bbox']
                cls_name = obj['class_name']
                
                # Check Red Light Violation using REAL ID
                if self.red_light.check_violation(object_id, bbox, signal_state):
                     # Construct a detection dict for the logger
                     det_for_log = {'bbox': bbox, 'class_name': cls_name, 'confidence': obj.get('confidence', 0.0)}
                     self._log_violation(frame, det_for_log, "Red Light Violation", signal_state=signal_state)
                     violations_count += 1
                     continue
            
            # Fallback for detections that weren't tracked (optional, usually skipped)
            
            # Optimization: Skip frames?
            # if frame_count % 2 != 0: continue
            
        cap.release()
        return {"frames_processed": frame_count, "violations_detected": violations_count}

    def _log_violation(self, frame, detection, violation_type, **kwargs):
        """
        Save violation to DB and disk.
        """
        # Save image
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:6]
        filename = f"vio_{timestamp_str}_{unique_id}.jpg"
        save_path = os.path.join(self.config['VIOLATIONS_FOLDER'], filename)
        
        # Draw bounding box for context
        x1, y1, x2, y2 = detection['bbox']
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(frame, violation_type, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)
        
        save_frame(frame, save_path)
        
        # Extract Plate (best effort)
        vehicle_crop = frame[y1:y2, x1:x2]
        plate_text = self.anpr.extract_text(vehicle_crop)
        
        # Generate Video Clip
        video_clip_path = None
        source_video_path = kwargs.get('source_video_path')
        video_fps = kwargs.get('video_fps', 30.0)
        frame_number = kwargs.get('frame_number', 0)
        
        if source_video_path and os.path.exists(source_video_path):
            violation_time = frame_number / video_fps if video_fps > 0 else 0
            # Define output filename for clip
            clip_filename = f"clip_{timestamp_str}_{unique_id}.mp4"
            clip_full_path = os.path.join(self.config['VIOLATIONS_FOLDER'], clip_filename)
            
            # Extract 5s clip (2.5s before, 2.5s after)
            try:
                # We need to import here to avoid circular dependencies if utils imports models
                from app.utils.video_clip import extract_clip
                generated_clip = extract_clip(
                    source_video_path, 
                    self.config['VIOLATIONS_FOLDER'], 
                    violation_time, 
                    duration=5.0
                )
                if generated_clip:
                    video_clip_path = f"violations/{generated_clip}"
            except Exception as e:
                print(f"Failed to generate clip: {e}")

        # Save to DB
        violation = Violation(
            violation_type=violation_type,
            vehicle_type=detection['class_name'],
            license_plate=plate_text,
            image_path=f"violations/{filename}",
            location="Camera 01", # Placeholder
            signal_state=kwargs.get('signal_state'),
            video_path=video_clip_path, # Save the CLIP path, not the full video
            frame_number=frame_number,
            video_fps=video_fps
        )
        db.session.add(violation)
        db.session.commit()
```

### File: `app/ai/video_annotator.py`
```python
"""
Video Annotator - Creates annotated video with all AI detections visualized.

This module processes a video and overlays:
- Vehicle detection bounding boxes
- Traffic light detection and state
- Stop lines and ROI zones
- Speed measurements
- Lane boundaries
- Violation highlights

The output is a video that shows exactly what the AI "sees".
"""
import cv2
import numpy as np
from app.ai.detector import VehicleDetector
from app.ai.red_light import RedLightSystem
from app.ai.speed import SpeedSystem
from app.ai.lane import LaneSystem
from app.ai.anpr import ANPR_System


class VideoAnnotator:
    """Annotates video with AI detections for visualization."""
    
    def __init__(self, config=None):
        """Initialize annotator with AI systems."""
        self.detector = VehicleDetector()
        self.red_light = RedLightSystem()
        self.speed = SpeedSystem()
        self.lane = LaneSystem()
        self.anpr = ANPR_System()
        
        # Colors (BGR)
        self.COLORS = {
            'vehicle': (0, 255, 0),      # Green
            'violation': (0, 0, 255),    # Red
            'traffic_light': (255, 255, 0),  # Cyan
            'stop_line': (0, 0, 255),    # Red
            'speed_zone': (0, 255, 0),   # Green
            'lane': (255, 255, 0),       # Yellow
            'text': (255, 255, 255)      # White
        }
        
    def annotate_video(self, input_path, output_path, roi_config=None, frame_skip=1):
        """
        Process video and create annotated version.
        
        Args:
            input_path: Path to input video
            output_path: Path to save annotated video
            roi_config: ROI configuration object (optional)
            frame_skip: Process every Nth frame (for speed)
        
        Returns:
            dict: Processing statistics
        """
        cap = cv2.VideoCapture(input_path)
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Load ROI config if provided
        if roi_config and hasattr(roi_config, 'stop_lines'):
            if roi_config.stop_lines:
                self.red_light.set_stop_line(roi_config.stop_lines[0].points)
        
        frame_idx = 0
        violations = []
        
        print(f"📹 Annotating video: {total_frames} frames at {fps} FPS")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Skip frames if needed
            if frame_idx % frame_skip != 0:
                out.write(frame)
                frame_idx += 1
                continue
            
            # Create annotated frame
            annotated_frame = frame.copy()
            
            # 1. Draw ROI zones first (background layer)
            annotated_frame = self._draw_roi_zones(annotated_frame, roi_config)
            
            # 2. Detect and draw traffic light
            traffic_light_bbox = self.red_light.detect_traffic_light_with_yolo(frame, self.detector)
            signal_state = 'unknown'
            
            if traffic_light_bbox:
                signal_state = self.red_light.detect_signal_state(frame, traffic_light_bbox)
                annotated_frame = self._draw_traffic_light(annotated_frame, traffic_light_bbox, signal_state)
            
            # 3. Detect vehicles
            detections = self.detector.detect(frame)
            
            # 4. Process each vehicle
            for det in detections:
                bbox = [int(det['x1']), int(det['y1']), int(det['x2']), int(det['y2'])]
                cls = det['class']
                conf = det['confidence']
                
                # Check for violations
                is_violation = self.red_light.check_violation(bbox, signal_state)
                
                # Draw vehicle box
                color = self.COLORS['violation'] if is_violation else self.COLORS['vehicle']
                annotated_frame = self._draw_vehicle(annotated_frame, bbox, cls, conf, is_violation)
                
                if is_violation:
                    violations.append({
                        'frame': frame_idx,
                        'type': 'red_light',
                        'bbox': bbox
                    })
            
            # 5. Add info overlay
            annotated_frame = self._draw_info_overlay(
                annotated_frame, frame_idx, total_frames, signal_state, len(detections)
            )
            
            # Write annotated frame
            out.write(annotated_frame)
            
            frame_idx += 1
            
            # Progress
            if frame_idx % 100 == 0:
                progress = (frame_idx / total_frames) * 100
                print(f"   Progress: {progress:.1f}% ({frame_idx}/{total_frames})")
        
        cap.release()
        out.release()
        
        print(f"✅ Annotated video saved: {output_path}")
        print(f"   Total violations detected: {len(violations)}")
        
        # Convert to H.264 for web playback availability
        try:
            import subprocess
            import os
            
            temp_output = output_path.replace('.mp4', '_temp.mp4')
            os.rename(output_path, temp_output)
            
            # Use ffmpeg to convert to H.264 (avc1)
            # -movflags faststart moves metadata to front for faster web playback
            cmd = [
                'ffmpeg', '-y',
                '-i', temp_output,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23', 
                '-c:a', 'aac',
                '-movflags', 'faststart',
                output_path
            ]
            
            print("🔄 Converting processed video to H.264 for web playback...")
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Clean up temp file
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                os.remove(temp_output)
                print("✅ Conversion complete.")
            else:
                # Restore if failed
                os.rename(temp_output, output_path)
                print("⚠️ Conversion failed, restored original.")
                
        except Exception as e:
            print(f"⚠️ Could not convert video to H.264: {e}")
            if os.path.exists(temp_output):
                os.rename(temp_output, output_path)
        
        return {
            'frames_processed': frame_idx,
            'violations_detected': len(violations),
            'output_path': output_path
        }
    
    def _draw_roi_zones(self, frame, roi_config):
        """Draw ROI zones (stop line, speed zones, lanes)."""
        if not roi_config:
            return frame
        
        # Draw stop line
        if hasattr(roi_config, 'stop_lines') and roi_config.stop_lines:
            for stop_line in roi_config.stop_lines:
                pt1 = tuple(stop_line.points[0])
                pt2 = tuple(stop_line.points[1])
                cv2.line(frame, pt1, pt2, self.COLORS['stop_line'], 3)
                cv2.putText(frame, "STOP LINE", 
                           (pt1[0], pt1[1] - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
                           self.COLORS['stop_line'], 2)
        
        # Draw speed zones
        if hasattr(roi_config, 'speed_zones') and roi_config.speed_zones:
            for zone in roi_config.speed_zones:
                entry_pt1 = tuple(zone.entry_line[0])
                entry_pt2 = tuple(zone.entry_line[1])
                exit_pt1 = tuple(zone.exit_line[0])
                exit_pt2 = tuple(zone.exit_line[1])
                
                cv2.line(frame, entry_pt1, entry_pt2, self.COLORS['speed_zone'], 2)
                cv2.line(frame, exit_pt1, exit_pt2, self.COLORS['speed_zone'], 2)
        
        # Draw lane boundaries
        if hasattr(roi_config, 'lane_boundaries') and roi_config.lane_boundaries:
            for lane in roi_config.lane_boundaries:
                left_pt1 = tuple(lane.left_boundary[0])
                left_pt2 = tuple(lane.left_boundary[1])
                right_pt1 = tuple(lane.right_boundary[0])
                right_pt2 = tuple(lane.right_boundary[1])
                
                cv2.line(frame, left_pt1, left_pt2, self.COLORS['lane'], 1)
                cv2.line(frame, right_pt1, right_pt2, self.COLORS['lane'], 1)
        
        return frame
    
    def _draw_traffic_light(self, frame, bbox, state):
        """Draw traffic light detection box and state."""
        x1, y1, x2, y2 = bbox
        
        # Determine color based on state
        if state == 'red':
            color = (0, 0, 255)  # Red
        elif state == 'green':
            color = (0, 255, 0)  # Green
        elif state == 'yellow':
            color = (0, 255, 255)  # Yellow
        else:
            color = (128, 128, 128)  # Gray for unknown
        
        # Draw box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
        
        # Draw state label
        label = f"Signal: {state.upper()}"
        cv2.putText(frame, label, (x1, y1 - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        return frame
    
    def _draw_vehicle(self, frame, bbox, cls, conf, is_violation):
        """Draw vehicle detection box with label."""
        x1, y1, x2, y2 = bbox
        color = self.COLORS['violation'] if is_violation else self.COLORS['vehicle']
        
        # Draw bounding box
        thickness = 3 if is_violation else 2
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
        
        # Create label
        label = f"{cls} {conf:.2f}"
        if is_violation:
            label = f"⚠️ VIOLATION - {label}"
        
        # Draw label background
        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x1, y1 - label_h - 10), (x1 + label_w, y1), color, -1)
        
        # Draw label text
        cv2.putText(frame, label, (x1, y1 - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def _draw_info_overlay(self, frame, current_frame, total_frames, signal_state, vehicles_count):
        """Draw information overlay at top of frame."""
        # Semi-transparent black background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], 80), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
        
        # Frame info
        frame_text = f"Frame: {current_frame}/{total_frames}"
        cv2.putText(frame, frame_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.COLORS['text'], 2)
        
        # Signal state
        signal_text = f"Signal: {signal_state.upper()}"
        signal_color = (0, 0, 255) if signal_state == 'red' else (0, 255, 0)
        cv2.putText(frame, signal_text, (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, signal_color, 2)
        
        # Vehicles count
        vehicles_text = f"Vehicles: {vehicles_count}"
        cv2.putText(frame, vehicles_text, (250, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.COLORS['text'], 2)
        
        # System info
        system_text = "TrafficAI - Real-time Detection"
        cv2.putText(frame, system_text, (frame.shape[1] - 400, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 200, 255), 2)
        
        return frame
```

### File: `app/routes/violations.py`
```python
from app.models import Violation
from sqlalchemy import desc
from app.routes import violations_bp
from flask import jsonify, render_template, current_app
import os

@violations_bp.route('/api/violations', methods=['GET'])
def get_violations():
    violations = Violation.query.order_by(desc(Violation.timestamp)).all()
    return jsonify({'violations': [v.to_dict() for v in violations]}), 200

@violations_bp.route('/violation/<int:violation_id>')
def violation_detail(violation_id):
    violation = Violation.query.get_or_404(violation_id)
    
    # Check if video file actually exists and is valid
    if violation.video_path:
        video_full_path = os.path.join(current_app.root_path, 'static', violation.video_path)
        if not os.path.exists(video_full_path) or os.path.getsize(video_full_path) < 1000:
            # If video file is missing or too small (corrupt), fallback to image
            violation.video_path = None
            
    return render_template('violation_detail.html', violation=violation)
```

### File: `app/routes/admin.py`
```python
from flask import Blueprint, render_template, request, current_app, abort
from app import db
from sqlalchemy import inspect, text

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
def admin_dashboard():
    """Admin dashboard showing list of tables and selected table data."""
    # Get all tables
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    selected_table = request.args.get('table')
    table_data = []
    columns = []
    
    if selected_table:
        if selected_table not in tables:
            abort(404)
            
        # Get columns
        columns_info = inspector.get_columns(selected_table)
        columns = [c['name'] for c in columns_info]
        
        # Get data (raw SQL for flexibility with any table)
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text(f"SELECT * FROM {selected_table} LIMIT 100"))
                table_data = [dict(row._mapping) for row in result]
        except Exception as e:
            current_app.logger.error(f"Error fetching table data: {e}")
            
    return render_template('admin.html', 
                          tables=tables, 
                          selected_table=selected_table,
                          columns=columns,
                          data=table_data)

@admin_bp.route('/admin/add', methods=['POST'])
def add_record():
    """Add a new record to a specific table."""
    table_name = request.form.get('table_name')
    if not table_name:
        return {'status': 'error', 'message': 'No table name provided'}, 400
    
    try:
        from app import models
        # Map table names to model classes
        model_map = {
            'owners': models.Owner,
            'vehicles': models.Vehicle,
            'traffic_officers': models.TrafficOfficer,
            'cameras': models.Camera,
            'violations': models.Violation
        }
        
        model_class = model_map.get(table_name)
        if not model_class:
            return {'status': 'error', 'message': f'No model found for table {table_name}'}, 400
        
        # Build object from form data
        data = {}
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns(table_name) if c['name'] != 'id' and c['name'] != 'created_at']
        
        for col in columns:
            val = request.form.get(col)
            if val:
                data[col] = val
                
        new_record = model_class(**data)
        db.session.add(new_record)
        db.session.commit()
        
        return {'status': 'success', 'message': f'Record added to {table_name}!'}
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding record to {table_name}: {e}")
        return {'status': 'error', 'message': str(e)}, 500

import os
import glob
import shutil

@admin_bp.route('/admin/reset', methods=['POST'])
def reset_db():
    """Clear all data from the database and delete generated files."""
    try:
        from app.models import Violation
        
        # 1. Clear Database
        num_deleted = db.session.query(Violation).delete()
        db.session.commit()
        
        # 2. Clear Files (Processed Videos & Evidence)
        cleaned_files = 0
        folders_to_clear = ['processed', 'violations']
        
        for folder in folders_to_clear:
            folder_path = os.path.join(current_app.static_folder, folder)
            if os.path.exists(folder_path):
                # Delete all files in the folder (keep the folder itself)
                files = glob.glob(os.path.join(folder_path, '*'))
                for f in files:
                    try:
                        if os.path.isfile(f):
                            os.remove(f)
                            cleaned_files += 1
                    except Exception as e:
                        current_app.logger.error(f"Error deleting file {f}: {e}")
            
        current_app.logger.info(f"System reset: {num_deleted} DB records, {cleaned_files} files removed.")
        return {'status': 'success', 'message': f'System Reset Complete! {num_deleted} records and {cleaned_files} files removed.'}
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error resetting database: {e}")
        return {'status': 'error', 'message': str(e)}, 500
```

### File: `requirements.txt`
```text
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
python-dotenv==1.0.0
opencv-python-headless==4.8.1.78
ultralytics==8.0.200
torch
numpy==1.26.0

paddlepaddle
paddleocr>=2.7.0
easyocr>=1.7.0
Pillow==10.1.0
pytest==7.4.3
pytest-cov

flask-socketio

simple-websocket

eventlet>=0.33.0

ultralytics>=8.3.0
moviepy>=1.0.3
```

---

## PART 3: DIRECTIVE FOR ORCHESTRATOR

**Attention: Senior AI Orchestrator**

You have received this Escalation Handoff Report. A local agent has failed to solve this problem to the user's complete satisfaction, specifically regarding portability and "fresh perspective".

**Your Directive:**
1.  **Analyze the Failure:** The previous agent relied on a hybrid `moviepy` / `subprocess(ffmpeg)` approach. Portability is compromised if `moviepy` fails to install its own binary and system `ffmpeg` is missing. The user specifically asked for a robust solution that works on other machines ("proper installation and what not").
2.  **Verify Codec Strategy:** Ensure the H.264 conversion logic in `video_annotator.py` is solid and consistent. The current implementation relies on `subprocess`, which again assumes system `ffmpeg`.
3.  **Formulate a New Plan:**
    -   Consider if using `imageio-ffmpeg` directly (or a similar standalone binary wrapper) is more robust for portability than hoping a system install exists.
    -   Address the "Restart Required" friction. Is there a way to hot-reload or make the user experience better?
    -   Verify the history sync logic in `admin.py`.
4.  **Execute:** Provide the final, polished solution that guarantees video playback across browsers and machines.

**Begin your analysis now.**
