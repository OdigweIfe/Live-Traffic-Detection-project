# Task: Add Elapsed Time Counter

**Priority:** P1 (UX Enhancement)  
**Effort:** Small (~15 min)

## Problem
No visual indicator of how long processing has been running.

## Solution
Add a timer display showing elapsed time (MM:SS format) next to the progress bar.

## Implementation

### 1. Update `live_processing.html`
```javascript
// Add to script section
let startTime = null;
let timerInterval = null;

socket.on('video_info', (data) => {
    startTime = Date.now();
    timerInterval = setInterval(updateTimer, 1000);
    // ... existing code
});

function updateTimer() {
    if (!startTime) return;
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const mins = Math.floor(elapsed / 60).toString().padStart(2, '0');
    const secs = (elapsed % 60).toString().padStart(2, '0');
    document.getElementById('elapsed-time').textContent = `${mins}:${secs}`;
}

socket.on('processing_complete', () => {
    clearInterval(timerInterval);
    // ... existing code
});
```

### 2. Add HTML element
```html
<span id="elapsed-time" class="text-slate-500 font-mono">00:00</span>
```

## Acceptance Criteria
- [x] Timer starts when processing begins
- [x] Shows MM:SS format
- [x] Stops when complete