from flask import render_template, request, abort
from app.models import Violation
from app import db
from sqlalchemy import desc
from app.routes import dashboard_bp
from datetime import datetime, timedelta

@dashboard_bp.route('/dashboard')
def view_dashboard():
    query = Violation.query

    # Filters
    v_type = request.args.get('type')
    if v_type:
        query = query.filter(Violation.violation_type.ilike(f'%{v_type}%'))

    start_date = request.args.get('start_date')
    if start_date:
        try:
            sd = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Violation.timestamp >= sd)
        except ValueError:
            pass
    
    end_date = request.args.get('end_date')
    if end_date:
        try:
            ed = datetime.strptime(end_date, '%Y-%m-%d')
            # Set to end of day
            ed = ed.replace(hour=23, minute=59, second=59)
            query = query.filter(Violation.timestamp <= ed)
        except ValueError:
            pass

    plate = request.args.get('plate')
    if plate:
        query = query.filter(Violation.license_plate.ilike(f'%{plate}%'))

    # Fetch recent violations (filtered)
    violations = query.order_by(desc(Violation.timestamp)).limit(50).all()
    
    # Calculate global stats (unfiltered)
    total = Violation.query.count()
    red_light = Violation.query.filter(Violation.violation_type.ilike('%red%')).count()
    speeding = Violation.query.filter(Violation.violation_type.ilike('%speed%')).count()
    
    return render_template('dashboard.html', 
                          violations=violations,
                          total_violations=total,
                          red_light_violations=red_light,
                          speeding_violations=speeding)

@dashboard_bp.route('/violation/<int:violation_id>/dismiss', methods=['POST'])
def dismiss_violation(violation_id):
    """Dismiss/cancel a violation (false positive)."""
    import os
    from flask import current_app, flash, redirect, url_for
    
    violation = Violation.query.get_or_404(violation_id)
    
    # Delete the snapshot image if it exists
    if violation.image_path:
        image_full_path = os.path.join(current_app.static_folder, violation.image_path)
        if os.path.exists(image_full_path):
            os.remove(image_full_path)
    
    # Delete from database
    db.session.delete(violation)
    db.session.commit()
    
    flash(f'Violation #{violation_id} dismissed as false positive', 'success')
    return redirect(url_for('dashboard.view_dashboard'))
