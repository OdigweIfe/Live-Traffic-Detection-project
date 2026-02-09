import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import sys
import os

# Ensure we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.ai.anpr import ANPR_System

class TestANPRMock(unittest.TestCase):
    
    @patch('app.ai.anpr.YOLO')
    @patch('app.ai.anpr.PaddleOCR')
    @patch('app.ai.anpr.easyocr')
    def setUp(self, mock_easyocr, mock_paddle, mock_yolo):
        """Setup ANPR system with mocks."""
        # Store mocks for use in tests
        self.mock_yolo = mock_yolo
        self.mock_paddle = mock_paddle
        self.mock_easyocr = mock_easyocr
        
        # Setup specific return values
        self.mock_detector = MagicMock()
        self.mock_yolo.return_value = self.mock_detector
        
        self.mock_paddle_instance = MagicMock()
        self.mock_paddle.return_value = self.mock_paddle_instance
        
        self.mock_easy_reader = MagicMock()
        self.mock_easyocr.Reader.return_value = self.mock_easy_reader
        
        # Initialize ANPR system with mocked flags
        with patch('app.ai.anpr.YOLO_AVAILABLE', True), \
             patch('app.ai.anpr.PADDLEOCR_AVAILABLE', True), \
             patch('app.ai.anpr.EASYOCR_AVAILABLE', True):
            self.anpr = ANPR_System()

    def test_detect_plate_region_found(self):
        """Test plate detection when YOLO finds a plate."""
        vehicle_crop = np.zeros((100, 200, 3), dtype=np.uint8)
        
        # Mock YOLO result
        mock_result = MagicMock()
        mock_boxes = MagicMock()
        mock_boxes.__len__.return_value = 1 # Fix: Allow len(boxes) check
        
        # Setup the chain: results[0].boxes.conf.argmax().item()
        mock_boxes.conf.argmax.return_value.item.return_value = 0
        
        # Setup the chain: results[0].boxes.xyxy[0].cpu().numpy().astype(int)
        box_tensor = MagicMock()
        box_tensor.cpu.return_value.numpy.return_value.astype.return_value = np.array([50, 20, 150, 80])
        mock_boxes.xyxy.__getitem__.return_value = box_tensor
        
        mock_result.boxes = mock_boxes
        self.mock_detector.predict.return_value = [mock_result]
        
        plate_crop = self.anpr.detect_plate_region(vehicle_crop)
        
        self.assertIsNotNone(plate_crop)
        # Expected size: (80-20) x (150-50) = 60x100
        self.assertEqual(plate_crop.shape, (60, 100, 3))

    def test_detect_plate_region_none(self):
        """Test plate detection when YOLO finds nothing."""
        vehicle_crop = np.zeros((100, 200, 3), dtype=np.uint8)
        self.mock_detector.predict.return_value = []
        
        plate_crop = self.anpr.detect_plate_region(vehicle_crop)
        self.assertIsNone(plate_crop)

    def test_extract_text_paddle_success(self):
        """Test text extraction using PaddleOCR."""
        plate_crop = np.zeros((50, 100, 3), dtype=np.uint8)
        
        # Mock Paddle result
        mock_res = MagicMock()
        mock_res.rec_texts = ["ABC1234"]
        mock_res.rec_scores = [0.99]
        
        self.mock_paddle_instance.predict.return_value = [mock_res]
        
        text = self.anpr.extract_text_from_plate(plate_crop)
        self.assertEqual(text, "ABC1234")

    def test_extract_text_easyocr_fallback(self):
        """Test fallback to EasyOCR."""
        plate_crop = np.zeros((50, 100, 3), dtype=np.uint8)
        
        # Disable Paddle
        self.anpr.use_paddleocr = False
        self.anpr.use_easyocr = True
        self.anpr.easyocr_reader = self.mock_easy_reader # Fix: Inject reader manually
        
        self.mock_easy_reader.readtext.return_value = ["XYZ", "789"]
        
        text = self.anpr.extract_text_from_plate(plate_crop)
        self.assertEqual(text, "XYZ789")

    def test_full_pipeline_success(self):
        """Test full pipeline success."""
        vehicle_crop = np.zeros((100, 200, 3), dtype=np.uint8)
        
        with patch.object(self.anpr, 'detect_plate_region') as mock_detect:
            mock_detect.return_value = np.zeros((30, 60, 3), dtype=np.uint8)
            
            with patch.object(self.anpr, 'extract_text_from_plate') as mock_ocr:
                mock_ocr.return_value = "TE57CAR"
                text = self.anpr.extract_text(vehicle_crop)
                self.assertEqual(text, "TE57CAR")

    def test_clean_plate_text(self):
        """Test text cleaning."""
        self.assertEqual(self.anpr._clean_plate_text("abc-123"), "ABC123")
        self.assertIsNone(self.anpr._clean_plate_text("TAXI"))

    def test_validate_plate(self):
        """Test validation."""
        self.assertTrue(self.anpr.validate_plate("ABCD123"))
        self.assertFalse(self.anpr.validate_plate("N/A"))

if __name__ == '__main__':
    unittest.main()