import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # Use absolute path for database to avoid relative path issues
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'trafficai.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app/static/uploads')
    VIOLATIONS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app/static/violations')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max upload
    USE_GPU = os.environ.get('USE_GPU', 'auto')  # 'auto', 'true', or 'false'
    
    # Traffic Analysis Configuration
    SPEED_LIMIT = float(os.environ.get('SPEED_LIMIT', 60.0))  # km/h
    PIXELS_PER_METER = float(os.environ.get('PIXELS_PER_METER', 40.0))  # Calibration value

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Use in-memory DB for tests

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
