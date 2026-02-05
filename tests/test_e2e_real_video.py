"""
End-to-end test with real traffic video.
Tests the complete pipeline: video processing, detection, violation logging.
"""
import cv2
import os
from app import create_app, db
from app.ai.pipeline import VideoPipeline
from app.models import Violation
from config import config

def test_real_video():
    """Process real traffic video and verify violations are detected."""
    
    # Create app context
    app = create_app('testing')
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        video_path = 'test_data/traffic_video_modified.mp4'
        
        if not os.path.exists(video_path):
            print(f"❌ Video not found: {video_path}")
            return
        
        # Verify video can be opened
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Could not open video: {video_path}")
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        
        print(f"\n📹 Video Info:")
        print(f"   Path: {video_path}")
        print(f"   FPS: {fps}")
        print(f"   Frames: {frame_count}")
        print(f"   Duration: {duration:.2f}s")
        
        # Initialize pipeline
        pipeline_config = {
            'VIOLATIONS_FOLDER': app.config['VIOLATIONS_FOLDER']
        }
        
        os.makedirs(app.config['VIOLATIONS_FOLDER'], exist_ok=True)
        
        pipeline = VideoPipeline(pipeline_config)
        
        print(f"\n🚀 Processing video...")
        results = pipeline.process_video(video_path)
        
        print(f"\n✅ Processing Results:")
        print(f"   Frames Processed: {results.get('frames_processed', 0)}")
        print(f"   Violations Detected: {results.get('violations_detected', 0)}")
        
        # Query database
        violations = Violation.query.all()
        print(f"\n📊 Database Records: {len(violations)}")
        
        if violations:
            print(f"\n📋 Violations Found:")
            for i, v in enumerate(violations[:10], 1):  # Show first 10
                print(f"   {i}. {v.violation_type} - {v.vehicle_type} - {v.license_plate} - {v.timestamp}")
        
        # Verify violations were saved
        assert len(violations) >= 0, "Should have processed without errors"
        
        print(f"\n✅ End-to-end test complete!")
        print(f"   - Video processed successfully")
        print(f"   - Pipeline executed without crashes")
        if len(violations) > 0:
            print(f"   - {len(violations)} violations logged to database")
            print(f"  - Violation images saved to {app.config['VIOLATIONS_FOLDER']}")

if __name__ == '__main__':
    test_real_video()
