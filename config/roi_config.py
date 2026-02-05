"""
ROI (Region of Interest) Configuration for TrafficAI.

This module defines configurable ROIs for:
- Stop lines (for red-light violations)
- Speed measurement zones
- Lane boundaries

ROIs must be calibrated for each specific camera position.
"""

import json
import os
from typing import List, Tuple, Dict, Optional

class ROIConfig:
    """Base class for ROI configurations."""
    
    def __init__(self, name: str, points: List[Tuple[int, int]]):
        """
        Args:
            name: Descriptive name for this ROI
            points: List of (x, y) coordinates defining the ROI
        """
        self.name = name
        self.points = points
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'points': self.points
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create ROI from dictionary."""
        return cls(data['name'], data['points'])


class StopLineROI(ROIConfig):
    """ROI for stop line detection (red-light violations)."""
    
    def __init__(self, name: str, points: List[Tuple[int, int]], direction: str = "horizontal"):
        """
        Args:
            name: Name of this stop line
            points: Two points defining the line [(x1, y1), (x2, y2)]
            direction: "horizontal" or "vertical"
        """
        super().__init__(name, points)
        self.direction = direction
        
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data['direction'] = self.direction
        return data


class SpeedZoneROI(ROIConfig):
    """ROI for speed measurement zone."""
    
    def __init__(self, name: str, entry_line: List[Tuple[int, int]], 
                 exit_line: List[Tuple[int, int]], real_distance_m: float):
        """
        Args:
            name: Name of speed zone
            entry_line: Two points defining entry line
            exit_line: Two points defining exit line  
            real_distance_m: Real-world distance between lines in meters
        """
        self.name = name
        self.entry_line = entry_line
        self.exit_line = exit_line
        self.real_distance_m = real_distance_m
        
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'entry_line': self.entry_line,
            'exit_line': self.exit_line,
            'real_distance_m': self.real_distance_m
        }


class LaneBoundaryROI(ROIConfig):
    """ROI for lane boundaries."""
    
    def __init__(self, lane_number: int, left_boundary: List[Tuple[int, int]], 
                 right_boundary: List[Tuple[int, int]]):
        """
        Args:
            lane_number: Lane number (1, 2, 3, etc.)
            left_boundary: Points defining left boundary
            right_boundary: Points defining right boundary
        """
        super().__init__(f"Lane {lane_number}", left_boundary)
        self.lane_number = lane_number
        self.left_boundary = left_boundary
        self.right_boundary = right_boundary
        
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'lane_number': self.lane_number,
            'left_boundary': self.left_boundary,
            'right_boundary': self.right_boundary
        }


class CameraROIConfig:
    """Complete ROI configuration for a camera."""
    
    def __init__(self, camera_id: str):
        self.camera_id = camera_id
        self.stop_lines: List[StopLineROI] = []
        self.speed_zones: List[SpeedZoneROI] = []
        self.lane_boundaries: List[LaneBoundaryROI] = []
        self.traffic_signal_roi: Optional[List[Tuple[int, int]]] = None
        
    def add_stop_line(self, name: str, points: List[Tuple[int, int]], direction: str = "horizontal"):
        """Add a stop line ROI."""
        self.stop_lines.append(StopLineROI(name, points, direction))
        
    def add_speed_zone(self, name: str, entry_line: List[Tuple[int, int]], 
                      exit_line: List[Tuple[int, int]], real_distance_m: float):
        """Add a speed measurement zone."""
        self.speed_zones.append(SpeedZoneROI(name, entry_line, exit_line, real_distance_m))
        
    def add_lane_boundary(self, lane_number: int, left_boundary: List[Tuple[int, int]], 
                         right_boundary: List[Tuple[int, int]]):
        """Add lane boundary ROI."""
        self.lane_boundaries.append(LaneBoundaryROI(lane_number, left_boundary, right_boundary))
        
    def set_traffic_signal_roi(self, points: List[Tuple[int, int]]):
        """Set ROI for traffic signal detection."""
        self.traffic_signal_roi = points
        
    def save_to_file(self, filepath: str):
        """Save configuration to JSON file."""
        config_data = {
            'camera_id': self.camera_id,
            'stop_lines': [sl.to_dict() for sl in self.stop_lines],
            'speed_zones': [sz.to_dict() for sz in self.speed_zones],
            'lane_boundaries': [lb.to_dict() for lb in self.lane_boundaries],
            'traffic_signal_roi': self.traffic_signal_roi
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(config_data, f, indent=2)
            
    @classmethod
    def load_from_file(cls, filepath: str):
        """Load configuration from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        config = cls(data['camera_id'])
        
        for sl_data in data.get('stop_lines', []):
            config.add_stop_line(sl_data['name'], sl_data['points'], sl_data.get('direction', 'horizontal'))
            
        for sz_data in data.get('speed_zones', []):
            config.add_speed_zone(sz_data['name'], sz_data['entry_line'], 
                                 sz_data['exit_line'], sz_data['real_distance_m'])
            
        for lb_data in data.get('lane_boundaries', []):
            config.add_lane_boundary(lb_data['lane_number'], lb_data['left_boundary'], 
                                    lb_data['right_boundary'])
            
        config.traffic_signal_roi = data.get('traffic_signal_roi')
        
        return config


# ===== Example Configurations =====

def create_example_config_highway() -> CameraROIConfig:
    """Example configuration for highway camera."""
    config = CameraROIConfig("Highway_Cam_01")
    
    # Stop line for traffic light (horizontal line)
    config.add_stop_line(
        name="Main Stop Line",
        points=[(100, 300), (540, 300)],  # Horizontal line across frame
        direction="horizontal"
    )
    
    # Speed zone (20 meters real distance)
    config.add_speed_zone(
        name="Speed Zone 1",
        entry_line=[(50, 250), (590, 250)],
        exit_line=[(50, 400), (590, 400)],
        real_distance_m=20.0  # Measured real distance
    )
    
    # Lane boundaries
    config.add_lane_boundary(
        lane_number=1,
        left_boundary=[(0, 200), (0, 480)],
        right_boundary=[(213, 200), (213, 480)]
    )
    
    config.add_lane_boundary(
        lane_number=2,
        left_boundary=[(213, 200), (213, 480)],
        right_boundary=[(426, 200), (426, 480)]
    )
    
    config.add_lane_boundary(
        lane_number=3,
        left_boundary=[(426, 200), (426, 480)],
        right_boundary=[(640, 200), (640, 480)]
    )
    
    # Traffic signal ROI (bounding box around signal)
    config.set_traffic_signal_roi([(50, 30), (100, 100)])
    
    return config


def create_example_config_intersection() -> CameraROIConfig:
    """Example configuration for intersection camera."""
    config = CameraROIConfig("Intersection_Cam_01")
    
    # Multiple stop lines for different directions
    config.add_stop_line(
        name="North Stop Line",
        points=[(200, 150), (440, 150)],
        direction="horizontal"
    )
    
    config.add_stop_line(
        name="East Stop Line",
        points=[(480, 200), (480, 400)],
        direction="vertical"
    )
    
    # Traffic signal ROI
    config.set_traffic_signal_roi([(30, 30), (80, 120)])
    
    return config


if __name__ == '__main__':
    # Generate example configurations
    highway_config = create_example_config_highway()
    highway_config.save_to_file('config/roi/highway_cam_01.json')
    print("✅ Created highway camera config: config/roi/highway_cam_01.json")
    
    intersection_config = create_example_config_intersection()
    intersection_config.save_to_file('config/roi/intersection_cam_01.json')
    print("✅ Created intersection camera config: config/roi/intersection_cam_01.json")
    
    print("\n📝 Edit these files to match your camera's perspective!")
