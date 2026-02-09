# Task: Fix WebSocket Session Persistence

**Priority:** P1 (Bug Fix)  
**Effort:** Medium (~30 min)

## Problem
When user switches tabs, WebSocket disconnects. Returning triggers a NEW processing session instead of resuming the existing one.

## Root Cause
- No server-side session tracking by video path
- Client reconnects and re-emits `start_processing` with same video
- Server starts duplicate processing

## Solution
Implement session persistence with duplicate detection.

## Implementation

### 1. Update `sockets.py`

```python
# Add near top
active_video_sessions = {}  # {video_path: {sid, progress, status}}

@socketio.on('start_processing')
def handle_start_processing(data):
    video_path = data.get('video_path')
    
    # Check if already processing this video
    if video_path in active_video_sessions:
        existing = active_video_sessions[video_path]
        if existing['status'] == 'processing':
            emit('resume_session', {
                'message': 'Resuming existing session',
                'progress': existing['progress']
            })
            return
    
    # ... existing processing logic
    active_video_sessions[video_path] = {
        'sid': sid,
        'progress': 0,
        'status': 'processing'
    }
```

### 2. Update client to handle `resume_session`

```javascript
socket.on('resume_session', (data) => {
    console.log('Resuming:', data);
    showStatus(`🔄 Resumed at ${data.progress}%`, 'info');
});
```

## Acceptance Criteria
- [x] Switching tabs doesn't restart processing
- [x] Returning shows current progress
- [x] Only one session per video at a time

## Result
Implemented session persistence using Flask-SocketIO Rooms.
- **Server:** Added `active_video_sessions` keyed by video path. Clients joining the same video path are added to a shared Room. The processing thread emits updates to the Room instead of a specific SID.
- **Client:** Added handler for `resume_session` to display resume status without restarting.
- **Verification:** Verified using a test script that simulates a second client connecting to an active session; confirmed it receives `resume_session` and joins the existing room without triggering a new processing thread.