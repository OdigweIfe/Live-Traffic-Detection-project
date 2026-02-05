import cv2
import numpy as np

class RedLightSystem:
    def __init__(self):
        """
        Initialize Red Light Detection System with automatic traffic light detection.
        No manual ROI configuration needed - uses YOLO to find traffic lights.
        """
        self.stop_line_y = None  # Will be set from ROI config if available
        self.traffic_light_roi = None
        self.last_detected_signal_bbox = None  # Cache for performance
        
        # Track vehicle positions relative to stop line
        self.vehicle_positions = {}  # vehicle_id -> 'before' or 'after'
        
    def set_stop_line(self, points):
        """Set stop line coordinates (horizontal line assumed)."""
        if points and len(points) >= 2:
            # Average y-coordinate of the two points
            self.stop_line_y = (points[0][1] + points[1][1]) // 2
    
    def detect_traffic_light_with_yolo(self, frame, detector):
        """
        Auto-detect traffic light using YOLO.
        Returns bbox of traffic light: [x1, y1, x2, y2] or None
        """
        # Run YOLO detection
        results = detector.model(frame, verbose=False)
        
        # YOLO class ID for traffic light is 9
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                
                # Traffic light class (9) with good confidence
                if cls == 9 and conf > 0.3:
                    # Get bbox coordinates
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    self.last_detected_signal_bbox = [x1, y1, x2, y2]
                    return [x1, y1, x2, y2]
        
        # Return cached bbox if no new detection (signal might be occluded)
        return self.last_detected_signal_bbox
    
    def detect_signal_state(self, frame, traffic_light_bbox=None):
        """
        Detect traffic signal state (red/green/yellow/unknown).
        
        Args:
            frame: Input frame
            traffic_light_bbox: [x1, y1, x2, y2] bounding box of traffic light
                               If None, will search entire frame (less accurate)
        
        Returns:
            str: 'red', 'green', 'yellow', or 'unknown'
        """
        # If bbox provided, crop to traffic light region
        if traffic_light_bbox:
            x1, y1, x2, y2 = traffic_light_bbox
            # Add padding
            padding = 10
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(frame.shape[1], x2 + padding)
            y2 = min(frame.shape[0], y2 + padding)
            
            roi = frame[y1:y2, x1:x2]
        else:
            # Use entire frame (fallback)
            roi = frame
        
        if roi.size == 0:
            return 'unknown'
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Define color ranges in HSV
        # Red (wraps around, so two ranges)
        red_lower1 = np.array([0, 100, 100])
        red_upper1 = np.array([10, 255, 255])
        red_lower2 = np.array([160, 100, 100])
        red_upper2 = np.array([180, 255, 255])
        
        # Yellow
        yellow_lower = np.array([20, 100, 100])
        yellow_upper = np.array([30, 255, 255])
        
        # Green
        green_lower = np.array([40, 50, 50])
        green_upper = np.array([80, 255, 255])
        
        # Create masks
        red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
        red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        
        yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
        green_mask = cv2.inRange(hsv, green_lower, green_upper)
        
        # Count pixels for each color
        red_pixels = cv2.countNonZero(red_mask)
        yellow_pixels = cv2.countNonZero(yellow_mask)
        green_pixels = cv2.countNonZero(green_mask)
        
        # Determine dominant color
        max_pixels = max(red_pixels, yellow_pixels, green_pixels)
        
        # Threshold: at least 50 pixels to be considered
        if max_pixels < 50:
            return 'unknown'
        
        if red_pixels == max_pixels:
            return 'red'
        elif yellow_pixels == max_pixels:
            return 'yellow'
        elif green_pixels == max_pixels:
            return 'green'
        else:
            return 'unknown'
    
    def check_violation(self, vehicle_id, vehicle_bbox, signal_state):
        """
        Check if vehicle CROSSED stop line during red signal.
        Only triggers on transition from before → after, not just presence.
        
        Args:
            vehicle_id: Unique vehicle ID for tracking position history
            vehicle_bbox: [x1, y1, x2, y2] vehicle bounding box
            signal_state: 'red', 'green', 'yellow', 'unknown'
        
        Returns:
            bool: True if violation detected (crossing during red)
        """
        # If no stop line configured, cannot detect violations
        if self.stop_line_y is None:
            return False
        
        # Determine current position relative to stop line
        vehicle_bottom = vehicle_bbox[3]
        current_position = 'after' if vehicle_bottom > self.stop_line_y else 'before'
        
        # Get previous position
        previous_position = self.vehicle_positions.get(vehicle_id, 'before')
        
        # Update position tracker
        self.vehicle_positions[vehicle_id] = current_position
        
        # Violation occurs when:
        # 1. Signal is RED
        # 2. Vehicle crosses from 'before' to 'after' (transition)
        if signal_state == 'red' and previous_position == 'before' and current_position == 'after':
            return True
        
        return False
    
    def get_signal_bbox(self):
        """Get the last detected traffic light bounding box."""
        return self.last_detected_signal_bbox
    
    def cleanup_old_vehicles(self, active_vehicle_ids):
        """Remove position tracking data for vehicles that are no longer tracked."""
        # Remove vehicles that are no longer being tracked
        tracked_ids = set(self.vehicle_positions.keys())
        for vid in tracked_ids:
            if vid not in active_vehicle_ids:
                del self.vehicle_positions[vid]
