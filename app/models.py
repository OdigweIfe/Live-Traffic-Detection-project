from app import db
from datetime import datetime

class Violation(db.Model):
    __tablename__ = 'violations'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, index=True)
    violation_type = db.Column(db.String(50), nullable=False, index=True)
    vehicle_type = db.Column(db.String(50))
    license_plate = db.Column(db.String(20), index=True)
    speed_kmh = db.Column(db.Float)
    image_path = db.Column(db.String(255))
    location = db.Column(db.String(100))
    signal_state = db.Column(db.String(20)) # "red", "yellow", "green"
    
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
            'frame_number': self.frame_number,
            'video_fps': self.video_fps,
            'video_path': self.video_path
        }
    
    @property
    def video_timestamp_seconds(self):
        """Calculate the timestamp in seconds for video seek."""
        if self.frame_number and self.video_fps and self.video_fps > 0:
            return self.frame_number / self.video_fps
        return 0
