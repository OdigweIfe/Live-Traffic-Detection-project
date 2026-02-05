from flask import Blueprint

upload_bp = Blueprint('upload', __name__)
violations_bp = Blueprint('violations', __name__)
dashboard_bp = Blueprint('dashboard', __name__)

from app.routes import upload, violations, dashboard
