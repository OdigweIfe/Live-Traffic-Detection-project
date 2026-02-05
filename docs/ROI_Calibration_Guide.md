# ROI Calibration Guide

## What is ROI Calibration?

ROI (Region of Interest) calibration is the process of defining specific areas in your camera's field of view where violations are detected. Proper calibration is **essential** for accurate violation detection.

---

## Why Calibrate?

Without calibration:
- ❌ No violations will be detected (even if they occur)
- ❌ Wrong vehicles flagged as violators
- ❌ Inaccurate speed measurements

With calibration:
- ✅ Accurate violation detection
- ✅ Correct vehicle tracking
- ✅ Reliable speed estimation

---

## What Needs Calibration?

1. **Stop Lines** - Where vehicles must stop at red lights
2. **Speed Zones** - Entry/exit lines with known distance
3. **Lane Boundaries** - Left and right edges of each lane
4. **Traffic Signal ROI** - Bounding box around the traffic light

---

## Quick Start

### Step 1: Generate Example Configs

```powershell
python config\roi_config.py
```

This creates:
- `config/roi/highway_cam_01.json`
- `config/roi/intersection_cam_01.json`

### Step 2: Use ROI Calibration Tool

```powershell
python tools\roi_calibrator.py --video test_data\traffic_video_modified.mp4
```

This opens an interactive tool to:
- Click points to define ROIs
- Save configurations
- Test ROIs on video frames

---

## Manual Calibration (Frame-by-Frame)

### Step 1: Extract a Sample Frame

```powershell
.\venv\Scripts\Activate.ps1
python
```

```python
import cv2

# Open video
video_path = 'test_data/traffic_video_modified.mp4'
cap = cv2.VideoCapture(video_path)

# Get a middle frame
cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
ret, frame = cap.read()

# Save frame
cv2.imwrite('calibration_frame.jpg', frame)
cap.release()

print("✅ Saved calibration_frame.jpg")
```

### Step 2: Measure Coordinates

Open `calibration_frame.jpg` in an image editor (e.g., Paint, GIMP, Photoshop):

1. **Enable pixel coordinates** display
2. **Hover over key points** and note (x, y) coordinates
3. **Record coordinates** for each ROI type

### Step 3: Define Stop Line

**Find:** The line where vehicles should stop at a red light

**Measure:** Two points defining the line
- Left endpoint: (x1, y1)
- Right endpoint: (x2, y2)

**Example:**
- **Image:** Horizontal stop line across 3 lanes
- **Coordinates:** (100, 300) to (540, 300)

**Add to config:**
```python
config.add_stop_line(
    name="Main Stop Line",
    points=[(100, 300), (540, 300)],
    direction="horizontal"
)
```

### Step 4: Define Speed Zone

**Find:** Two parallel lines with **known real-world distance**

**Measure:**
1. **Entry line:** Two points
2. **Exit line:** Two points
3. **Real distance:** Walk/measure the actual distance in meters

**Example:**
- Entry: (50, 250) to (590, 250)
- Exit: (50, 400) to (590, 400)
- Real distance: 20 meters (measured on road)

**Add to config:**
```python
config.add_speed_zone(
    name="Speed Zone 1",
    entry_line=[(50, 250), (590, 250)],
    exit_line=[(50, 400), (590, 400)],
    real_distance_m=20.0
)
```

### Step 5: Define Lane Boundaries

**Find:** Left and right edges of each lane

**Measure:** For each lane, define vertical boundaries

**Example (3-lane highway):**
- **Lane 1:** x=0 to x=213
- **Lane 2:** x=213 to x=426
- **Lane 3:** x=426 to x=640

**Add to config:**
```python
# Lane 1
config.add_lane_boundary(
    lane_number=1,
    left_boundary=[(0, 200), (0, 480)],
    right_boundary=[(213, 200), (213, 480)]
)

# Lane 2
config.add_lane_boundary(
    lane_number=2,
    left_boundary=[(213, 200), (213, 480)],
    right_boundary=[(426, 200), (426, 480)]
)

# Lane 3
config.add_lane_boundary(
    lane_number=3,
    left_boundary=[(426, 200), (426, 480)],
    right_boundary=[(640, 200), (640, 480)]
)
```

### Step 6: Define Traffic Signal ROI

**Find:** The traffic light in the frame

**Measure:** Bounding box around the signal (top-left and bottom-right corners)

**Example:**
- Top-left: (50, 30)
- Bottom-right: (100, 100)

**Add to config:**
```python
config.set_traffic_signal_roi([(50, 30), (100, 100)])
```

### Step 7: Save Configuration

```python
from config.roi_config import CameraROIConfig

# Create config
config = CameraROIConfig("My_Camera_01")

# Add all ROIs (from steps above)
config.add_stop_line(...)
config.add_speed_zone(...)
config.add_lane_boundary(...)
config.set_traffic_signal_roi(...)

# Save
config.save_to_file('config/roi/my_camera.json')
print("✅ Configuration saved!")
```

---

## Using Your Configuration

### Method 1: Load in Pipeline

Modify `app/ai/pipeline.py`:

```python
from config.roi_config import CameraROIConfig

class VideoPipeline:
    def __init__(self, config, roi_config_path='config/roi/my_camera.json'):
        self.config = config
        
        # Load ROI config
        self.roi_config = CameraROIConfig.load_from_file(roi_config_path)
        
        # Pass ROIs to detection systems
        self.detector = VehicleDetector()
        self.red_light = RedLightSystem()
        self.speed = SpeedSystem()
        self.lane = LaneSystem()
        
        # Apply ROIs
        if self.roi_config.stop_lines:
            self.red_light.set_stop_line(self.roi_config.stop_lines[0].points)
        
        if self.roi_config.speed_zones:
            zone = self.roi_config.speed_zones[0]
            self.speed.set_zone(zone.entry_line, zone.exit_line, zone.real_distance_m)
        
        if self.roi_config.lane_boundaries:
            self.lane.set_boundaries(self.roi_config.lane_boundaries)
```

### Method 2: Environment Variable

Set in `.env`:
```
ROI_CONFIG_PATH=config/roi/my_camera.json
```

---

## Validation & Testing

### Test ROI Visualization

```python
import cv2
import json

# Load config
with open('config/roi/my_camera.json', 'r') as f:
    roi_data = json.load(f)

# Load frame
frame = cv2.imread('calibration_frame.jpg')

# Draw stop line
stop_line = roi_data['stop_lines'][0]['points']
cv2.line(frame, tuple(stop_line[0]), tuple(stop_line[1]), (0, 0, 255), 3)

# Draw speed zone
speed_zone = roi_data['speed_zones'][0]
entry = speed_zone['entry_line']
exit_line = speed_zone['exit_line']
cv2.line(frame, tuple(entry[0]), tuple(entry[1]), (0, 255, 0), 2)
cv2.line(frame, tuple(exit_line[0]), tuple(exit_line[1]), (0, 255, 0), 2)

# Draw lanes
for lane in roi_data['lane_boundaries']:
    left = lane['left_boundary']
    right = lane['right_boundary']
    cv2.line(frame, tuple(left[0]), tuple(left[1]), (255, 255, 0), 1)
    cv2.line(frame, tuple(right[0]), tuple(right[1]), (255, 255, 0), 1)

# Save visualized frame
cv2.imwrite('roi_visualization.jpg', frame)
print("✅ See roi_visualization.jpg to verify ROIs")
```

---

## Common Pitfalls

### ❌ Using Frame Coordinates from Different Video
**Problem:** Each camera/video has different dimensions  
**Solution:** Always calibrate using a frame from the **actual camera** you'll use

### ❌ Incorrect Real-World Distance
**Problem:** Guessing speed zone distance → inaccurate speed  
**Solution:** **Physically measure** the distance on the road

### ❌ Lane Boundaries Too Narrow/Wide
**Problem:** Vehicles incorrectly assigned to lanes  
**Solution:** Test with real footage and adjust boundaries

### ❌ Traffic Signal ROI Includes Non-Signal Area
**Problem:** False detections (sky, buildings mistaken for signal)  
**Solution:** Make ROI as **tight as possible** around just the signal

---

## Tips for Best Results

✅ **Use a clear, well-lit frame** for calibration  
✅ **Zoom in to get exact pixel coordinates**  
✅ **Test ROIs on multiple frames** to verify accuracy  
✅ **Account for perspective distortion** (distant objects appear smaller)  
✅ **Calibrate separately for each camera** (never reuse configs)

---

## Next Steps

1. ✅ Calibrate ROIs for your camera
2. ✅ Save configuration file
3. ✅ Load config in pipeline
4. ✅ Process test video
5. ✅ Verify violations detected correctly
6. ✅ Fine-tune ROIs if needed

**With proper calibration, TrafficAI will accurately detect all violations!** 🚦✅
