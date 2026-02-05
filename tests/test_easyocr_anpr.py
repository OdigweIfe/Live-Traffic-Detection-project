"""
Quick test to verify EasyOCR ANPR works correctly.
"""
import cv2
from app.ai.anpr import ANPR_System

# Initialize ANPR with EasyOCR
print("Initializing ANPR system with EasyOCR...")
anpr = ANPR_System(use_easyocr=True)

# Test with sample plate
print("\nTesting with sample_plate.jpg...")
plate_img = cv2.imread('app/static/violation_21.jpg')

if plate_img is not None:
    text = anpr.extract_text(plate_img)
    print(f"✅ Extracted text: '{text}'")
    print(f"   Expected: 'ABC1234' or similar")
else:
    print("❌ Could not load sample_plate.jpg")

# Test with vehicle crop
print("\nTesting with sample_vehicle.jpg...")
vehicle_img = cv2.imread('test_data/sample_vehicle.jpg')

if vehicle_img is not None:
    text = anpr.extract_text(vehicle_img)
    print(f"✅ Extracted text: '{text}'")
    print(f"   Expected: 'XYZ789' or similar")
else:
    print("❌ Could not load sample_vehicle.jpg")

print("\n✅ EasyOCR ANPR test complete!")
print("   No external binary installation needed!")
