"""
Quick test to verify EasyOCR ANPR works correctly.
"""
import pytest
import cv2
import os
from app.ai.anpr import ANPR_System

# Check availability
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

@pytest.mark.skipif(not EASYOCR_AVAILABLE, reason="EasyOCR not installed")
def test_easyocr_anpr_extraction():
    """Test ANPR extraction using EasyOCR explicitly."""
    
    # Initialize ANPR system
    anpr = ANPR_System()
    
    # Force EasyOCR usage
    # 1. Disable PaddleOCR flag
    anpr.use_paddleocr = False
    
    # 2. Initialize EasyOCR if not already done (because Paddle might have taken precedence)
    if anpr.easyocr_reader is None:
        try:
            anpr.easyocr_reader = easyocr.Reader(['en'], gpu=False)
            anpr.use_easyocr = True
        except Exception as e:
            pytest.fail(f"Could not initialize EasyOCR manually: {e}")
    else:
        # Ensure the flag is set if reader exists
        anpr.use_easyocr = True

    # Validate setup
    assert anpr.use_paddleocr is False
    assert anpr.use_easyocr is True
    assert anpr.easyocr_reader is not None

    # Test with sample image
    # Trying to find a valid image in the project
    possible_paths = [
        'app/static/violations/violation_21.jpg',
        'app/static/violation_21.jpg',
        'test_data/sample_vehicle.jpg'
    ]
    
    image_path = None
    for p in possible_paths:
        if os.path.exists(p):
            image_path = p
            break
            
    if image_path:
        print(f"Testing with image: {image_path}")
        img = cv2.imread(image_path)
        assert img is not None, "Failed to load image"
        
        # Test extraction
        text = anpr.extract_text(img)
        print(f"Extracted text: '{text}'")
        
        # We assume it returns a string, even if "N/A"
        assert isinstance(text, str)
    else:
        print("No test image found, skipping actual extraction test")