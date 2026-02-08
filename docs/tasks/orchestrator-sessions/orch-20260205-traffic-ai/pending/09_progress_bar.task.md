# Task: Fix Progress Bar Updates

**Priority:** P1 (Bug Fix)  
**Effort:** Small (~10 min)

## Problem
Progress bar stays at 0% even though frames are processing.

## Root Cause
Server sends `progress` in frame data, but progress bar may not be updating correctly.

## Solution
Verify and fix progress bar binding.

## Implementation

### 1. Verify server sends progress
In `sockets.py` line ~363:
```python
progress = int((frame_idx / total_frames) * 100)
```
✅ This looks correct.

### 2. Check client receives and updates
In `live_processing.html`:
```javascript
socket.on('frame', (data) => {
    // ... existing code
    progressBar.style.width = data.progress + '%';
    const progressText = document.getElementById('progress-text');
    if (progressText) progressText.textContent = data.progress + '%';
});
```

### 3. Debug check
Add console log temporarily:
```javascript
console.log('Progress:', data.progress);
```

## Acceptance Criteria
- [ ] Progress bar fills from 0% to 100%
- [ ] Progress text updates
- [ ] Matches frame count ratio
