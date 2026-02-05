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

@admin_bp.route('/admin/reset', methods=['POST'])
def reset_db():
    """Clear all data from the database."""
    try:
        from app.models import Violation
        
        # Clear specific tables (safest approach)
        num_deleted = db.session.query(Violation).delete()
        db.session.commit()
        
        # If we wanted to clear ALL tables dynamically:
        # meta = db.metadata
        # for table in reversed(meta.sorted_tables):
        #     db.session.execute(table.delete())
        # db.session.commit()
            
        current_app.logger.info(f"Database cleared: {num_deleted} records deleted")
        return {'status': 'success', 'message': f'Database cleared! {num_deleted} records removed.'}
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error resetting database: {e}")
        return {'status': 'error', 'message': str(e)}, 500
