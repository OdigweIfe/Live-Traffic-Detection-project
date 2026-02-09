from flask import Blueprint, render_template, request, send_file, current_app, flash, redirect, url_for
from app.models import Violation, Vehicle, Camera, TrafficOfficer, Owner
from app import db
from datetime import datetime, timedelta
import pandas as pd
import io
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
def index():
    """Reports dashboard with filtering and summary."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    violation_type = request.args.get('violation_type')
    
    query = Violation.query
    
    if start_date:
        query = query.filter(Violation.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        # Add 1 day to end_date to include all of the end day
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(Violation.timestamp < end_dt)
    if violation_type:
        query = query.filter(Violation.violation_type == violation_type)
        
    violations = query.order_by(Violation.timestamp.desc()).all()
    
    # Calculate stats for the dashboard
    total_violations = len(violations)
    most_common_type = "N/A"
    avg_speed = 0
    
    if violations:
        # Most common type
        from collections import Counter
        type_counts = Counter(v.violation_type for v in violations)
        most_common_type = type_counts.most_common(1)[0][0]
        
        # Avg speed
        speeds = [v.speed_kmh for v in violations if v.speed_kmh is not None]
        if speeds:
            avg_speed = sum(speeds) / len(speeds)
            
    # Types for filter dropdown
    types = db.session.query(Violation.violation_type).distinct().all()
    types = [t[0] for t in types]
    
    return render_template('reports.html', 
                          violations=violations, 
                          types=types,
                          stats={
                              'total': total_violations,
                              'most_common': most_common_type,
                              'avg_speed': round(avg_speed, 1)
                          },
                          filters={'start_date': start_date, 'end_date': end_date, 'violation_type': violation_type})

@reports_bp.route('/reports/export', methods=['POST'])
def export_report():
    """Export filtered violations to PDF or CSV."""
    export_format = request.form.get('format', 'csv')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    violation_type = request.form.get('violation_type')
    
    query = Violation.query
    if start_date:
        query = query.filter(Violation.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(Violation.timestamp < end_dt)
    if violation_type:
        query = query.filter(Violation.violation_type == violation_type)
        
    violations = query.order_by(Violation.timestamp.desc()).all()
    
    if not violations:
        flash("No data found for the selected filters.", "warning")
        return redirect(url_for('reports.index'))

    if export_format == 'csv':
        data = []
        for v in violations:
            data.append({
                'ID': v.id,
                'Timestamp': v.timestamp,
                'Type': v.violation_type,
                'License Plate': v.license_plate,
                'Vehicle Type': v.vehicle_type,
                'Speed (km/h)': v.speed_kmh,
                'Location': v.location,
                'Owner': v.vehicle.owner.owner_name if v.vehicle and v.vehicle.owner else "N/A"
            })
        df = pd.DataFrame(data)
        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(output, mimetype='text/csv', as_attachment=True, download_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

    elif export_format == 'pdf':
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        elements.append(Paragraph("Traffic Violation Report", styles['Title']))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Table Data
        data = [['Date', 'Type', 'Plate', 'Owner']]
        for v in violations:
            owner = v.vehicle.owner.owner_name if v.vehicle and v.vehicle.owner else "N/A"
            data.append([
                v.timestamp.strftime('%Y-%m-%d %H:%M'),
                v.violation_type,
                v.license_plate,
                owner
            ])
            
        t = Table(data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
        
        # Evidence Details
        elements.append(Spacer(1, 24))
        elements.append(Paragraph("Evidence Images", styles['Heading2']))
        
        for v in violations[:10]: # Limit to first 10 for performance/size
            if v.image_path:
                full_path = os.path.join(current_app.static_folder, v.image_path.replace('static/', ''))
                if os.path.exists(full_path):
                    elements.append(Paragraph(f"ID: {v.id} - {v.license_plate} ({v.violation_type})", styles['Normal']))
                    try:
                        img = Image(full_path, width=400, height=225)
                        elements.append(img)
                    except:
                        elements.append(Paragraph("[Image Error]", styles['Normal']))
                    elements.append(Spacer(1, 12))

        doc.build(elements)
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
