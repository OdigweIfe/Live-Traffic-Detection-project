# PaddlePaddle environment fixes (must be set before any paddle imports)
import os
os.environ['FLAGS_use_mkldnn'] = '0'      # Disable broken MKLDNN optimization
os.environ['ONEDNN_MAX_CPU_ISA'] = 'SSE42'  # Forces a more stable instruction set
os.environ['FLAGS_enable_pir_api'] = '0'  # Use stable executor

from app import create_app, db, socketio
from app.models import Violation

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Violation': Violation}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print(f"✅ SocketIO Async Mode: {socketio.async_mode}")
    # Use socketio.run instead of app.run for WebSocket support
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
