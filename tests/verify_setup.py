
import os
import sys
import torch
import cv2
from app import create_app, db
from app.models import Violation
from app.ai.detector import VehicleDetector

def verify_setup():
    print("[-] Verifying Setup...")
    
    # 1. Flask App
    try:
        app = create_app('default')
        print("[+] Flask app created successfully.")
    except Exception as e:
        print(f"[!] Failed to create Flask app: {e}")
        return

    # 2. Database
    with app.app_context():
        try:
            db.create_all()
            print("[+] Database connected and tables created.")
            
            # Try a query
            count = Violation.query.count()
            print(f"[+] Violation count: {count}")
        except Exception as e:
            print(f"[!] Database check failed: {e}")

    # 3. AI Dependencies
    print(f"[-] OpenCV Version: {cv2.__version__}")
    print(f"[-] PyTorch Version: {torch.__version__}")
    print(f"[-] CUDA Available: {torch.cuda.is_available()}")

    # 4. Model Loading
    model_path = os.path.join(os.getcwd(), 'models', 'yolov8n.pt')
    if os.path.exists(model_path):
        print(f"[+] YOLO model found at {model_path}")
        try:
            detector = VehicleDetector(model_path)
            print("[+] VehicleDetector initialized successfully.")
        except Exception as e:
            print(f"[!] Failed to initialize VehicleDetector: {e}")
    else:
        print(f"[!] YOLO model NOT found at {model_path}")

if __name__ == "__main__":
    verify_setup()
