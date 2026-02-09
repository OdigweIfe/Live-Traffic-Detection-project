from app import db
from datetime import datetime

class Owner(db.Model):
    __tablename__ = 'owners'
    id = db.Column(db.Integer, primary_key=True)
    owner_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    vehicles = db.relationship('Vehicle', backref='owner', lazy=True)

class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    id = db.Column(db.Integer, primary_key=True)
    license_plate = db.Column(db.String(20), unique=True, nullable=False, index=True)
    vehicle_type = db.Column(db.String(50))
    owner_id = db.Column(db.Integer, db.ForeignKey('owners.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    violations = db.relationship('Violation', backref='vehicle', lazy=True)

class TrafficOfficer(db.Model):
    __tablename__ = 'traffic_officers'
    id = db.Column(db.Integer, primary_key=True)
    officer_name = db.Column(db.String(100), nullable=False)
    badge_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100))
    role = db.Column(db.String(20), default='officer') # admin, officer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    violations = db.relationship('Violation', backref='officer', lazy=True)

class Camera(db.Model):
    __tablename__ = 'cameras'
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='active') # active, inactive, maintenance
    stream_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    violations = db.relationship('Violation', backref='camera', lazy=True)

class Violation(db.Model):
    __tablename__ = 'violations'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, index=True)
    violation_type = db.Column(db.String(50), nullable=False, index=True)
    vehicle_type = db.Column(db.String(50))
    license_plate = db.Column(db.String(20), index=True) # Keep for legacy/direct access
    speed_kmh = db.Column(db.Float)
    image_path = db.Column(db.String(255))
    location = db.Column(db.String(100))
    signal_state = db.Column(db.String(20)) # "red", "yellow", "green"
    
    # Relationships
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'))
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'))
    officer_id = db.Column(db.Integer, db.ForeignKey('traffic_officers.id'))
    
    # Video playback fields
    frame_number = db.Column(db.Integer)  # Frame where violation occurred
    video_fps = db.Column(db.Float)  # FPS of the source video
    video_path = db.Column(db.String(255))  # Path to processed video

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'violation_type': self.violation_type,
            'vehicle_type': self.vehicle_type,
            'license_plate': self.license_plate,
            'speed_kmh': self.speed_kmh,
            'image_path': self.image_path,
            'location': self.location,
            'signal_state': self.signal_state,
            'vehicle_id': self.vehicle_id,
            'camera_id': self.camera_id,
            'officer_id': self.officer_id,
            'frame_number': self.frame_number,
            'video_fps': self.video_fps,
            'video_path': self.video_path,
            'owner_name': self.vehicle.owner.owner_name if self.vehicle and self.vehicle.owner else None
        }
    
    @property
    def video_timestamp_seconds(self):
        """Calculate the timestamp in seconds for video seek."""
        if self.frame_number and self.video_fps and self.video_fps > 0:
            return self.frame_number / self.video_fps
        return 0
