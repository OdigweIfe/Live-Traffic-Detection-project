import numpy as np

class SpeedSystem:
    def __init__(self, calibration_factor=0.05):
        """
        Initialize Speed Detection System.
        
        Args:
            calibration_factor (float): Meters per pixel (needs calibration).
        """
        self.calibration_factor = calibration_factor
        self.track_history = {} # {id: {'last_pos': (x,y), 'last_time': t}}
        self.fps = 30 # Default assumption

    def update_fps(self, fps):
        self.fps = fps

    def estimate_speed(self, vehicle_id, centroid, current_frame_idx):
        """
        Estimate speed based on displacement between frames.
        
        Args:
            vehicle_id (int): Unique ID from tracker.
            centroid (tuple): (x, y) center point.
            current_frame_idx (int): Current frame number.
            
        Returns:
            float: Speed in km/h, or None if insufficient history.
        """
        if vehicle_id not in self.track_history:
            self.track_history[vehicle_id] = {
                'start_pos': centroid,
                'start_frame': current_frame_idx,
                'history': [centroid] # Keep last few positions
            }
            return None
        
        # Simple speed calculation over discrete interval (e.g., 5 frames)
        data = self.track_history[vehicle_id]
        
        # Wait for some movement history (e.g., 10 frames)
        frames_elapsed = current_frame_idx - data['start_frame']
        if frames_elapsed < 10:
            data['history'].append(centroid)
            return None
            
        # Calculate distance
        start_pos = data['start_pos']
        # Distance (Euclidean) in pixels
        dist_px = np.sqrt((centroid[0] - start_pos[0])**2 + (centroid[1] - start_pos[1])**2)
        
        # Convert to meters
        dist_m = dist_px * self.calibration_factor
        
        # Calculate time (seconds)
        time_sec = frames_elapsed / self.fps
        
        if time_sec == 0:
            return 0
            
        # Speed (m/s)
        speed_ms = dist_m / time_sec
        
        # Speed (km/h)
        speed_kmh = speed_ms * 3.6
        
        # Update history for sliding window
        # For simplicity in MUS, we just use start->current. 
        # In tracking, we'd update "last_pos" every second effectively.
        
        return round(speed_kmh, 1)
