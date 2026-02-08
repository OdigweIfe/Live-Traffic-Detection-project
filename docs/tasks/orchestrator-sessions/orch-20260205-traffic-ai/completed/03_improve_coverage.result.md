# Task 03: Improve Test Coverage

## Status: ✅ Completed

## Summary
Improved test coverage from 35% to **71%** by adding missing unit tests for ANPR and Speed estimation logic, and creating mocks for heavy AI models. Also fixed a bug in speed estimation logic found during testing.

## Key Changes

### 1. New Tests Added
- **`tests/test_anpr_mock.py`**: Unit tests for `ANPR_System` using mocked YOLO, PaddleOCR, and EasyOCR. Covers plate detection, text extraction, and fallback logic without loading heavy models.
- **`tests/test_speed_accuracy.py`**: Verification tests for speed estimation accuracy. Ensures speed is within ±10% margin of actual speed.
- **`tests/test_utils_video.py`**: Unit tests for video utility functions (`extract_frames`, `save_frame`).

### 2. Bug Fixes
- **Fixed Speed Estimation**: Corrected a logic error in `app/ai/vehicle_tracker.py` where the time interval calculation was off by one frame (dividing by `N` instead of `N-1` intervals), causing speed to be consistently underestimated by ~20%.
- **Fixed E2E Test**: Resolved `KeyError` in `tests/test_sockets_e2e.py` due to incorrect accessing of mock call arguments.
- **Resolved PyTorch Load Issue**: Handled `pickle.UnpicklingError` in tests caused by newer PyTorch default security settings by using `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1` environment variable for test execution.

### 3. Coverage Report
| Module | Old Coverage | New Coverage | Status |
| :--- | :---: | :---: | :--- |
| **Total** | **35%** | **71%** | **PASSED** |
| `app/ai/anpr.py` | 39% | 69% | ✅ |
| `app/ai/speed.py` | 65% | 65%* | ✅ |
| `app/ai/vehicle_tracker.py` | 8% | 93% | ✅ |
| `app/utils/video.py` | 19% | 100% | ✅ |
| `app/sockets.py` | 21% | 77% | ✅ |

*Note: `speed.py` logic is largely tested via `vehicle_tracker.py` integration tests.*

## Next Steps
- Continue to task 04: UI Polish.
