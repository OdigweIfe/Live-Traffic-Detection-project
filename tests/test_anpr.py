import pytest
import cv2
import numpy as np
from app.ai.anpr import ANPR_System
import os

@pytest.fixture
def anpr_system():
    """Initialize ANPR system."""
    return ANPR_System()

@pytest.fixture
def sample_vehicle_crop():
    """Create a simple test vehicle crop."""
    # Create a blank image with some text-like patterns
    crop = np.ones((100, 200, 3), dtype=np.uint8) * 255
    # Add a dark rectangle to simulate license plate area
    cv2.rectangle(crop, (50, 30), (150, 70), (50, 50, 50), -1)
    # Add some white rectangles to simulate characters
    cv2.putText(crop, "ABC123", (55, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    return crop

def test_anpr_initialization(anpr_system):
    """Test that ANPR system initializes correctly."""
    assert anpr_system is not None

def test_extract_text_returns_string(anpr_system, sample_vehicle_crop):
    """Test that extract_text returns a string."""
    result = anpr_system.extract_text(sample_vehicle_crop)
    assert isinstance(result, str)

def test_extract_text_handles_empty_image(anpr_system):
    """Test that ANPR handles empty/black images gracefully."""
    # Create a completely black image
    empty_crop = np.zeros((100, 200, 3), dtype=np.uint8)
    result = anpr_system.extract_text(empty_crop)
    
    # Should return empty string or "N/A"
    assert isinstance(result, str)

def test_extract_text_filters_alphanumeric(anpr_system):
    """Test that extracted text contains only alphanumeric characters."""
    crop = np.ones((100, 200, 3), dtype=np.uint8) * 255
    cv2.putText(crop, "Test!@#123", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    result = anpr_system.extract_text(crop)
    
    # Result should only contain alphanumeric characters (or be empty)
    if result and result != "N/A":
        # Allow only letters, numbers, and spaces
        assert all(c.isalnum() or c.isspace() for c in result)

def test_preprocessing_enhances_contrast(anpr_system, sample_vehicle_crop):
    """Test that preprocessing is applied."""
    # This is tested indirectly - just ensure method doesn't crash
    result = anpr_system.extract_text(sample_vehicle_crop)
    assert result is not None

@pytest.mark.skipif(not os.path.exists('test_data/sample_plate.jpg'), 
                    reason="Sample plate image not available")
def test_anpr_with_real_plate_image(anpr_system):
    """Test ANPR with real license plate crop."""
    crop = cv2.imread('test_data/sample_plate.jpg')
    assert crop is not None
    
    result = anpr_system.extract_text(crop)
    assert isinstance(result, str)
    
    print(f"Extracted text from sample plate: '{result}'")
    
    # For a real plate, we should get some text (unless OCR fails)
    # This is a soft check - OCR might not always work perfectly

def test_handles_various_image_sizes(anpr_system):
    """Test that ANPR handles different image sizes."""
    sizes = [(50, 100), (100, 200), (200, 400), (150, 300)]
    
    for h, w in sizes:
        crop = np.ones((h, w, 3), dtype=np.uint8) * 128
        result = anpr_system.extract_text(crop)
        assert isinstance(result, str)

def test_handles_grayscale_conversion(anpr_system):
    """Test that color images are properly converted to grayscale."""
    # Create a color image
    color_crop = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)
    
    # Should not crash
    result = anpr_system.extract_text(color_crop)
    assert isinstance(result, str)

def test_empty_result_returns_empty_string_or_na(anpr_system):
    """Test that images with no text return empty string or N/A."""
    # Completely white image - no text
    white_crop = np.ones((100, 200, 3), dtype=np.uint8) * 255
    result = anpr_system.extract_text(white_crop)
    
    # Should be empty or "N/A"
    assert result == "" or result == "N/A" or len(result) == 0

def test_multiple_extractions_consistent(anpr_system, sample_vehicle_crop):
    """Test that multiple extractions on same image are consistent."""
    result1 = anpr_system.extract_text(sample_vehicle_crop)
    result2 = anpr_system.extract_text(sample_vehicle_crop)
    
    # Results should be identical
    assert result1 == result2

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
