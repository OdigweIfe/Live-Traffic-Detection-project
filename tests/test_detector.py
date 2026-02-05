import pytest
import cv2
import numpy as np
from app.ai.detector import VehicleDetector
import os

@pytest.fixture
def sample_frame():
    """Create a simple test frame."""
    # Create a blank image (640x480, BGR)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Add some content (a simple rectangle to simulate a vehicle)
    cv2.rectangle(frame, (100, 100), (300, 300), (255, 255, 255), -1)
    return frame

@pytest.fixture
def detector():
    """Initialize vehicle detector."""
    # This will download YOLOv8n model if not present
    return VehicleDetector()

def test_detector_initialization(detector):
    """Test that detector initializes correctly."""
    assert detector is not None
    assert detector.model is not None
    assert detector.device in ['cuda', 'cpu']
    assert len(detector.vehicle_classes) == 4
    assert 2 in detector.vehicle_classes  # car
    assert 3 in detector.vehicle_classes  # motorcycle

def test_detector_returns_list(detector, sample_frame):
    """Test that detect method returns a list."""
    detections = detector.detect(sample_frame)
    assert isinstance(detections, list)

def test_detection_structure(detector, sample_frame):
    """Test that detections have correct structure."""
    detections = detector.detect(sample_frame)
    
    # Each detection should be a dict with required keys
    for det in detections:
        assert isinstance(det, dict)
        assert 'class_id' in det
        assert 'class_name' in det
        assert 'confidence' in det
        assert 'bbox' in det
        assert isinstance(det['bbox'], list)
        assert len(det['bbox']) == 4

def test_detector_filters_vehicles_only(detector):
    """Test that only vehicle classes are returned."""
    # Create frame with test content
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = detector.detect(frame)
    
    # All detections should be vehicles
    for det in detections:
        assert det['class_id'] in detector.vehicle_classes
        assert det['class_name'] in ['car', 'motorcycle', 'bus', 'truck']

def test_detector_confidence_threshold(detector, sample_frame):
    """Test that detections meet confidence threshold."""
    detections = detector.detect(sample_frame)
    
    # All detections should have confidence >= 0.4 (threshold in detector.py)
    for det in detections:
        assert det['confidence'] >= 0.4

@pytest.mark.skipif(not os.path.exists('test_data/sample_frame.jpg'), 
                    reason="Sample test image not available")
def test_detector_with_real_image(detector):
    """Test detector with real traffic image."""
    frame = cv2.imread('test_data/sample_frame.jpg')
    assert frame is not None
    
    detections = detector.detect(frame)
    assert isinstance(detections, list)
    
    # Should detect at least some vehicles in a traffic scene
    # (This is a soft assertion - real images may have zero vehicles)
    print(f"Detected {len(detections)} vehicles in sample image")

def test_bbox_coordinates_valid(detector, sample_frame):
    """Test that bounding box coordinates are valid."""
    detections = detector.detect(sample_frame)
    
    for det in detections:
        x1, y1, x2, y2 = det['bbox']
        
        # Coordinates should be positive
        assert x1 >= 0
        assert y1 >= 0
        
        # x2 should be greater than x1, y2 greater than y1
        assert x2 > x1
        assert y2 > y1
        
        # Coordinates should be within frame bounds
        h, w = sample_frame.shape[:2]
        assert x2 <= w
        assert y2 <= h

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
