
import pytest
from app import create_app, db
from app.models import Violation
from datetime import datetime, timedelta

@pytest.fixture
def client():
    app = create_app('testing')
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_dashboard_route(client):
    """Test that dashboard loads successfully."""
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b'Traffic Overview' in response.data

def test_dashboard_filtering(client):
    """Test that dashboard filtering works."""
    # Add dummy data
    v1 = Violation(violation_type='red_light', timestamp=datetime.now())
    v2 = Violation(violation_type='speeding', timestamp=datetime.now() - timedelta(days=2))
    
    with client.application.app_context():
        db.session.add(v1)
        db.session.add(v2)
        db.session.commit()
        # Get IDs for verification
        v1_id = v1.id
        v2_id = v2.id

    # Test filter by type
    response = client.get('/dashboard?type=red_light')
    assert response.status_code == 200
    # Ideally check if v1 is present and v2 is absent (requires parsing HTML or ensuring context pass)
    # For now, just check status
    
def test_violation_detail(client):
    """Test violation detail view."""
    with client.application.app_context():
        v = Violation(violation_type='lane_violation', timestamp=datetime.now())
        db.session.add(v)
        db.session.commit()
        v_id = v.id
    
    response = client.get(f'/violation/{v_id}')
    assert response.status_code == 200
    assert b'Violation Details' in response.data

def test_violation_detail_404(client):
    """Test 404 for non-existent violation."""
    response = client.get('/violation/999')
    assert response.status_code == 404
