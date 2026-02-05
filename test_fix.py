"""
Test Fixed ANPR System
Verifies that the ANPR_System class now correctly handles PaddleOCR 3.x API.
"""
import os
import sys
import cv2
import traceback

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

# Import the ANPR System
try:
    from app.ai.anpr import ANPR_System
except ImportError:
    print("Failed to import ANPR_System. check python path")
    sys.exit(1)

def test_anpr():
    print("=" * 60)
    print("Testing Fixed ANPR System")
    print("=" * 60)
    
    # Initialize ANPR
    print("\n1. Initializing ANPR System...")
    try:
        anpr = ANPR_System()
        if anpr.use_paddleocr:
            print("✅ PaddleOCR initialized successfully")
        else:
            print("⚠️ PaddleOCR not initialized (using fallback?)")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        traceback.print_exc()
        return

    # Load test image
    image_path = os.path.join("app", "static", "violations", "violation_21.jpg")
    if not os.path.exists(image_path):
        print(f"❌ Test image not found: {image_path}")
        # Try finding any violation image
        import glob
        violations = glob.glob("app/static/violations/*.jpg")
        if violations:
            image_path = violations[0]
            print(f"🔄 Using alternative image: {image_path}")
        else:
            return

    print(f"\n2. Testing on image: {image_path}")
    image = cv2.imread(image_path)
    if image is None:
        print("❌ Could not read image")
        return

    # Run extraction
    print("\n3. Running text extraction...")
    try:
        # We can test the full pipeline or just the text extraction if we have a crop
        # Let's try full pipeline first
        text = anpr.extract_text(image)
        print(f"\n🏷️  Result: '{text}'")
        
        if text and text != "N/A":
            print("✅ SUCCESSS: Plate detected and read!")
        else:
            print("⚠️ Plate not detected or read. Testing manual crop...")
            
            # Try manual crop to test OCR specifically
            h, w = image.shape[:2]
            # Manual crop for violation_21.jpg (Yellow Audi)
            x1, y1, x2, y2 = int(w*0.32), int(h*0.65), int(w*0.45), int(h*0.75)
            manual_crop = image[y1:y2, x1:x2]
            
            ocr_text = anpr.extract_text_from_plate(manual_crop)
            print(f"🏷️  Manual Crop OCR Result: '{ocr_text}'")
            
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_anpr()
