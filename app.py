from flask import Flask
from src.routes.log_routes import log_bp
from src.config import Config
import logging
from logging.handlers import RotatingFileHandler
import os

def create_app():
    """Initialize and configure the Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)
    
    # Configure logging
    handler = RotatingFileHandler(
        Config.LOG_FILE,
        maxBytes=10000000,  # 10MB
        backupCount=10
    )
    handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
    app.logger.addHandler(handler)
    app.logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Register blueprints
    app.register_blueprint(log_bp, url_prefix=Config.API_PREFIX)
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}, 200
    
    return app

def init_db():
    """Initialize the database with required tables"""
    from sqlalchemy import create_engine, text
    
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    # Create log_entries table if it doesn't exist
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS log_entries (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                service VARCHAR(50) NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                user_id VARCHAR(50),
                details JSONB NOT NULL,
                level VARCHAR(20) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create indexes for better query performance
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_log_entries_timestamp ON log_entries (timestamp);
            CREATE INDEX IF NOT EXISTS idx_log_entries_service ON log_entries (service);
            CREATE INDEX IF NOT EXISTS idx_log_entries_event_type ON log_entries (event_type);
            CREATE INDEX IF NOT EXISTS idx_log_entries_user_id ON log_entries (user_id);
            CREATE INDEX IF NOT EXISTS idx_log_entries_level ON log_entries (level);
        """))
        
        conn.commit()

if __name__ == '__main__':
    app = create_app()
    
    # Initialize database
    init_db()
    
    # Start server
    port = int(os.getenv('PORT', 5002))
    app.run(host='0.0.0.0', port=port) 