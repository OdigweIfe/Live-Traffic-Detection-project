from flask import Blueprint, render_template, request, current_app, abort
from app import db
from sqlalchemy import inspect, text

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
def admin_dashboard():
    """Admin dashboard showing list of tables and selected table data."""
    # Get all tables
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    selected_table = request.args.get('table')
    table_data = []
    columns = []
    
    if selected_table:
        if selected_table not in tables:
            abort(404)
            
        # Get columns
        columns_info = inspector.get_columns(selected_table)
        columns = [c['name'] for c in columns_info]
        
        # Get data (raw SQL for flexibility with any table)
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text(f"SELECT * FROM {selected_table} LIMIT 100"))
                table_data = [dict(row._mapping) for row in result]
        except Exception as e:
            current_app.logger.error(f"Error fetching table data: {e}")
            
    return render_template('admin.html', 
                          tables=tables, 
                          selected_table=selected_table,
                          columns=columns,
                          data=table_data)

@admin_bp.route('/admin/add', methods=['POST'])
def add_record():
    """Add a new record to a specific table."""
    table_name = request.form.get('table_name')
    if not table_name:
        return {'status': 'error', 'message': 'No table name provided'}, 400
    
    try:
        from app import models
        # Map table names to model classes
        model_map = {
            'owners': models.Owner,
            'vehicles': models.Vehicle,
            'traffic_officers': models.TrafficOfficer,
            'cameras': models.Camera,
            'violations': models.Violation
        }
        
        model_class = model_map.get(table_name)
        if not model_class:
            return {'status': 'error', 'message': f'No model found for table {table_name}'}, 400
        
        # Build object from form data
        data = {}
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns(table_name) if c['name'] != 'id' and c['name'] != 'created_at']
        
        for col in columns:
            val = request.form.get(col)
            if val:
                data[col] = val
                
        new_record = model_class(**data)
        db.session.add(new_record)
        db.session.commit()
        
        return {'status': 'success', 'message': f'Record added to {table_name}!'}
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding record to {table_name}: {e}")
        return {'status': 'error', 'message': str(e)}, 500

import os
import glob
import shutil

@admin_bp.route('/admin/reset', methods=['POST'])
def reset_db():
    """Clear all data from the database and delete generated files."""
    try:
        from app.models import Violation
        
        # 1. Clear Database
        num_deleted = db.session.query(Violation).delete()
        db.session.commit()
        
        # 2. Clear Files (Processed Videos & Evidence)
        cleaned_files = 0
        folders_to_clear = ['processed', 'violations']
        
        for folder in folders_to_clear:
            folder_path = os.path.join(current_app.static_folder, folder)
            if os.path.exists(folder_path):
                # Delete all files in the folder (keep the folder itself)
                files = glob.glob(os.path.join(folder_path, '*'))
                for f in files:
                    try:
                        if os.path.isfile(f):
                            os.remove(f)
                            cleaned_files += 1
                    except Exception as e:
                        current_app.logger.error(f"Error deleting file {f}: {e}")
            
        current_app.logger.info(f"System reset: {num_deleted} DB records, {cleaned_files} files removed.")
        return {'status': 'success', 'message': f'System Reset Complete! {num_deleted} records and {cleaned_files} files removed.'}
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error resetting database: {e}")
        return {'status': 'error', 'message': str(e)}, 500
