"""
Simple ANPR Test Script
Tests license plate detection and OCR on violation_21.jpg
"""
import os
import sys
import cv2
import numpy as np

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Set PaddlePaddle environment variables BEFORE importing
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_enable_pir_api'] = '0'

def main():
    # Path to test image
    image_path = os.path.join(os.path.dirname(__file__), 'app', 'static', 'violations', 'violation_21.jpg')
    
    print("=" * 60)
    print("ANPR Test Script - License Plate Detection & Recognition")
    print("=" * 60)
    print(f"\n📷 Image: {image_path}")
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print("❌ Failed to load image")
        return
    
    h, w = image.shape[:2]
    print(f"✅ Image loaded: {w}x{h} pixels")
    
    # ===== Stage 1: License Plate Detection with YOLO =====
    print("\n" + "-" * 40)
    print("Stage 1: License Plate Detection (YOLO)")
    print("-" * 40)
    
    plate_crop = None
    used_yolo = False
    
    try:
        from ultralytics import YOLO
        
        # Look for specialized plate detector
        model_path = os.path.join(os.path.dirname(__file__), 'models', 'license_plate_detector.pt')
        
        if os.path.exists(model_path):
            print(f"🔄 Loading specialized plate detector...")
            detector = YOLO(model_path)
            print("✅ Specialized plate detector loaded!")
        else:
            print(f"⚠️ Specialized model not found at: {model_path}")
            print("⚠️ Using generic YOLOv8n (won't detect plates specifically)")
            detector = YOLO("yolov8n.pt")
        
        # Run detection
        results = detector.predict(source=image, conf=0.25, verbose=False)
        
        if results and len(results) > 0:
            boxes = results[0].boxes
            if boxes is not None and len(boxes) > 0:
                print(f"✅ Found {len(boxes)} detections")
                
                # Show all detections
                for i, (box, conf) in enumerate(zip(boxes.xyxy, boxes.conf)):
                    coords = box.cpu().numpy().astype(int)
                    print(f"   [{i}] Box: {coords}, Confidence: {conf.item():.2%}")
                
                # Get best detection
                best_idx = boxes.conf.argmax().item()
                box = boxes.xyxy[best_idx].cpu().numpy().astype(int)
                conf = boxes.conf[best_idx].item()
                x1, y1, x2, y2 = box
                
                print(f"\n   📍 Best plate location: ({x1}, {y1}) to ({x2}, {y2})")
                print(f"   🎯 Confidence: {conf:.2%}")
                
                # Crop the plate
                plate_crop = image[y1:y2, x1:x2]
                used_yolo = True
                
                # Save cropped plate for inspection
                cv2.imwrite("detected_plate.jpg", plate_crop)
                print(f"   💾 Saved cropped plate to: detected_plate.jpg")
            else:
                print("⚠️ No plates detected by YOLO")
        else:
            print("⚠️ No detection results")
            
    except ImportError:
        print("❌ YOLO not available (ultralytics not installed)")
    except Exception as e:
        print(f"❌ YOLO error: {e}")
        import traceback
        traceback.print_exc()
    
    # If no plate detected by YOLO, manually crop the plate region
    # Based on the image: the yellow Audi's plate "NN 773" is at approximately:
    # - The plate is in the bottom center of the red bounding box
    # - Image is 640x360 (approx)
    if plate_crop is None or not used_yolo:
        print("\n🔄 Using manual crop based on known plate location...")
        # The plate "NN 773" is visible on the yellow Audi
        # Approximate coordinates: the plate is roughly at the front of the car
        # Looking at the image, the plate appears around:
        # x: 210-290, y: 240-265 (approximately)
        
        # More precise region targeting the license plate on the yellow Audi
        x1, y1, x2, y2 = int(w*0.32), int(h*0.65), int(w*0.45), int(h*0.75)
        print(f"   Manual crop region: ({x1}, {y1}) to ({x2}, {y2})")
        
        plate_crop = image[y1:y2, x1:x2]
        cv2.imwrite("detected_plate.jpg", plate_crop)
        print(f"   💾 Saved manual crop to: detected_plate.jpg")
        print(f"   📏 Crop size: {plate_crop.shape[1]}x{plate_crop.shape[0]} pixels")
    
    # ===== Stage 2: OCR with PaddleOCR =====
    print("\n" + "-" * 40)
    print("Stage 2: Text Recognition (PaddleOCR)")
    print("-" * 40)
    
    try:
        from paddleocr import PaddleOCR
        
        print("🔄 Initializing PaddleOCR...")
        ocr = PaddleOCR(lang='en')
        print("✅ PaddleOCR initialized")
        
        # List available methods
        methods = [m for m in dir(ocr) if not m.startswith('_')]
        print(f"\n📋 Available methods: {methods}")
        
        # Resize plate for better OCR
        if plate_crop is not None and plate_crop.size > 0:
            # Resize 3x for better OCR
            plate_resized = cv2.resize(plate_crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
            cv2.imwrite("plate_resized.jpg", plate_resized)
            
            print(f"\n🔍 Running OCR on plate crop ({plate_resized.shape[1]}x{plate_resized.shape[0]} pixels)...")
            
            # Use the ocr method
            result = ocr.ocr(plate_resized, cls=True)
            
            print("\n📊 OCR Results on Plate Crop:")
            if result and result[0]:
                for i, line in enumerate(result[0]):
                    if line and len(line) >= 2:
                        text = line[1][0]
                        score = line[1][1]
                        print(f"   [{i+1}] Text: '{text}' (Confidence: {score:.2%})")
                
                # Combine all text
                all_texts = []
                for line in result[0]:
                    if line and len(line) >= 2 and line[1][1] > 0.5:
                        all_texts.append(line[1][0])
                
                if all_texts:
                    combined = " ".join(all_texts)
                    import re
                    clean_text = re.sub(r'[^A-Z0-9 ]', '', combined.upper())
                    print(f"\n🏷️  DETECTED LICENSE PLATE: {clean_text}")
            else:
                print("   ⚠️ No text detected in plate crop")
                
            # Also try on the original full image
            print("\n🔍 Running OCR on FULL IMAGE to find all text...")
            full_result = ocr.ocr(image, cls=True)
            
            if full_result and full_result[0]:
                print("\n📊 All text found in full image:")
                for i, line in enumerate(full_result[0]):
                    if line and len(line) >= 2:
                        text = line[1][0]
                        score = line[1][1]
                        if score > 0.5:  # Show all somewhat confident detections
                            print(f"   [{i+1}] '{text}' (Confidence: {score:.2%})")
            else:
                print("   ⚠️ No text detected in full image")
        else:
            print("❌ No plate crop available for OCR")
            
    except ImportError as e:
        print(f"❌ PaddleOCR not available: {e}")
    except Exception as e:
        print(f"❌ PaddleOCR error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
