# Tesseract OCR Installation Guide

## What is Tesseract?
Tesseract is an open-source OCR (Optical Character Recognition) engine that TrafficAI uses to read license plate numbers from vehicle images.

## Current Status
- ✅ `pytesseract` Python wrapper installed
- ❌ Tesseract OCR binary **not installed**
- ⚠️ ANPR currently returns "N/A" for all plates (graceful fallback)

---

## Installation Instructions

### Windows Installation

#### Option 1: Using Installer (Recommended)

1. **Download Tesseract Installer**
   - Visit: https://github.com/UB-Mannheim/tesseract/wiki
   - Download the latest Windows installer (e.g., `tesseract-ocr-w64-setup-5.3.3.20231005.exe`)

2. **Run Installer**
   - Double-click the downloaded `.exe` file
   - **IMPORTANT:** During installation, note the installation path (default: `C:\Program Files\Tesseract-OCR\`)
   - Check "Add to PATH" if prompted

3. **Verify Installation**
   ```powershell
   tesseract --version
   ```
   Should output: `tesseract 5.x.x`

4. **Configure TrafficAI** (if not auto-detected)
   
   Edit `app/ai/anpr.py` and add this line in the `__init__` method:
   ```python
   import pytesseract
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

#### Option 2: Using Chocolatey (for advanced users)

```powershell
# Install Chocolatey package manager first (if not installed)
# Then run:
choco install tesseract

# Verify
tesseract --version
```

---

### Linux Installation

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install tesseract-ocr
tesseract --version
```

#### Fedora/RHEL
```bash
sudo dnf install tesseract
tesseract --version
```

---

### macOS Installation

```bash
# Using Homebrew
brew install tesseract

# Verify
tesseract --version
```

---

## Testing ANPR After Installation

### Step 1: Verify Tesseract Works

```powershell
# Test OCR on test image
tesseract test_data/sample_plate.jpg stdout
```

Should output text like: `ABC 1234`

### Step 2: Test TrafficAI ANPR

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run ANPR tests
pytest tests/test_anpr.py -v
```

Expected output: **10/10 tests passing** ✅

### Step 3: Test with Real Video

Upload a traffic video via the web interface and verify license plates are extracted:
1. Navigate to `http://localhost:5000`
2. Upload a video
3. Check violations dashboard
4. License plates should show actual text instead of "N/A"

---

## Troubleshooting

### Error: "tesseract is not recognized"

**Cause:** Tesseract not in PATH

**Solution:**
1. Add Tesseract to PATH manually:
   - Open System Properties → Environment Variables
   - Edit "Path" variable
   - Add: `C:\Program Files\Tesseract-OCR\`
   - Restart terminal

2. Or configure in code (see Option 1, step 4 above)

### Error: "Failed loading language 'eng'"

**Cause:** Language data files missing

**Solution:**
```powershell
# Reinstall Tesseract with language data
choco install tesseract --params "/Languages:eng"
```

### Low OCR Accuracy (\<50%)

**Common Causes:**
- Poor image quality (blur, low resolution)
- Incorrect ROI (plate not fully visible)
- Unusual plate font/style

**Solutions:**
- Improve camera resolution
- Adjust vehicle detection bounding boxes
- Fine-tune preprocessing in `app/ai/anpr.py`
- Train custom Tesseract model for specific plate format

---

## Alternative: EasyOCR (Optional)

If Tesseract accuracy is insufficient, consider EasyOCR:

```powershell
pip install easyocr
```

Modify `app/ai/anpr.py`:
```python
import easyocr

class ANPR_System:
    def __init__(self):
        self.reader = easyocr.Reader(['en'])  # Load English model
    
    def extract_text(self, plate_crop):
        results = self.reader.readtext(plate_crop)
        text = " ".join([res[1] for res in results])
        return self._clean_text(text)
```

---

## Quick Start (TL;DR)

```powershell
# 1. Download installer from:
# https://github.com/UB-Mannheim/tesseract/wiki

# 2. Install (default path: C:\Program Files\Tesseract-OCR\)

# 3. Restart terminal and verify:
tesseract --version

# 4. Test ANPR:
pytest tests/test_anpr.py -v

# 5. Process video and check license plates!
```

---

## Current Behavior Without Tesseract

- ✅ System works without crashes
- ✅ All violations detected (red light, speed, lane)
- ⚠️ License plates show "N/A"
- ✅ Database records created normally

**Installing Tesseract is optional but recommended for production use.**
