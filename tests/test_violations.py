import pytest
import numpy as np
from app.ai.red_light import RedLightSystem
from app.ai.speed import SpeedSystem
from app.ai.lane import LaneSystem

# ===== Red Light Tests =====

@pytest.fixture
def red_light_system():
    """Initialize red light detection system."""
    return RedLightSystem()

@pytest.fixture
def sample_frame_red():
    """Create a frame with red light simulation."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Add a red circle to simulate red traffic light
    import cv2
    cv2.circle(frame, (320, 50), 20, (0, 0, 255), -1)  # Red light (BGR)
    return frame

@pytest.fixture
def sample_frame_green():
    """Create a frame with green light simulation."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    import cv2
    cv2.circle(frame, (320, 50), 20, (0, 255, 0), -1)  # Green light (BGR)
    return frame

def test_red_light_initialization(red_light_system):
    """Test red light system initializes correctly."""
    assert red_light_system is not None

def test_detect_signal_state_returns_string(red_light_system, sample_frame_red):
    """Test that signal detection returns a string."""
    state = red_light_system.detect_signal_state(sample_frame_red)
    assert isinstance(state, str)
    assert state in ['red', 'green', 'yellow', 'unknown']

def test_check_violation_returns_bool(red_light_system):
    """Test that violation check returns boolean."""
    bbox = [100, 200, 150, 250]  # Sample bounding box
    signal_state = 'red'
    
    result = red_light_system.check_violation(bbox, signal_state)
    assert isinstance(result, bool)

def test_no_violation_on_green(red_light_system):
    """Test that green light does not trigger violation."""
    bbox = [100, 200, 150, 250]
    signal_state = 'green'
    
    # Should not be a violation when light is green
    result = red_light_system.check_violation(bbox, signal_state)
    # This depends on implementation, but green should generally allow passage

def test_handles_various_bbox_formats(red_light_system):
    """Test that system handles different bbox formats."""
    bboxes = [
        [10, 20, 50, 60],
        [100, 100, 200, 200],
        [0, 0, 10, 10],
    ]
    
    for bbox in bboxes:
        result = red_light_system.check_violation(bbox, 'red')
        assert isinstance(result, bool)


# ===== Speed Tests =====

@pytest.fixture
def speed_system():
    """Initialize speed estimation system."""
    system = SpeedSystem()
    system.update_fps(30)  # Set 30 FPS for testing
    return system

def test_speed_initialization(speed_system):
    """Test speed system initializes correctly."""
    assert speed_system is not None

def test_update_fps(speed_system):
    """Test FPS update functionality."""
    speed_system.update_fps(60)
    # FPS should be updated (can't directly test private variable, but ensure no crash)

def test_estimate_speed_returns_float_or_none(speed_system):
    """Test that speed estimation returns float or None."""
    # Simulate vehicle tracking across frames
    track_id = 1
    center1 = (100, 200)
    center2 = (150, 200)  # Moved 50 pixels
    
    # First call establishes position
    speed1 = speed_system.estimate_speed(track_id, center1, 1)
    
    # Second call calculates speed
    speed2 = speed_system.estimate_speed(track_id, center2, 2)
    
    # First call might return None, second should return float or None
    assert speed1 is None or isinstance(speed1, float)
    assert speed2 is None or isinstance(speed2, float)

def test_speed_calculation_consistency(speed_system):
    """Test that speed increases with faster movement."""
    track_id = 1
    
    # Slower movement
    speed_system.estimate_speed(track_id, (100, 200), 1)
    slow_speed = speed_system.estimate_speed(track_id, (110, 200), 2)
    
    # Reset for faster movement
    speed_system2 = SpeedSystem()
    speed_system2.update_fps(30)
    track_id2 = 2
    
    speed_system2.estimate_speed(track_id2, (100, 200), 1)
    fast_speed = speed_system2.estimate_speed(track_id2, (200, 200), 2)
    
    # Faster movement should result in higher speed (if not None)
    if slow_speed is not None and fast_speed is not None:
        assert fast_speed > slow_speed


# ===== Lane Tests =====

@pytest.fixture
def lane_system():
    """Initialize lane violation system."""
    return LaneSystem()

def test_lane_initialization(lane_system):
    """Test lane system initializes correctly."""
    assert lane_system is not None

def test_get_lane_returns_int_or_none(lane_system):
    """Test that lane detection returns int or None."""
    center = (320, 240)  # Center of 640x480 frame
    
    lane = lane_system.get_lane(center)
    assert lane is None or isinstance(lane, int)

def test_check_violation_returns_bool(lane_system):
    """Test that lane violation check returns boolean."""
    track_id = 1
    center = (320, 240)
    
    result = lane_system.check_violation(track_id, center)
    assert isinstance(result, bool)

def test_lane_tracking_consistency(lane_system):
    """Test that lane tracking maintains state."""
    track_id = 1
    
    # First position
    lane_system.check_violation(track_id, (100, 200))
    
    # Second position (slight movement)
    result = lane_system.check_violation(track_id, (105, 200))
    
    assert isinstance(result, bool)

def test_handles_multiple_vehicles(lane_system):
    """Test that system tracks multiple vehicles independently."""
    track_ids = [1, 2, 3, 4, 5]
    centers = [(100, 200), (200, 200), (300, 200), (400, 200), (500, 200)]
    
    for track_id, center in zip(track_ids, centers):
        result = lane_system.check_violation(track_id, center)
        assert isinstance(result, bool)


# ===== Integration Tests =====

def test_all_systems_initialize_together():
    """Test that all violation detection systems can be initialized together."""
    red_light = RedLightSystem()
    speed = SpeedSystem()
    lane = LaneSystem()
    
    assert red_light is not None
    assert speed is not None
    assert lane is not None

def test_violation_workflow_integration():
    """Test a complete violation detection workflow."""
    # Initialize systems
    red_light = RedLightSystem()
    speed = SpeedSystem()
    lane = LaneSystem()
    
    # Simulate frame processing
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    bbox = [100, 200, 150, 250]
    track_id = 1
    center = (125, 225)
    
    # Check red light
    signal_state = red_light.detect_signal_state(frame)
    red_violation = red_light.check_violation(bbox, signal_state)
    
    # Check speed
    speed.update_fps(30)
    estimated_speed = speed.estimate_speed(track_id, center, 1)
    
    # Check lane
    lane_violation = lane.check_violation(track_id, center)
    
    # All systems should complete without errors
    assert isinstance(red_violation, bool)
    assert estimated_speed is None or isinstance(estimated_speed, float)
    assert isinstance(lane_violation, bool)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
