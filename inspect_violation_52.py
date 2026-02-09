from app import create_app, db
from app.models import Violation
import os

app = create_app()

with app.app_context():
    v = Violation.query.get(52)
    if v:
        print(f"Violation ID: {v.id}")
        print(f"Video Path in DB: {v.video_path}")
        print(f"Image Path in DB: {v.image_path}")
        
        if v.video_path:
            full_path = os.path.join(app.root_path, 'static', v.video_path)
            print(f"Full Path: {full_path}")
            exists = os.path.exists(full_path)
            print(f"Exists: {exists}")
            if exists:
                print(f"Size: {os.path.getsize(full_path)} bytes")
            else:
                print("File does NOT exist on disk.")
        else:
            print("Video path is None/Empty in DB.")
    else:
        print("Violation 52 not found in DB.")
