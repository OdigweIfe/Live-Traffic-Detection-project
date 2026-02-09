"""
WebSocket Event Handlers for Real-Time Video Processing with Vehicle Tracking.

Handles:
- Client connections
- Video processing requests
- Frame streaming
- Progress updates
- Violation notifications
- Vehicle tracking across frames
- Video recording to disk
- ANPR (License Plate Recognition)
- Speed Estimation
"""
from flask import request, current_app
from flask_socketio import emit, join_room
from app import socketio, db
from app.models import Violation
import cv2
import base64
import os
import threading
import json
import numpy as np
from datetime import datetime
import hashlib

# Global dictionary to track active processing sessions
# Key: video_path, Value: { 'room_id': str, 'stop': bool, 'progress': int }
active_video_sessions = {}
processing_sessions = {}  # Legacy: Keep for sid tracking if needed, but primarily use active_video_sessions



@socketio.on('connect')
def handle_connect():
    """Client connected to WebSocket."""
    print(f'✅ Client connected: {request.sid}')
    emit('connection_response', {'status': 'connected', 'sid': request.sid})


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected."""
    print(f'❌ Client disconnected: {request.sid}')
    if request.sid in processing_sessions:
        processing_sessions[request.sid]['stop'] = True


@socketio.on('start_processing')
def handle_start_processing(data):
    """Start processing a video with real-time frame streaming."""
    from urllib.parse import unquote
    
    sid = request.sid
    video_path = data.get('video_path')
    roi_config_path = data.get('roi_config_path')
    
    # URL decode the path
    if video_path:
        video_path = unquote(video_path)
    
    print(f"📹 Processing request for video: {video_path}")
    
    if not video_path or not os.path.exists(video_path):
        error_msg = f'Video file not found: {video_path}'
        print(f"❌ {error_msg}")
        emit('error', {'message': error_msg})
        return

    # Create a consistent room ID for this video
    room_id = hashlib.md5(video_path.encode()).hexdigest()
    join_room(room_id)
    print(f"🔗 Client {sid} joined room {room_id}")
    
    # Check if already processing this video
    if video_path in active_video_sessions:
        existing = active_video_sessions[video_path]
        if not existing.get('stop', False):
            print(f"🔄 Resuming existing session for {video_path}")
            emit('resume_session', {
                'message': 'Resuming existing session',
                'progress': existing.get('progress', 0)
            })
            return

    # Initialize new session
    active_video_sessions[video_path] = {
        'room_id': room_id,
        'stop': False,
        'progress': 0
    }
    
    # Get current app to pass to thread
    app = current_app._get_current_object()
    
    # Start processing in background thread
    thread = threading.Thread(
        target=process_video_stream,
        args=(app, room_id, video_path, roi_config_path)
    )
    thread.daemon = True
    thread.start()
    
    print(f"✅ Processing thread started for room {room_id}")
    emit('processing_started', {'message': 'Video processing started'})


def process_video_stream(app, room_id, video_path, roi_config_path=None):
    """Process video and stream frames with vehicle tracking."""
    print(f"🎬 Starting video processing thread for room {room_id}")
    
    with app.app_context():
        try:
            # Load ROI config
            roi_config = None
            if roi_config_path and os.path.exists(roi_config_path):
                with open(roi_config_path, 'r') as f:
                    roi_config = json.load(f)
            
            # Open video
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            print(f"✅ Video: {width}x{height}, {total_frames} frames, {fps:.1f} FPS")
            
            # Initialize Video Writer
            processed_filename = f"processed_{os.path.basename(video_path)}"
            processed_path = os.path.join(app.static_folder, 'processed', processed_filename)
            os.makedirs(os.path.dirname(processed_path), exist_ok=True)
            
            # Use mp4v codec (native Windows, no external library needed)
            # Use avc1 (H.264) for better browser compatibility
            try:
                fourcc = cv2.VideoWriter_fourcc(*'avc1')
            except:
                print("⚠️ avc1 codec not found, falling back to mp4v")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                
            out = cv2.VideoWriter(processed_path, fourcc, fps, (width, height))
            print(f"📼 Recording processed video to: {processed_filename}")
            
            # Initialize AI systems
            from app.ai.detector import VehicleDetector
            from app.ai.red_light import RedLightSystem
            from app.ai.vehicle_tracker import VehicleTracker
            from app.ai.anpr import ANPR_System
            
            detector = VehicleDetector()
            red_light = RedLightSystem()
            tracker = VehicleTracker(iou_threshold=0.3, max_missing_frames=10)
            anpr = ANPR_System()  # Uses PaddleOCR by default, falls back to EasyOCR
            
            print(f"✅ AI systems ready (detector, red_light, tracker, anpr)")
            
            # Set stop line from ROI config
            if roi_config and 'stop_lines' in roi_config and roi_config['stop_lines']:
                red_light.set_stop_line(roi_config['stop_lines'][0]['points'])
            
            # Send video info to client
            socketio.emit('video_info', {
                'fps': fps,
                'total_frames': total_frames,
                'width': width,
                'height': height,
                'duration': total_frames / fps if fps > 0 else 0
            }, room=room_id)
            
            frame_idx = 0
            pending_violations = {}  # Queue for deferred violation saving
            plate_cache = {}  # PRE-VIOLATION CAPTURE: Store plates captured before violation
            
            # Helper: Check if vehicle is in detection zone (before stop line)
            def is_in_detection_zone(bbox, stop_line_y):
                """Vehicle is approaching stop line = good time to capture plate."""
                if stop_line_y is None:
                    return False
                # Get vehicle center
                center_y = (bbox[1] + bbox[3]) // 2
                # Detection zone: Expand to 300px before stop line for more chances
                return (stop_line_y - 300) < center_y < (stop_line_y - 10)
            
            # Get stop line Y coordinate for detection zone
            stop_line_y = None
            if roi_config and 'stop_lines' in roi_config and roi_config['stop_lines']:
                points = roi_config['stop_lines'][0].get('points', [])
                if points:
                    stop_line_y = points[0][1]  # Y coordinate of first stop line point

            # Helper: Process Violation Event
            def process_violation_event(vehicle_id, violation_type, bbox, signal_state, cls_name):
                """Handle violation: ANPR, Snapshot, DB Queue."""
                if tracker.mark_violation(vehicle_id, violation_type):
                    print(f"🚨 VIOLATION DETECTED: {violation_type} | Vehicle {vehicle_id}")
                    
                    # copy frame for snapshot
                    snapshot_frame = frame.copy()
                    
                    # ========= USE PRE-CAPTURED PLATE OR SCAN NOW =========
                    # First check if we have a pre-captured plate
                    plate_text = f"ID-{vehicle_id}"  # Default
                    if vehicle_id in plate_cache:
                        plate_text = plate_cache[vehicle_id]['plate_text']
                        print(f"📋 Using PRE-CAPTURED plate: {plate_text}")
                    else:
                        # Fallback: try to scan now
                        x1, y1, x2, y2 = bbox
                        h_f, w_f = frame.shape[:2]
                        x1, y1 = max(0, x1), max(0, y1)
                        x2, y2 = min(w_f, x2), min(h_f, y2)
                        
                        if x2 > x1 and y2 > y1:
                            vehicle_crop = frame[y1:y2, x1:x2]
                            try:
                                # Standard ANPR logic
                                detected_text = anpr.extract_text(vehicle_crop)
                                if detected_text and len(detected_text) >= 3 and detected_text != "N/A":
                                    plate_text = detected_text
                                    tracker.update_license_plate(vehicle_id, plate_text)
                            except Exception as e:
                                print(f"❌ ANPR Error: {e}")

                    # Save violation snapshot image
                    snapshot_filename = f"violation_{vehicle_id}_{int(frame_idx)}.jpg"
                    snapshot_dir = os.path.join(current_app.static_folder, 'violations')
                    os.makedirs(snapshot_dir, exist_ok=True)
                    snapshot_path = os.path.join(snapshot_dir, snapshot_filename)
                    
                    # Draw bounding box on snapshot
                    cv2.rectangle(snapshot_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 255), 3)
                    cv2.putText(snapshot_frame, f"{violation_type}: {plate_text}", 
                               (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.imwrite(snapshot_path, snapshot_frame)
                    
                    # Queue violation for deferred save
                    pending_violations[vehicle_id] = {
                        'detected_frame': frame_idx,
                        'vehicle_type': cls_name,
                        'plate_text': plate_text,
                        'signal_state': signal_state,
                        'violation_type': violation_type, # Store specific type
                        'bbox': bbox,
                        'image_path': f"violations/{snapshot_filename}",
                        'video_path': f"processed/{processed_filename}",
                        'video_fps': fps
                    }
                    return True
                return False
            
            while cap.isOpened():
                if video_path in active_video_sessions and active_video_sessions[video_path].get('stop', False):
                    break
                
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Create annotated frame
                annotated_frame = frame.copy()
                
                # Draw ROI zones
                if roi_config:
                    annotated_frame = draw_roi_zones(annotated_frame, roi_config)
                
                # Detect traffic light
                traffic_light_bbox = red_light.detect_traffic_light_with_yolo(frame, detector)
                signal_state = 'unknown'
                
                if traffic_light_bbox:
                    signal_state = red_light.detect_signal_state(frame, traffic_light_bbox)
                    annotated_frame = draw_traffic_light(annotated_frame, traffic_light_bbox, signal_state)
                
                # Detect vehicles
                detections = detector.detect(frame)
                
                # Update tracker with detections
                tracked_vehicles = tracker.update(detections, frame_idx)
                
                # Process each tracked vehicle
                for vehicle in tracked_vehicles:
                    bbox = vehicle['bbox']
                    cls = vehicle['class_name']
                    conf = vehicle['confidence']
                    vehicle_id = vehicle['id']
                    
                    SPEED_LIMIT = current_app.config['SPEED_LIMIT']
                    PIXELS_PER_METER = current_app.config['PIXELS_PER_METER']
                    
                    # Calculate Speed
                    speed_kmh = tracker.calculate_speed(vehicle_id, fps=fps, ppm=PIXELS_PER_METER)
                    
                    # Check for Red Light Violation
                    if red_light.check_violation(vehicle_id, bbox, signal_state):
                        process_violation_event(vehicle_id, 'Red Light Violation', bbox, signal_state, cls)
                    
                    # Check for Speeding Violation
                    if speed_kmh > SPEED_LIMIT:
                        process_violation_event(vehicle_id, 'Speeding Violation', bbox, signal_state, cls)
                    
                    # Process pending violations after 5 frames (for accurate speed)
                    for vid in list(pending_violations.keys()):
                        pending = pending_violations[vid]
                        frames_since_detection = frame_idx - pending['detected_frame']
                        
                        if frames_since_detection >= 5:
                            # Now get speed with accumulated tracking data
                            final_speed = tracker.calculate_speed(vid, fps=fps, ppm=PIXELS_PER_METER)
                            tracked_plate = tracker.tracked_vehicles.get(vid, {}).get('license_plate')
                            final_plate = tracked_plate if tracked_plate else pending['plate_text']
                            
                            # Save to Database
                            # Save to Database ONLY if final confirmed speed is still valid (or if it's not a speed violation)
                            # This prevents "Ghost Violations" where a momentary glitch triggers it but the smoothed speed is lower
                            is_valid_violation = True
                            if pending['violation_type'] == 'Speeding Violation' and final_speed <= SPEED_LIMIT:
                                print(f"⚠️ Discarding Speed Violation for {final_plate}: Initial > {SPEED_LIMIT}, but Final {final_speed:.1f} <= {SPEED_LIMIT}")
                                is_valid_violation = False
                            
                            if is_valid_violation:
                                try:
                                    violation = Violation(
                                        timestamp=datetime.utcnow(),
                                        violation_type=pending.get('violation_type', 'Red Light Violation'), # Use specific type or default
                                        vehicle_type=pending['vehicle_type'],
                                        license_plate=final_plate,
                                        speed_kmh=round(final_speed, 1),
                                        location='Main Intersection',
                                        signal_state=pending['signal_state'],
                                        image_path=pending.get('image_path', f"violations/violation_{vid}.jpg"),
                                        frame_number=pending['detected_frame'],
                                        video_fps=pending.get('video_fps'),
                                        video_path=pending.get('video_path')
                                    )
                                    db.session.add(violation)
                                    db.session.commit()
                                    print(f"💾 Saved: {final_plate} @ {final_speed:.1f} km/h")
                                except Exception as e:
                                    db.session.rollback()
                                    print(f"❌ Database error: {e}")
                            
                            del pending_violations[vid]
                    
                    # Get current info (plate might have been updated by ANPR)
                    current_plate = tracker.tracked_vehicles.get(vehicle_id, {}).get('license_plate')
                    violation_count = tracker.tracked_vehicles.get(vehicle_id, {}).get('violation_count', 0)
                    is_violation = tracker.tracked_vehicles.get(vehicle_id, {}).get('has_violated', False)
                    
                    # Draw vehicle
                    annotated_frame = draw_vehicle(
                        annotated_frame, bbox, cls, conf, 
                        is_violation, violation_count, speed_kmh, current_plate
                    )
                
                # Get tracking stats
                stats = tracker.get_stats()
                
                # Add info overlay
                annotated_frame = draw_info_overlay(
                    annotated_frame, frame_idx, total_frames, signal_state, 
                    len(tracked_vehicles), stats
                )
                
                # Write frame to video file (RECORDING)
                out.write(annotated_frame)
                
                # Encode frame to base64
                _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # Calculate progress
                progress = int(((frame_idx + 1) / total_frames) * 100) if total_frames > 0 else 0
                
                # Send frame to client
                socketio.emit('frame', {
                    'frame_index': frame_idx,
                    'image': frame_base64,
                    'signal_state': signal_state,
                    'vehicles_count': len(tracked_vehicles),
                    'unique_vehicles': stats['total_unique_vehicles'],
                    'total_violations': stats['total_violations'],
                    'progress': progress
                }, room=room_id)
                
                # Update progress in session
                if video_path in active_video_sessions:
                    active_video_sessions[video_path]['progress'] = progress
                
                frame_idx += 1
                
                # No skipping frames if we want smooth recording
            
            final_stats = tracker.get_stats()
            
            # Flush any remaining pending violations
            for vid in list(pending_violations.keys()):
                pending = pending_violations[vid]
                final_speed = tracker.calculate_speed(vid, fps=fps, ppm=40.0)
                tracked_plate = tracker.tracked_vehicles.get(vid, {}).get('license_plate')
                final_plate = tracked_plate if tracked_plate else pending['plate_text']
                
                try:
                    violation = Violation(
                        timestamp=datetime.utcnow(),
                        violation_type=pending.get('violation_type', 'Red Light Violation'),
                        vehicle_type=pending['vehicle_type'],
                        license_plate=final_plate,
                        speed_kmh=round(final_speed, 1),
                        location='Main Intersection',
                        signal_state=pending['signal_state'],
                        image_path=pending.get('image_path', f"violations/violation_{vid}.jpg"),
                        frame_number=pending['detected_frame'],
                        video_fps=pending.get('video_fps'),
                        video_path=pending.get('video_path')
                    )
                    db.session.add(violation)
                    db.session.commit()
                    print(f"💾 Saved (flush): {final_plate} @ {final_speed:.1f} km/h")
                except Exception as e:
                    db.session.rollback()
                    print(f"❌ Database error: {e}")
            
            cap.release()
            out.release()
            
            # Save stats to JSON sidecar
            json_filename = f"{processed_filename}.json"
            json_path = os.path.join(app.static_folder, 'processed', json_filename)
            
            stats_data = {
                'filename': processed_filename,
                'stats': {
                    'unique_vehicles': final_stats['total_unique_vehicles'],
                    'total_violations': final_stats['total_violations'],
                    'duration': f"{int(total_frames / fps // 60)}:{int(total_frames / fps % 60):02d}" if fps > 0 else "0:00",
                    'processed_at': datetime.utcnow().isoformat()
                }
            }
            
            try:
                with open(json_path, 'w') as f:
                    json.dump(stats_data, f, indent=4)
                print(f"📊 Stats saved to: {json_filename}")
            except Exception as e:
                print(f"❌ Error saving stats JSON: {e}")
            
            print(f"✅ Video saved to: {processed_path}")
            
            # Send completion message
            socketio.emit('processing_complete', {
                'frames_processed': frame_idx,
                'violations_detected': final_stats['total_violations'],
                'unique_vehicles': final_stats['total_unique_vehicles'],
                'processed_video': processed_filename,
                'message': 'Video processing complete!'
            }, room=room_id)
            
            print(f"✅ Processing complete: {final_stats['total_unique_vehicles']} vehicles, {final_stats['total_violations']} violations")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            socketio.emit('error', {'message': str(e)}, room=room_id)
        finally:
            if video_path in active_video_sessions:
                del active_video_sessions[video_path]


def draw_roi_zones(frame, roi_config):
    """Draw ROI zones on frame."""
    if roi_config and 'stop_lines' in roi_config and roi_config['stop_lines']:
        for stop_line in roi_config['stop_lines']:
            pt1 = tuple(stop_line['points'][0])
            pt2 = tuple(stop_line['points'][1])
            cv2.line(frame, pt1, pt2, (0, 0, 255), 3)
    return frame


def draw_traffic_light(frame, bbox, state):
    """Draw traffic light detection."""
    x1, y1, x2, y2 = bbox
    color = (0, 0, 255) if state == 'red' else (0, 255, 0) if state == 'green' else (128, 128, 128)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
    cv2.putText(frame, f"Signal: {state.upper()}", (x1, y1 - 10), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    return frame


def draw_vehicle(frame, bbox, cls, conf, is_violation, violation_count=0, speed_kmh=0.0, plate=None):
    """Draw vehicle bounding box with violation count and speed."""
    x1, y1, x2, y2 = bbox
    color = (0, 0, 255) if is_violation else (0, 255, 0)
    thickness = 3 if is_violation else 2
    
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
    
    # Create label
    display_id = plate if plate else cls
    label = f"{display_id} {speed_kmh:.0f}km/h"
    
    if violation_count > 0:
        label = f"[!] {violation_count}x - {label}"
    elif is_violation:
        label = f"[!] {label}"
    
    cv2.putText(frame, label, (x1, y1 - 5), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return frame


def draw_info_overlay(frame, current_frame, total_frames, signal_state, vehicles_count, stats):
    """Draw information overlay with tracking stats."""
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (frame.shape[1], 110), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
    
    # Frame info
    cv2.putText(frame, f"Frame: {current_frame}/{total_frames}", (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Signal state
    signal_color = (0, 0, 255) if signal_state == 'red' else (0, 255, 0)
    cv2.putText(frame, f"Signal: {signal_state.upper()}", (10, 60), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, signal_color, 2)
    
    # Active vehicles
    cv2.putText(frame, f"Active: {vehicles_count}", (250, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Unique vehicles (cyan)
    cv2.putText(frame, f"Unique: {stats['total_unique_vehicles']}", (250, 60), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 100), 2)
    
    # Total violations (red)
    cv2.putText(frame, f"Violations: {stats['total_violations']}", (250, 90), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    return frame
