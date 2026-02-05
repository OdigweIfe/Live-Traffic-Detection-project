"""
Vehicle Tracker - Tracks unique vehicles across video frames.

Uses Intersection over Union (IoU) to match detections across frames
and assigns unique IDs to each vehicle.
"""
import numpy as np


class VehicleTracker:
    """Tracks vehicles across frames using bounding box matching."""
    
    def __init__(self, iou_threshold=0.3, max_missing_frames=10):
        """
        Initialize vehicle tracker.
        
        Args:
            iou_threshold: Minimum IoU to consider same vehicle
            max_missing_frames: Max frames a vehicle can be missing before removal
        """
        self.next_id = 1
        self.tracked_vehicles = {}  # id -> vehicle data
        self.iou_threshold = iou_threshold
        self.max_missing_frames = max_missing_frames
        
        # Track cumulative violations (for stats)
        self.total_violations_cumulative = 0
        
    def calculate_iou(self, bbox1, bbox2):
        """
        Calculate Intersection over Union between two bboxes.
        
        Args:
            bbox1, bbox2: [x1, y1, x2, y2]
        
        Returns:
            float: IoU score
        """
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # Calculate intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i < x1_i or y2_i < y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        
        # Calculate union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def update(self, detections, frame_idx):
        """
        Update tracker with new frame detections.
        
        Args:
            detections: List of detections from current frame
            frame_idx: Current frame index
        
        Returns:
            List of tracked detections with IDs
        """
        # Mark all vehicles as not seen this frame
        for vehicle_id in self.tracked_vehicles:
            self.tracked_vehicles[vehicle_id]['frames_missing'] += 1
        
        tracked_detections = []
        
        for det in detections:
            bbox = det['bbox']
            cls = det['class_name']
            conf = det['confidence']
            
            # Find best matching existing vehicle
            best_match_id = None
            best_iou = 0
            
            for vehicle_id, vehicle in self.tracked_vehicles.items():
                # Only match same class
                if vehicle['class_name'] != cls:
                    continue
                
                iou = self.calculate_iou(bbox, vehicle['bbox'])
                
                if iou > best_iou and iou >= self.iou_threshold:
                    best_iou = iou
                    best_match_id = vehicle_id
            
            if best_match_id is not None:
                # Update existing vehicle
                self.tracked_vehicles[best_match_id]['bbox'] = bbox
                self.tracked_vehicles[best_match_id]['confidence'] = conf
                self.tracked_vehicles[best_match_id]['last_frame'] = frame_idx
                self.tracked_vehicles[best_match_id]['frames_missing'] = 0
                
                # Update centroid history
                cx = (bbox[0] + bbox[2]) // 2
                cy = (bbox[1] + bbox[3]) // 2
                self.tracked_vehicles[best_match_id]['centroids'].append((cx, cy))
                
                # Keep history manageable
                if len(self.tracked_vehicles[best_match_id]['centroids']) > 30:
                     self.tracked_vehicles[best_match_id]['centroids'].pop(0)
                
                tracked_detections.append({
                    'id': best_match_id,
                    'bbox': bbox,
                    'class_name': cls,
                    'confidence': conf,
                    'violation_count': self.tracked_vehicles[best_match_id]['violation_count'],
                    'license_plate': self.tracked_vehicles[best_match_id]['license_plate'],
                    'speed_kmh': self.tracked_vehicles[best_match_id].get('speed_kmh', 0.0)
                })
            else:
                # New vehicle
                vehicle_id = self.next_id
                self.next_id += 1
                
                # Calculate center
                cx = (bbox[0] + bbox[2]) // 2
                cy = (bbox[1] + bbox[3]) // 2
                
                self.tracked_vehicles[vehicle_id] = {
                    'bbox': bbox,
                    'class_name': cls,
                    'confidence': conf,
                    'first_frame': frame_idx,
                    'last_frame': frame_idx,
                    'frames_missing': 0,
                    'violation_count': 0,
                    'license_plate': None,
                    'has_violated': False,
                    'violated_types': set(),
                    'centroids': [(cx, cy)],
                    'speed_kmh': 0.0
                }
                
                tracked_detections.append({
                    'id': vehicle_id,
                    'bbox': bbox,
                    'class_name': cls,
                    'confidence': conf,
                    'violation_count': 0,
                    'license_plate': None,
                    'speed_kmh': 0.0
                })
        
        # Remove old vehicles
        to_remove = []
        for vehicle_id, vehicle in self.tracked_vehicles.items():
            if vehicle['frames_missing'] > self.max_missing_frames:
                to_remove.append(vehicle_id)
        
        for vehicle_id in to_remove:
            del self.tracked_vehicles[vehicle_id]
        
        return tracked_detections

    def calculate_speed(self, vehicle_id, fps=30.0, ppm=30.0):
        """Calculate speed in km/h using pixel displacement."""
        if vehicle_id not in self.tracked_vehicles:
            return 0.0
            
        vehicle = self.tracked_vehicles[vehicle_id]
        centroids = vehicle['centroids']
        
        # Need at least 2 centroids to calculate movement
        if len(centroids) < 2:
            return vehicle.get('speed_kmh', 0.0)  # Return cached speed
        
        # Use last 2-5 frames depending on what's available
        frames_to_use = min(5, len(centroids))
        p1 = centroids[-frames_to_use]
        p2 = centroids[-1]
        
        pixel_dist = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        real_dist_m = pixel_dist / ppm
        
        time_elapsed_s = frames_to_use / fps
        
        if time_elapsed_s > 0:
            speed_mps = real_dist_m / time_elapsed_s
            speed_kmh = speed_mps * 3.6
        else:
            speed_kmh = 0.0
        
        # Smooth speed to reduce jitter
        if vehicle.get('speed_kmh', 0) > 0:
            speed_kmh = (vehicle['speed_kmh'] * 0.6) + (speed_kmh * 0.4)
             
        vehicle['speed_kmh'] = speed_kmh
        return speed_kmh
    
    def mark_violation(self, vehicle_id, violation_type='Red Light Violation'):
        """
        Mark a vehicle as having committed a specific violation.
        Counts each unique violation type once per vehicle.
        
        Returns:
            bool: True if this is a new violation of this type
        """
        if vehicle_id in self.tracked_vehicles:
            vehicle = self.tracked_vehicles[vehicle_id]
            
            # Initialize set if not present (migration/safty)
            if 'violated_types' not in vehicle:
                vehicle['violated_types'] = set()
                if vehicle['has_violated']:
                    vehicle['violated_types'].add('Red Light Violation')
            
            if violation_type not in vehicle['violated_types']:
                vehicle['violated_types'].add(violation_type)
                vehicle['violation_count'] += 1
                vehicle['has_violated'] = True
                self.total_violations_cumulative += 1  # Track cumulative
                return True
        return False
    
    def update_license_plate(self, vehicle_id, plate):
        """Update license plate for a vehicle."""
        if vehicle_id in self.tracked_vehicles:
            self.tracked_vehicles[vehicle_id]['license_plate'] = plate
    
    def get_stats(self):
        """Get tracking statistics with cumulative violation count."""
        total_vehicles = self.next_id - 1
        active_vehicles = len(self.tracked_vehicles)
        
        # Use cumulative counter that persists even after vehicles leave scene
        total_violations = self.total_violations_cumulative
        
        return {
            'total_unique_vehicles': total_vehicles,
            'active_vehicles': active_vehicles,
            'total_violations': total_violations
        }
