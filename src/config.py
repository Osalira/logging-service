import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:osalocal_database@localhost:5432/db_daytrading_logs')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask Configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')  # Change in production
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.getenv('LOG_FILE', 'logs/daytrading.log')
    
    # Service Configuration
    MAX_LOG_AGE_DAYS = int(os.getenv('MAX_LOG_AGE_DAYS', '30'))  # How long to keep logs
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '1000'))  # Number of logs to process in batch
    
    # API Configuration
    API_VERSION = 'v1'
    API_PREFIX = f'/api/{API_VERSION}'
    
    # Retention Policy
    LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', '90'))  # Days to keep logs in DB
    
    # Service URLs
    AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:5000')
    TRADING_SERVICE_URL = os.getenv('TRADING_SERVICE_URL', 'http://localhost:8000')
    MATCHING_ENGINE_URL = os.getenv('MATCHING_ENGINE_URL', 'http://localhost:8080') 