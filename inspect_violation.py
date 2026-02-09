from app import create_app, db
from app.models import Violation
import os

app = create_app()

with app.app_context():
    v = Violation.query.get(99)
    if v:
        print(f"Violation ID: {v.id}")
        print(f"Video Path: {v.video_path}")
        print(f"Image Path: {v.image_path}")
        print(f"Frame Number: {v.frame_number}")
        print(f"Video FPS: {v.video_fps}")
        print(f"Computed Timestamp: {v.video_timestamp_seconds}")
        
        # Check file existence
        if v.video_path:
            full_path = os.path.join(app.root_path, 'static', v.video_path)
            print(f"Absolute Video Path: {full_path}")
            print(f"Exists: {os.path.exists(full_path)}")
            if os.path.exists(full_path):
                print(f"Size: {os.path.getsize(full_path)} bytes")
    else:
        print("Violation 99 not found.")
