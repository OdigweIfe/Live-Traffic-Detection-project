"""
Auto-calibrate ROI for traffic_video_modified.mp4
"""
import cv2
import os
import sys
import json

# Don't use package import for roi_config to avoid conflict
# Instead, we'll define a simple class here
class CameraROIConfig:
    def __init__(self, camera_id):
        self.camera_id = camera_id
        self.stop_lines = []
        self.speed_zones = []
        self.lane_boundaries = []
        self.traffic_signal_roi = None
    
    class StopLine:
        def __init__(self, name, points, direction="horizontal"):
            self.name = name
            self.points = points
            self.direction = direction
    
    class SpeedZone:
        def __init__(self, name, entry_line, exit_line, real_distance_m):
            self.name = name
            self.entry_line = entry_line
            self.exit_line = exit_line
            self.real_distance_m = real_distance_m
    
    class LaneBoundary:
        def __init__(self, lane_number, left_boundary, right_boundary):
            self.name = f"Lane {lane_number}"
            self.lane_number = lane_number
            self.left_boundary = left_boundary
            self.right_boundary = right_boundary
    
    def add_stop_line(self, name, points, direction="horizontal"):
        self.stop_lines.append(self.StopLine(name, points, direction))
    
    def add_speed_zone(self, name, entry_line, exit_line, real_distance_m):
        self.speed_zones.append(self.SpeedZone(name, entry_line, exit_line, real_distance_m))
    
    def add_lane_boundary(self, lane_number, left_boundary, right_boundary):
        self.lane_boundaries.append(self.LaneBoundary(lane_number, left_boundary, right_boundary))
    
    def set_traffic_signal_roi(self, points):
        self.traffic_signal_roi = points
    
    def save_to_file(self, filepath):
        config_data = {
            'camera_id': self.camera_id,
            'stop_lines': [{'name': sl.name, 'points': sl.points, 'direction': sl.direction} for sl in self.stop_lines],
            'speed_zones': [{'name': sz.name, 'entry_line': sz.entry_line, 'exit_line': sz.exit_line, 'real_distance_m': sz.real_distance_m} for sz in self.speed_zones],
            'lane_boundaries': [{'name': lb.name, 'lane_number': lb.lane_number, 'left_boundary': lb.left_boundary, 'right_boundary': lb.right_boundary} for lb in self.lane_boundaries],
            'traffic_signal_roi': self.traffic_signal_roi
        }
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(config_data, f, indent=2)

import argparse

# Parse arguments
parser = argparse.ArgumentParser(description='Auto-calibrate ROI for a given video')
parser.add_argument('--video', type=str, required=True, help='Path to input video file')
parser.add_argument('--output', type=str, required=True, help='Path to output JSON config file')
args = parser.parse_args()

# Path to video
video_path = args.video
config_path = args.output
visualization_path = config_path.replace('.json', '_vis.jpg')

# Open video
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print(f"❌ Could not open video: {video_path}")
    exit(1)

# Get video properties
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

print(f"📹 Video Info:")
print(f"   Resolution: {width}x{height}")
print(f"   Total Frames: {total_frames}")

# Extract middle frame
cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
ret, frame = cap.read()
cap.release()

if not ret:
    print("❌ Could not extract frame")
    exit(1)

# Save calibration frame
os.makedirs('config/roi', exist_ok=True)
cv2.imwrite('config/roi/calibration_frame.jpg', frame)
print(f"✅ Saved calibration frame: config/roi/calibration_frame.jpg")

# Create ROI configuration with reasonable defaults
print(f"\n🎯 Creating ROI configuration...")

config = CameraROIConfig("traffic_video_modified")

# Stop line (horizontal line across middle-bottom of frame)
# Assume vehicles cross from top to bottom
stop_line_y = int(height * 0.65)  # 65% down the frame
config.add_stop_line(
    name="Main Stop Line",
    points=[(int(width * 0.1), stop_line_y), (int(width * 0.9), stop_line_y)],
    direction="horizontal"
)
print(f"   ✅ Stop line at y={stop_line_y}")

# Speed zone (two horizontal lines with 20m distance)
entry_y = int(height * 0.35)  # Upper line
exit_y = int(height * 0.65)   # Lower line (same as stop line)
config.add_speed_zone(
    name="Speed Zone 1",
    entry_line=[(int(width * 0.1), entry_y), (int(width * 0.9), entry_y)],
    exit_line=[(int(width * 0.1), exit_y), (int(width * 0.9), exit_y)],
    real_distance_m=20.0  # Estimate - adjust based on actual road
)
print(f"   ✅ Speed zone: entry y={entry_y}, exit y={exit_y}")

# Lane boundaries (3 lanes - typical road)
# Divide width into 3 equal lanes
lane_width = width // 3

config.add_lane_boundary(
    lane_number=1,
    left_boundary=[(0, int(height * 0.3)), (0, height)],
    right_boundary=[(lane_width, int(height * 0.3)), (lane_width, height)]
)

config.add_lane_boundary(
    lane_number=2,
    left_boundary=[(lane_width, int(height * 0.3)), (lane_width, height)],
    right_boundary=[(lane_width * 2, int(height * 0.3)), (lane_width * 2, height)]
)

config.add_lane_boundary(
    lane_number=3,
    left_boundary=[(lane_width * 2, int(height * 0.3)), (lane_width * 2, height)],
    right_boundary=[(width, int(height * 0.3)), (width, height)]
)
print(f"   ✅ 3 lanes configured (width: {lane_width}px each)")

# Traffic signal ROI (top-left corner by default)
signal_x = int(width * 0.05)
signal_y = int(height * 0.05)
signal_w = int(width * 0.1)
signal_h = int(height * 0.15)

config.set_traffic_signal_roi([
    (signal_x, signal_y), 
    (signal_x + signal_w, signal_y + signal_h)
])
print(f"   ✅ Traffic signal ROI: top-left corner")

# Save configuration
# config_path is already set from args
config.save_to_file(config_path)
print(f"\n✅ Configuration saved: {config_path}")

# Draw ROIs on calibration frame for visualization
import cv2
vis_frame = frame.copy()

# Draw stop line (RED)
cv2.line(vis_frame, (int(width * 0.1), stop_line_y), (int(width * 0.9), stop_line_y), (0, 0, 255), 3)
cv2.putText(vis_frame, "STOP LINE", (int(width * 0.1), stop_line_y - 10), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

# Draw speed zone (GREEN)
cv2.line(vis_frame, (int(width * 0.1), entry_y), (int(width * 0.9), entry_y), (0, 255, 0), 2)
cv2.putText(vis_frame, "SPEED ENTRY", (int(width * 0.1), entry_y - 10), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
cv2.line(vis_frame, (int(width * 0.1), exit_y), (int(width * 0.9), exit_y), (0, 255, 0), 2)
cv2.putText(vis_frame, "SPEED EXIT", (int(width * 0.1), exit_y + 25), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

# Draw lane boundaries (YELLOW)
cv2.line(vis_frame, (lane_width, int(height * 0.3)), (lane_width, height), (0, 255, 255), 2)
cv2.line(vis_frame, (lane_width * 2, int(height * 0.3)), (lane_width * 2, height), (0, 255, 255), 2)
cv2.putText(vis_frame, "L1", (lane_width // 2, height - 20), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
cv2.putText(vis_frame, "L2", (lane_width + lane_width // 2, height - 20), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
cv2.putText(vis_frame, "L3", (lane_width * 2 + lane_width // 2, height - 20), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

# Draw traffic signal ROI (BLUE)
cv2.rectangle(vis_frame, (signal_x, signal_y), (signal_x + signal_w, signal_y + signal_h), (255, 0, 0), 2)
cv2.putText(vis_frame, "SIGNAL", (signal_x, signal_y - 5), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

cv2.imwrite(visualization_path, vis_frame)
print(f"✅ Saved visualization: {visualization_path}")

print(f"\n🎉 ROI calibration complete!")
print(f"\n📝 Next steps:")
print(f"   1. Check roi_visualization.jpg to see the ROI overlay")
print(f"   2. If it looks good, the system will now use these ROIs automatically")
print(f"   3. Re-upload your video to test violation detection")
print(f"   4. Adjust ROIs in {config_path} if needed")
