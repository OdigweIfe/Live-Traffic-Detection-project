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
        filename = f"vio_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.jpg"
        save_path = os.path.join(self.config['VIOLATIONS_FOLDER'], filename)
        
        # Draw bounding box for context
        x1, y1, x2, y2 = detection['bbox']
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(frame, violation_type, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)
        
        save_frame(frame, save_path)
        
        # Extract Plate (best effort)
        vehicle_crop = frame[y1:y2, x1:x2]
        plate_text = self.anpr.extract_text(vehicle_crop)
        
        # Save to DB
        violation = Violation(
            violation_type=violation_type,
            vehicle_type=detection['class_name'],
            license_plate=plate_text,
            image_path=f"violations/{filename}",
            location="Camera 01", # Placeholder
            signal_state=kwargs.get('signal_state')
        )
        db.session.add(violation)
        db.session.commit()
