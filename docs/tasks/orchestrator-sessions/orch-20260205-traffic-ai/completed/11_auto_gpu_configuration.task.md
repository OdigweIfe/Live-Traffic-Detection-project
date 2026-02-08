# Task: Implement Auto-Configurable GPU Acceleration for ANPR

**Priority:** P2 (Optimization)  
**Effort:** Medium (~45 min)

## Objective
Make the ANPR system (PaddleOCR and EasyOCR) intelligently select GPU acceleration if available, while gracefully falling back to CPU on systems without NVIDIA hardware. Ensure this behavior is configurable.

## Current State
- **Vehicle Detection (YOLO):** Already supports dynamic GPU/CPU selection (`torch.cuda.is_available()`).
- **PaddleOCR:** Uses `paddlepaddle` (CPU package). Needs `paddlepaddle-gpu` to support GPU, but standard `paddlepaddle` is installed.
- **EasyOCR:** Hardcoded to `gpu=False` in `app/ai/anpr.py`.

## Requirements

### 1. Library Management
- [ ] Update `requirements.txt` or setup script to install `paddlepaddle-gpu` if a GPU is detected, or ensure the package structure supports both.
- *Note:* `paddlepaddle-gpu` usually includes CPU kernels, so it serves as a superset. However, size might be an issue. A robust "install script" check (like in `setup.ps1` / `setup.sh`) is preferred over just hardcoding it in `requirements.txt`.

### 2. Code Changes (`app/ai/anpr.py`)
- [ ] Remove `gpu=False` hardcoding for EasyOCR.
- [ ] Implement a dynamic check for GPU availability (similar to YOLO's check).
- [ ] Allow override via environment variable (e.g., `USE_GPU=true/false/auto`).

### 3. Configuration
- [ ] Add `USE_GPU` to `.env` (default: `auto`).
- [ ] Ensure `config.py` loads this preference.

## Implementation Plan (Draft)

1.  **Modify `app/ai/anpr.py`**:
    ```python
    import torch
    import os
    
    # ... inside __init__ ...
    use_gpu_env = os.getenv('USE_GPU', 'auto').lower()
    
    # Determine actual capability
    has_cuda = torch.cuda.is_available() # or similar check for Paddle/EasyOCR
    
    should_use_gpu = False
    if use_gpu_env == 'true':
        should_use_gpu = True
    elif use_gpu_env == 'auto':
        should_use_gpu = has_cuda
        
    # Initialize EasyOCR
    self.easyocr_reader = easyocr.Reader(['en'], gpu=should_use_gpu)
    
    # PaddleOCR usually auto-selects if gpu package is present, 
    # but can be forced via `use_gpu` param.
    self.paddle_ocr = PaddleOCR(..., use_gpu=should_use_gpu)
    ```

2.  **Update Setup Scripts**:
    - Update `setup.ps1` and `setup.sh` to optionally install `paddlepaddle-gpu` if an NVIDIA GPU is detected, or provide a flag `--gpu`.

## Acceptance Criteria
- [ ] System works on a machine *with* GPU (uses CUDA).
- [ ] System works on a machine *without* GPU (uses CPU).
- [ ] User can force CPU mode via `.env` even if GPU exists.
