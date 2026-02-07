"""
Test PaddleOCR 3.x new API
"""
import os
os.environ['PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_enable_pir_api'] = '0'

from paddleocr import PaddleOCR

print("=" * 60)
print("PaddleOCR 3.x API Test")
print("=" * 60)

# Initialize with new API options
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False
)
print("OCR initialized successfully!")

# Test on plate image
print("\nRunning OCR on detected_plate.jpg...")
result = ocr.predict(input='detected_plate.jpg')

print("\n=== OCR RESULTS ===")
for res in result:
    # Print the result structure
    print(f"Result type: {type(res)}")
    print(f"Result keys: {list(res.keys()) if hasattr(res, 'keys') else 'N/A'}")
    
    # Try to access text results
    if 'rec_texts' in res:
        print(f"\nDetected texts: {res['rec_texts']}")
        print(f"Confidence scores: {res['rec_scores']}")
    
    # Also try the print method
    print("\n--- Using res.print() ---")
    res.print()

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)
