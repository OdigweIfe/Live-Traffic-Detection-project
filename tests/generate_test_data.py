"""
Generate sample test images for TrafficAI testing.
This script creates simple synthetic images to be used in unit tests.
"""
import cv2
import numpy as np
import os

def create_test_data_directory():
    """Create test_data directory if it doesn't exist."""
    os.makedirs('test_data', exist_ok=True)
    print("✅ Created test_data directory")

def create_sample_frame():
    """Create a sample traffic frame with vehicles."""
    # Create a road scene (640x480)
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 128  # Gray background
    
    # Draw road
    cv2.rectangle(frame, (0, 200), (640, 480), (80, 80, 80), -1)
    
    # Draw lane markings
    for x in range(0, 640, 40):
        cv2.rectangle(frame, (x, 335), (x+20, 345), (255, 255, 255), -1)
    
    # Draw sample vehicles (rectangles)
    vehicles = [
        (100, 250, 180, 310, (255, 0, 0)),    # Blue car
        (250, 260, 330, 320, (0, 255, 0)),    # Green car
        (400, 255, 480, 315, (0, 0, 255)),    # Red car
    ]
    
    for x1, y1, x2, y2, color in vehicles:
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)
        # Add wheels
        cv2.circle(frame, (x1+15, y2), 8, (0, 0, 0), -1)
        cv2.circle(frame, (x2-15, y2), 8, (0, 0, 0), -1)
    
    # Draw traffic light
    cv2.circle(frame, (50, 50), 25, (100, 100, 100), -1)
    cv2.circle(frame, (50, 50), 15, (0, 0, 255), -1)  # Red light
    
    # Save
    cv2.imwrite('test_data/sample_frame.jpg', frame)
    print("✅ Created sample_frame.jpg")
    return frame

def create_sample_plate():
    """Create a sample license plate image."""
    # Create white background
    plate = np.ones((100, 300, 3), dtype=np.uint8) * 255
    
    # Add border
    cv2.rectangle(plate, (5, 5), (295, 95), (0, 0, 0), 3)
    
    # Add license plate text
    cv2.putText(plate, "ABC 1234", (40, 65), 
                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 4)
    
    # Save
    cv2.imwrite('test_data/sample_plate.jpg', plate)
    print("✅ Created sample_plate.jpg")
    return plate

def create_sample_vehicle_crop():
    """Create a sample vehicle crop with visible plate."""
    # Create vehicle body
    vehicle = np.ones((200, 300, 3), dtype=np.uint8) * 100  # Dark gray
    
    # Draw vehicle shape
    cv2.rectangle(vehicle, (50, 30), (250, 150), (150, 150, 150), -1)
    
    # Draw license plate area
    cv2.rectangle(vehicle, (100, 130), (200, 165), (255, 255, 255), -1)
    cv2.rectangle(vehicle, (100, 130), (200, 165), (0, 0, 0), 2)
    
    # Add plate text
    cv2.putText(vehicle, "XYZ789", (110, 155), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    # Save
    cv2.imwrite('test_data/sample_vehicle.jpg', vehicle)
    print("✅ Created sample_vehicle.jpg (vehicle crop with plate)")
    return vehicle

def create_readme():
    """Create README for test data."""
    readme_content = """# Test Data

This directory contains sample images for testing TrafficAI components.

## Files

- **sample_frame.jpg**: Synthetic traffic scene with multiple vehicles (640x480)
  - Used for testing YOLO vehicle detection
  - Contains 3 simulated vehicles and a traffic light

- **sample_plate.jpg**: Sample license plate image (100x300)
  - Text: "ABC 1234"
  - Used for testing ANPR/OCR accuracy

- **sample_vehicle.jpg**: Vehicle crop with visible plate (200x300)
  - Contains license plate "XYZ789"
  - Used for testing end-to-end plate extraction

## Usage

These images are automatically used by pytest when running:
```bash
pytest tests/test_detector.py
pytest tests/test_anpr.py
```

## Note

Real CCTV footage should be added here for comprehensive testing:
- `real_traffic_video.mp4` - Actual traffic footage with violations
- `real_vehicle_*.jpg` - Real vehicle crops from CCTV

Synthetic images are sufficient for unit testing, but real data is needed for accuracy benchmarking.
"""
    
    with open('test_data/README.md', 'w') as f:
        f.write(readme_content)
    print("✅ Created test_data/README.md")

if __name__ == '__main__':
    print("Generating test data...")
    create_test_data_directory()
    create_sample_frame()
    create_sample_plate()
    create_sample_vehicle_crop()
    create_readme()
    print("\n✅ All test data generated successfully!")
    print("📂 Files created in test_data/:")
    print("   - sample_frame.jpg")
    print("   - sample_plate.jpg")
    print("   - sample_vehicle.jpg")
    print("   - README.md")
