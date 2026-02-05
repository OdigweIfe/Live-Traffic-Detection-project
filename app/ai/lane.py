import cv2
import numpy as np

class LaneSystem:
    def __init__(self, lane_rois=[]):
        """
        Initialize Lane Violation System.
        
        Args:
            lane_rois (list): List of polygon coordinates for lanes.
                              Each item: {'id': 1, 'poly': [...], 'type': 'allowed'}
        """
        self.lane_rois = lane_rois
        self.vehicle_lane_map = {} # {vehicle_id: lane_id}

    def set_rois(self, rois):
        self.lane_rois = rois

    def get_lane_id(self, centroid):
        """
        Determine which lane a point belongs to.
        """
        cx, cy = centroid
        
        for lane in self.lane_rois:
            poly = np.array(lane['poly'], np.int32).reshape((-1, 1, 2))
            if cv2.pointPolygonTest(poly, (cx, cy), False) >= 0:
                return lane.get('id')
                
        return None # Unknown/Road Shoulder

    def check_violation(self, vehicle_id, centroid):
        """
        Check for lane violation (e.g., illegal lane change).
        Warning: Needs tracker ID.
        """
        current_lane = self.get_lane_id(centroid)
        
        if vehicle_id in self.vehicle_lane_map:
            prev_lane = self.vehicle_lane_map[vehicle_id]
            
            if current_lane is not None and prev_lane is not None:
                if current_lane != prev_lane:
                    # Lane change detected
                    # Check if allowed (logic can be complex, for MUS assume specific restrictions)
                    # For example, if prev_lane was "straight_only" and current is "turn_lane" illegally
                    
                    # Store new lane
                    self.vehicle_lane_map[vehicle_id] = current_lane
                    
                    # Return True if violation (placeholder logic)
                    if self._is_illegal_change(prev_lane, current_lane):
                        return True
                        
        else:
            if current_lane is not None:
                self.vehicle_lane_map[vehicle_id] = current_lane
                
        return False
        
    def _is_illegal_change(self, from_lane, to_lane):
        # Define rules here (from config)
        # e.g., solid line crossing
        return False # Default to safe
