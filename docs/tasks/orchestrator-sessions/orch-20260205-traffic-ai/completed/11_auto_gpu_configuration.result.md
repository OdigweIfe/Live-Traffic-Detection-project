# Result: Auto-Configurable GPU Acceleration for ANPR

**Status:** ✅ Completed
**Date:** 2026-02-08

## Summary
Implemented dynamic GPU selection logic for the ANPR system (PaddleOCR and EasyOCR). The system now intelligently detects available NVIDIA GPUs and configures the OCR engines accordingly. Setup scripts have been updated to optionally install GPU-optimized dependencies.

## Changes

### 1. Configuration (`config.py`)
- Added `USE_GPU` configuration variable, reading from the environment variable `USE_GPU` (defaults to 'auto').

### 2. ANPR System (`app/ai/anpr.py`)
- **GPU Detection Logic:** 
  - Checks `USE_GPU` env var ('true', 'false', 'auto').
  - If 'auto', checks `torch.cuda.is_available()` to determine capability.
- **Initialization:**
  - `PaddleOCR` initialized with `use_gpu=should_use_gpu`.
  - `EasyOCR` initialized with `gpu=should_use_gpu`.
- **Logging:** Added logs to indicate which mode (CPU/GPU) is active at startup.

### 3. Setup Scripts
- **`setup.ps1` (Windows):**
  - Added detection for NVIDIA GPUs using WMI (`Win32_VideoController`).
  - Prompts user to install `paddlepaddle-gpu` if an NVIDIA GPU is found.
  - Automatically uninstalls cpu `paddlepaddle` before installing gpu version if requested.
- **`setup.sh` (Linux/macOS):**
  - Added detection using `nvidia-smi`.
  - Prompts user to install `paddlepaddle-gpu` if detected.

## Verification
- **CPU Mode:** Default behavior if no GPU is present or `USE_GPU=false`.
- **GPU Mode:** Activated if NVIDIA GPU is present and user accepts installation (or manually sets `USE_GPU=true`).
- **Override:** Users can force CPU mode by setting `USE_GPU=false` in `.env`.

## Next Steps
- Verify on a machine with an actual NVIDIA GPU to ensure `paddlepaddle-gpu` installation works seamlessly with the existing environment.
