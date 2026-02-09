import unittest
import numpy as np
from app.ai.vehicle_tracker import VehicleTracker

class TestSpeedAccuracy(unittest.TestCase):
    def setUp(self):
        """Setup tracker for speed tests."""
        self.tracker = VehicleTracker()
        self.ppm = 40.0 # Pixel per meter (from sockets.py production config)
        self.fps = 30.0 # Frames per second

    def test_speed_estimation_accuracy(self):
        """
        Verify speed estimation is within 10% of actual speed.
        Target Speed: 60 km/h
        """
        target_speed_kmh = 60.0
        target_speed_mps = target_speed_kmh / 3.6 # 16.67 m/s
        
        # Calculate pixels per frame
        # Speed (px/s) = Speed (m/s) * PPM
        speed_px_per_sec = target_speed_mps * self.ppm
        px_per_frame = speed_px_per_sec / self.fps
        
        # Simulate vehicle movement over 60 frames (allow convergence)
        # Start at (100, 100) and move in X direction
        start_x, start_y = 100, 100
        
        # Create a fake vehicle detection
        # We need to manually update tracker state because update() expects full detection flow
        # But we can call update() with constructed detections
        
        estimated_speeds = []
        
        for i in range(60):
            # Calculate current position
            curr_x = start_x + (i * px_per_frame)
            bbox = [int(curr_x), int(start_y), int(curr_x) + 50, int(start_y) + 30]
            
            detections = [{
                'bbox': bbox,
                'class_name': 'car',
                'confidence': 0.95
            }]
            
            # Update tracker
            tracked_objs = self.tracker.update(detections, frame_idx=i)
            
            if tracked_objs:
                vid = tracked_objs[0]['id']
                # Calculate speed
                est_speed = self.tracker.calculate_speed(vid, fps=self.fps, ppm=self.ppm)
                estimated_speeds.append(est_speed)
                print(f"Frame {i}: Pos={curr_x:.1f}, Est Speed={est_speed:.2f} km/h")

        # Check the last few frames where speed should have stabilized (smoothing factor)
        final_speed = estimated_speeds[-1]
        
        print(f"\nTarget Speed: {target_speed_kmh} km/h")
        print(f"Final Estimated Speed: {final_speed} km/h")
        
        # Calculate error margin
        error_margin = abs(final_speed - target_speed_kmh) / target_speed_kmh
        print(f"Error Margin: {error_margin:.2%}")
        
        # Assert accuracy within 10%
        self.assertLess(error_margin, 0.10, "Speed estimation error > 10%")

    def test_speed_stationary(self):
        """Verify speed is near 0 for stationary objects."""
        start_x, start_y = 100, 100
        bbox = [start_x, start_y, start_x + 50, start_y + 30]
        
        for i in range(10):
            detections = [{
                'bbox': bbox,
                'class_name': 'car',
                'confidence': 0.95
            }]
            tracked = self.tracker.update(detections, frame_idx=i)
            if tracked:
                vid = tracked[0]['id']
                speed = self.tracker.calculate_speed(vid, fps=self.fps, ppm=self.ppm)
        
        self.assertLess(speed, 5.0, "Stationary vehicle speed should be near 0")

    def test_variable_speed(self):
        """Verify speed adapts to acceleration."""
        # Accelerate from 30 km/h to 60 km/h
        # First 20 frames at 30 km/h
        # Next 40 frames at 60 km/h
        
        speeds_to_sim = [30.0] * 20 + [60.0] * 40
        
        curr_x = 100
        start_y = 100
        
        measured_speeds = []
        
        for i, target_speed in enumerate(speeds_to_sim):
            px_per_frame = (target_speed / 3.6 * self.ppm) / self.fps
            curr_x += px_per_frame
            
            bbox = [int(curr_x), int(start_y), int(curr_x) + 50, int(start_y) + 30]
            detections = [{'bbox': bbox, 'class_name': 'car', 'confidence': 0.95}]
            
            tracked = self.tracker.update(detections, frame_idx=i)
            if tracked:
                vid = tracked[0]['id']
                speed = self.tracker.calculate_speed(vid, fps=self.fps, ppm=self.ppm)
                measured_speeds.append(speed)
        
        final_speed = measured_speeds[-1]
        print(f"Final Speed after acceleration: {final_speed:.2f} km/h (Target: 60)")
        
        # Should be close to 60
        self.assertAlmostEqual(final_speed, 60.0, delta=6.0) # 10% tolerance

if __name__ == '__main__':
    unittest.main()
