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
