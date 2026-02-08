from ultralytics import YOLO
import torch
import os

class VehicleDetector:
    def __init__(self, model_path='models/yolov8n.pt', plate_model_path='models/license_plate_detector.pt'):
        """
        Initialize YOLOv8 vehicle and license plate detector.
        
        Args:
            model_path (str): Path to YOLOv8 general model weights
            plate_model_path (str): Path to license plate detection model
        """
        # Ensure model directory exists
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Load general model (for vehicles, traffic lights, etc.)
        self.model = YOLO(model_path)
        
        # Try to load dedicated license plate model
        self.plate_model = None
        if os.path.exists(plate_model_path):
            try:
                self.plate_model = YOLO(plate_model_path)
                print(f"✅ Loaded dedicated plate detection model: {plate_model_path}")
            except Exception as e:
                print(f"⚠️ Could not load plate model: {e}, will use fallback")
        else:
            # Download pre-trained license plate model
            try:
                print("📥 Downloading license plate detection model...")
                # Use a publicly available plate detection model from Ultralytics
                self.plate_model = YOLO('yolov8n.pt')  # Fallback to general model
                print("⚠️ Using general YOLOv8 model for plates (less accurate)")
            except Exception as e:
                print(f"⚠️ Plate model download failed: {e}")
        
        # Select device based on configuration
        use_gpu_env = os.environ.get('USE_GPU', 'auto').lower()
        cuda_available = torch.cuda.is_available()
        
        if use_gpu_env == 'true':
            self.device = 'cuda'
        elif use_gpu_env == 'auto':
            self.device = 'cuda' if cuda_available else 'cpu'
        else:
            self.device = 'cpu'
            
        print(f"⚙️ Vehicle Detector using device: {self.device}")
        
        self.model.to(self.device)
        if self.plate_model:
            self.plate_model.to(self.device)
        
        # Vehicle classes in COCO dataset:
        # 2: car, 3: motorcycle, 5: bus, 7: truck
        self.vehicle_classes = [2, 3, 5, 7]
        self.class_names = {
            2: 'car',
            3: 'motorcycle',
            5: 'bus',
            7: 'truck'
        }

    @torch.no_grad()
    def detect(self, frame):
        """
        Detect vehicles in a video frame.
        
        Args:
            frame (numpy.ndarray): Input image frame
            
        Returns:
            list: List of detections
        """
        # Run inference
        results = self.model(frame, verbose=False, conf=0.4, device=self.device)
        
        detections = []
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                
                # Filter for vehicles only
                if cls_id in self.vehicle_classes:
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].tolist()
                    
                    detections.append({
                        'class_id': cls_id,
                        'class_name': self.class_names.get(cls_id, 'vehicle'),
                        'confidence': conf,
                        'bbox': [int(x) for x in xyxy]
                    })
                    
        return detections
    
    @torch.no_grad()
    def detect_license_plate(self, vehicle_crop):
        """
        Detect license plate region within a vehicle crop.
        Uses dedicated plate model if available, otherwise falls back to heuristics.
        
        Args:
            vehicle_crop (numpy.ndarray): Cropped vehicle image
            
        Returns:
            list or None: Bounding box [x1, y1, x2, y2] or None
        """
        # Strategy 1: Use dedicated plate detection model if available
        if self.plate_model is not None:
            try:
                results = self.plate_model(vehicle_crop, verbose=False, conf=0.25, device=self.device)
                
                for result in results:
                    for box in result.boxes:
                        # Return first detected plate
                        xyxy = box.xyxy[0].tolist()
                        return [int(x) for x in xyxy]
            except Exception as e:
                print(f"⚠️ Plate model inference error: {e}")
        
        # Strategy 2: Fallback to heuristic-based detection using general model
        h, w = vehicle_crop.shape[:2]
        
        try:
            results = self.model(vehicle_crop, verbose=False, conf=0.15, device=self.device)
            
            candidates = []
            for result in results:
                for box in result.boxes:
                    xyxy = box.xyxy[0].tolist()
                    x1, y1, x2, y2 = [int(x) for x in xyxy]
                    
                    bbox_w = x2 - x1
                    bbox_h = y2 - y1
                    
                    # Plate heuristics
                    if y1 > h * 0.4:  # Bottom portion
                        aspect_ratio = bbox_w / bbox_h if bbox_h > 0 else 0
                        if 1.5 < aspect_ratio < 6:  # Plate-like ratio
                            area_ratio = (bbox_w * bbox_h) / (w * h)
                            if 0.01 < area_ratio < 0.25:
                                score = float(box.conf[0]) * (1 / (1 + abs(3 - aspect_ratio)))
                                candidates.append({
                                    'bbox': [x1, y1, x2, y2],
                                    'score': score
                                })
            
            if candidates:
                best = max(candidates, key=lambda x: x['score'])
                return best['bbox']
        except Exception as e:
            print(f"⚠️ Heuristic plate detection error: {e}")
        
        # Strategy 3: Return None and let ANPR try full vehicle crop
        return None
