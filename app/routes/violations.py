from app.models import Violation
from sqlalchemy import desc
from app.routes import violations_bp
from flask import jsonify, render_template

@violations_bp.route('/api/violations', methods=['GET'])
def get_violations():
    violations = Violation.query.order_by(desc(Violation.timestamp)).all()
    return jsonify({'violations': [v.to_dict() for v in violations]}), 200

@violations_bp.route('/violation/<int:violation_id>')
def violation_detail(violation_id):
    violation = Violation.query.get_or_404(violation_id)
    return render_template('violation_detail.html', violation=violation)
