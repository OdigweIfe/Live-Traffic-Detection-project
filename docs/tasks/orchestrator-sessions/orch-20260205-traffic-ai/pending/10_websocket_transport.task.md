# Task: Fix WebSocket Transport (eventlet)

**Priority:** P2 (Production Stability)  
**Effort:** Small (~15 min)

## Problem
```
WebSocket connection failed: Invalid frame header
```
WebSocket upgrade fails, falling back to HTTP polling (slower, reconnects frequently).

## Root Cause
Flask-SocketIO in `threading` mode doesn't have proper WebSocket support.

## Solution
Install `eventlet` for proper async WebSocket handling.

## Implementation

### 1. Install eventlet
```bash
pip install eventlet
```

### 2. Update requirements.txt
```
eventlet>=0.33.0
```

### 3. Verify async mode
After restart, should see:
```
✅ SocketIO Async Mode: eventlet
```

### 4. Alternative: gevent
If eventlet causes issues:
```bash
pip install gevent gevent-websocket
```

## Acceptance Criteria
- [ ] No "Invalid frame header" errors
- [ ] Async mode shows `eventlet` or `gevent`
- [ ] WebSocket transport works (no polling fallback)
