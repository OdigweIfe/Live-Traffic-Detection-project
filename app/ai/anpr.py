"""
ANPR (Automatic Number Plate Recognition) System
Uses specialized YOLOv8 plate detector + PaddleOCR for text extraction.
"""
import cv2
import numpy as np
import re
import os

# Ensure PaddlePaddle fixes are applied
os.environ.setdefault('FLAGS_use_mkldnn', '0')
os.environ.setdefault('FLAGS_enable_pir_api', '0')
# Disable model source check to prevent network timeouts/errors
os.environ.setdefault('PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK', 'True')
os.environ.setdefault('PDX_DISABLE_MODEL_SOURCE_CHECK', 'True')

import torch
# PyTorch 2.6+ Security fix for loading Ultralytics models
try:
    if hasattr(torch.serialization, 'add_safe_globals'):
        import ultralytics.nn.tasks
        torch.serialization.add_safe_globals([
            ultralytics.nn.tasks.DetectionModel,
            ultralytics.nn.tasks.SegmentationModel,
            ultralytics.nn.tasks.PoseModel,
            ultralytics.nn.tasks.ClassificationModel,
            ultralytics.nn.tasks.OBBModel
        ])
except Exception:
    pass

# Try to import YOLO for specialized plate detection
YOLO_AVAILABLE = False
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO = None

# Try to import PaddleOCR
PADDLEOCR_AVAILABLE = False
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except Exception:
    PaddleOCR = None

# Try to import EasyOCR as fallback
EASYOCR_AVAILABLE = False
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except Exception:
    easyocr = None


class ANPR_System:
    """
    Two-stage ANPR system:
    1. Detect license plates using specialized YOLOv8 model
    2. Extract text using PaddleOCR (or EasyOCR fallback)
    """
    
    def __init__(self):
        """Initialize ANPR with specialized plate detector + OCR."""
        self.plate_detector = None
        self.paddle_ocr = None
        self.easyocr_reader = None
        self.use_paddleocr = False
        self.use_easyocr = False
        
        # === GPU Configuration ===
        use_gpu_env = os.environ.get('USE_GPU', 'auto').lower()
        cuda_available = False
        try:
            import torch
            if torch.cuda.is_available():
                cuda_available = True
        except ImportError:
            pass
            
        if use_gpu_env == 'true':
            self.should_use_gpu = True
        elif use_gpu_env == 'auto':
            self.should_use_gpu = cuda_available
        else:
            self.should_use_gpu = False
            
        print(f"⚙️ ANPR GPU Mode: {'ENABLED' if self.should_use_gpu else 'DISABLED'} (Env: {use_gpu_env}, Cuda: {cuda_available})")
        
        # === Stage 1: Plate Detection (Specialized YOLO) ===
        if YOLO_AVAILABLE:
            try:
                print("🔄 Loading specialized license plate detector...")
                # Try local model first (downloaded from Hugging Face)
                # Model should be in the 'models' directory at the project root
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                local_model_path = os.path.join(base_dir, 'models', 'license_plate_detector.pt')
                
                if os.path.exists(local_model_path):
                    self.plate_detector = YOLO(local_model_path)
                    print(f"✅ Specialized plate detector loaded from local file!")
                else:
                    # Fallback to generic YOLOv8
                    print(f"⚠️ Local model not found at {local_model_path}, using generic YOLOv8n")
                    self.plate_detector = YOLO("yolov8n.pt")
            except Exception as e:
                print(f"⚠️ YOLO initialization failed: {e}")
        else:
            print("⚠️ YOLO not available for plate detection")
        
        # === Stage 2: OCR (PaddleOCR preferred) ===
        if PADDLEOCR_AVAILABLE:
            try:
                print(f"🔄 Initializing PaddleOCR (GPU: {self.should_use_gpu})...")
                # Attempt initialization with use_gpu
                try:
                    self.paddle_ocr = PaddleOCR(
                        lang='en',
                        use_doc_orientation_classify=False, 
                        use_doc_unwarping=False, 
                        use_textline_orientation=False,
                        use_gpu=self.should_use_gpu
                    )
                except TypeError as e:
                    if "use_gpu" in str(e):
                        print("⚠️ PaddleOCR 3.x+ detected, using standard initialization...")
                        self.paddle_ocr = PaddleOCR(lang='en')
                    else:
                        raise e
                
                self.use_paddleocr = True
                print("✅ PaddleOCR loaded successfully!")
            except Exception as e:
                print(f"⚠️ PaddleOCR failed: {e}")
        
        # Fallback to EasyOCR
        if not self.use_paddleocr and EASYOCR_AVAILABLE:
            try:
                print(f"🔄 Initializing EasyOCR as fallback (GPU: {self.should_use_gpu})...")
                self.easyocr_reader = easyocr.Reader(['en'], gpu=self.should_use_gpu)
                self.use_easyocr = True
                print("✅ EasyOCR loaded!")
            except Exception as e:
                print(f"⚠️ EasyOCR failed: {e}")
        
        if not self.use_paddleocr and not self.use_easyocr:
            print("❌ No OCR engine available!")

    def detect_plate_region(self, vehicle_crop, imgsz=640, conf=0.25):
        """
        Detect license plate region within a vehicle crop.
        Returns the plate crop or None if not found.
        """
        if self.plate_detector is None:
            return None
        
        try:
            results = self.plate_detector.predict(
                source=vehicle_crop,
                imgsz=imgsz,
                conf=conf,
                verbose=False
            )
            
            if results and len(results) > 0:
                boxes = results[0].boxes
                if boxes is not None and len(boxes) > 0:
                    # Get the most confident detection
                    best_idx = boxes.conf.argmax().item()
                    box = boxes.xyxy[best_idx].cpu().numpy().astype(int)
                    x1, y1, x2, y2 = box
                    
                    # Crop the plate region
                    h, w = vehicle_crop.shape[:2]
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(w, x2), min(h, y2)
                    
                    if x2 > x1 and y2 > y1:
                        plate_crop = vehicle_crop[y1:y2, x1:x2]
                        return plate_crop
            
            return None
            
        except Exception as e:
            print(f"⚠️ Plate detection error: {e}")
            return None

    def preprocess_plate(self, plate_img):
        """Preprocess plate image for better OCR accuracy."""
        if plate_img is None or plate_img.size == 0:
            return None
        
        # Resize if too small
        h, w = plate_img.shape[:2]
        if w < 100:
            scale = 100 / w
            plate_img = cv2.resize(plate_img, None, fx=scale, fy=scale)
        
        # Convert to grayscale
        if len(plate_img.shape) == 3:
            gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_img
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Adaptive threshold
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh

    def extract_text_from_plate(self, plate_crop):
        """Extract text from a plate crop using OCR."""
        if plate_crop is None or plate_crop.size == 0:
            return "N/A"
        
        # Resize plate 2x to make it easier for OCR to read
        plate_crop = cv2.resize(plate_crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        # Try PaddleOCR first
        if self.use_paddleocr and self.paddle_ocr is not None:
            try:
                # Use predict() method (new API for PaddleOCR 3.x)
                result = self.paddle_ocr.predict(input=plate_crop)
                
                # Iterate through results
                texts = []
                for res in result:
                    # Handle different result structures (dict or object)
                    # For object, we should check attributes, but based on PaddleOCR 3.4
                    # it often returns objects that act like dicts or have 'rec_texts' attribute
                    
                    # Try getting texts from known attribute/key
                    rec_texts = None
                    rect_scores = None
                    
                    # Check if it's a dict
                    if isinstance(res, dict):
                         rec_texts = res.get('rec_texts')
                         rect_scores = res.get('rec_scores')
                    # Check if it's an object with attributes
                    elif hasattr(res, 'rec_texts'):
                         rec_texts = res.rec_texts
                         rect_scores = res.rec_scores
                         
                    if rec_texts is not None:
                        # Depending on structure, this might be a list or numpy array
                        for i, text in enumerate(rec_texts):
                            score = rect_scores[i] if rect_scores is not None and i < len(rect_scores) else 0.0
                            if score > 0.5:
                                texts.append(text)
                
                if texts:
                    combined = " ".join([str(t) for t in texts if t])
                    clean = self._clean_plate_text(combined)
                    if clean and len(clean) >= 4:
                        return clean
                        
            except Exception as e:
                print(f"⚠️ PaddleOCR error: {e}")
        
        # Fallback to EasyOCR
        if self.use_easyocr and self.easyocr_reader is not None:
            try:
                results = self.easyocr_reader.readtext(plate_crop, detail=0)
                if results:
                    text = " ".join(results)
                    clean = self._clean_plate_text(text)
                    if clean and len(clean) >= 4:
                        return clean
                
                # Try with preprocessed image
                processed = self.preprocess_plate(plate_crop)
                if processed is not None:
                    results = self.easyocr_reader.readtext(processed, detail=0)
                    if results:
                        text = " ".join(results)
                        clean = self._clean_plate_text(text)
                        if clean and len(clean) >= 4:
                            return clean
                            
            except Exception as e:
                print(f"⚠️ EasyOCR error: {e}")
        
        return "N/A"

    def extract_text(self, vehicle_crop):
        """
        Full ANPR pipeline: detect plate region, then extract text.
        This is the main method called from the processing loop.
        """
        if vehicle_crop is None or vehicle_crop.size == 0:
            return "N/A"
        
        # Step 1: Detect plate region using specialized model
        plate_crop = self.detect_plate_region(vehicle_crop)
        
        if plate_crop is not None and plate_crop.size > 0:
            # Step 2: Extract text from detected plate
            text = self.extract_text_from_plate(plate_crop)
            if text and text != "N/A":
                print(f"✅ Plate Read: '{text}'")
                return text
        
        # Fallback: try OCR on entire vehicle crop (middle region)
        h, w = vehicle_crop.shape[:2]
        middle_crop = vehicle_crop[h//2:, :]  # Bottom half of vehicle
        text = self.extract_text_from_plate(middle_crop)
        
        if text and text != "N/A":
            print(f"✅ Plate Read (fallback): '{text}'")
            return text
        
        print("⚠️ No plate text detected")
        return "N/A"

    def _clean_plate_text(self, text):
        """Clean and validate license plate text."""
        if not text:
            return None
        
        # Remove non-alphanumeric characters
        clean = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        # Filter out common false positives
        invalid_words = ['TAXI', 'UBER', 'LYFT', 'CAB', 'BUS', 'STOP', 'SCHOOL']
        if clean in invalid_words or 'TAXI' in clean:
            return None
        
        # Validate minimum length
        if len(clean) < 4:
            return None
        
        return clean

    def validate_plate(self, text):
        """Basic validation for license plates."""
        if not text or text == "N/A":
            return False
        if len(text) < 4:
            return False
        return True
