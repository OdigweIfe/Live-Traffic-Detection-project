import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import cv2
import sys
import os

# Ensure we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.utils.video import extract_frames, save_frame

class TestUtilsVideo(unittest.TestCase):
    
    @patch('app.utils.video.cv2.VideoCapture')
    def test_extract_frames_success(self, mock_capture):
        """Test extracting frames from video."""
        mock_cap_instance = MagicMock()
        mock_capture.return_value = mock_cap_instance
        
        mock_cap_instance.isOpened.return_value = True
        
        # Simulate reading 10 frames
        # read() returns (ret, frame)
        dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # 10 successful reads, then 1 failure (EOF)
        side_effect = [(True, dummy_frame)] * 10 + [(False, None)]
        mock_cap_instance.read.side_effect = side_effect
        
        frames, processed = extract_frames("dummy.mp4", every_n_frames=2)
        
        # Should extract frames 0, 2, 4, 6, 8 (5 frames)
        self.assertEqual(len(frames), 5)
        self.assertEqual(processed, 5)
        
    @patch('app.utils.video.cv2.VideoCapture')
    def test_extract_frames_open_fail(self, mock_capture):
        """Test handling of open failure."""
        mock_cap_instance = MagicMock()
        mock_capture.return_value = mock_cap_instance
        mock_cap_instance.isOpened.return_value = False
        
        with self.assertRaises(ValueError):
            extract_frames("bad.mp4")

    @patch('app.utils.video.cv2.imwrite')
    def test_save_frame(self, mock_imwrite):
        """Test saving frame."""
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        save_frame(frame, "test.jpg")
        mock_imwrite.assert_called_with("test.jpg", frame)

if __name__ == '__main__':
    unittest.main()
