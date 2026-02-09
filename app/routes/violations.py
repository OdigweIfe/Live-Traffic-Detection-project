from app.models import Violation
from sqlalchemy import desc
from app.routes import violations_bp
from flask import jsonify, render_template, current_app
import os

@violations_bp.route('/api/violations', methods=['GET'])
def get_violations():
    violations = Violation.query.order_by(desc(Violation.timestamp)).all()
    return jsonify({'violations': [v.to_dict() for v in violations]}), 200

@violations_bp.route('/violation/<int:violation_id>')
def violation_detail(violation_id):
    violation = Violation.query.get_or_404(violation_id)
    
    # Check if video file actually exists and is valid
    if violation.video_path:
        video_full_path = os.path.join(current_app.root_path, 'static', violation.video_path)
        if not os.path.exists(video_full_path) or os.path.getsize(video_full_path) < 1000:
            # If video file is missing or too small (corrupt), fallback to image
            violation.video_path = None
            
    return render_template('violation_detail.html', violation=violation)
