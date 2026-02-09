from app import create_app
from app.models import Violation
import os

app = create_app()

with app.app_context():
    violation = Violation.query.get(99)
    if violation and violation.video_path:
        full_path = os.path.join(app.root_path, 'static', violation.video_path)
        print(f"Path: {full_path}")
        
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"Size: {size} bytes")
            
            # Read first 12 bytes to check signature
            with open(full_path, 'rb') as f:
                header = f.read(12)
                print(f"Header hex: {header.hex()}")
                # Common MP4 signatures: ftypisom, ftypmp42, etc.
        else:
            print("File does not exist (re-verification)")
