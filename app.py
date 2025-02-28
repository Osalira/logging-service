from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/logging_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Configure CORS
CORS(app)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class LogEntry(db.Model):
    __tablename__ = 'log_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(50), nullable=False)
    log_level = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'service': self.service,
            'log_level': self.log_level,
            'message': self.message,
            'timestamp': self.timestamp.isoformat()
        }

class AuditTrail(db.Model):
    __tablename__ = 'audit_trail'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }

# Routes

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "logging-service"})

@app.route('/api/logs/system', methods=['GET'])
def get_system_logs():
    """Get system logs with optional filtering"""
    try:
        # Get query parameters
        service = request.args.get('service')
        log_level = request.args.get('log_level')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = LogEntry.query
        
        if service:
            query = query.filter(LogEntry.service == service)
        if log_level:
            query = query.filter(LogEntry.log_level == log_level)
        if start_time:
            query = query.filter(LogEntry.timestamp >= datetime.fromisoformat(start_time))
        if end_time:
            query = query.filter(LogEntry.timestamp <= datetime.fromisoformat(end_time))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        logs = query.order_by(LogEntry.timestamp.desc()).offset(offset).limit(limit).all()
        
        # Convert to dict
        log_data = [log.to_dict() for log in logs]
        
        return jsonify({
            'total_count': total_count,
            'logs': log_data
        })
    except Exception as e:
        logger.error(f"Error getting system logs: {str(e)}")
        return jsonify({"error": "Failed to get system logs"}), 500

@app.route('/api/logs/audit', methods=['GET'])
def get_audit_logs():
    """Get audit logs with optional filtering"""
    try:
        # Get query parameters
        user_id = request.args.get('user_id')
        action = request.args.get('action')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = AuditTrail.query
        
        if user_id:
            query = query.filter(AuditTrail.user_id == user_id)
        if action:
            query = query.filter(AuditTrail.action == action)
        if start_time:
            query = query.filter(AuditTrail.timestamp >= datetime.fromisoformat(start_time))
        if end_time:
            query = query.filter(AuditTrail.timestamp <= datetime.fromisoformat(end_time))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        audit_logs = query.order_by(AuditTrail.timestamp.desc()).offset(offset).limit(limit).all()
        
        # Convert to dict
        audit_log_data = [log.to_dict() for log in audit_logs]
        
        return jsonify({
            'total_count': total_count,
            'logs': audit_log_data
        })
    except Exception as e:
        logger.error(f"Error getting audit logs: {str(e)}")
        return jsonify({"error": "Failed to get audit logs"}), 500

@app.route('/api/logs/create', methods=['POST'])
def create_log():
    """Create a new log entry"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['service', 'log_level', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create log entry
        log_entry = LogEntry(
            service=data['service'],
            log_level=data['log_level'],
            message=data['message']
        )
        
        # Save to database
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({
            "message": "Log entry created successfully",
            "log_id": log_entry.id
        }), 201
    except Exception as e:
        logger.error(f"Error creating log entry: {str(e)}")
        return jsonify({"error": "Failed to create log entry"}), 500

@app.route('/api/logs/audit/create', methods=['POST'])
def create_audit_log():
    """Create a new audit log entry"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['action']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create audit log entry
        audit_log = AuditTrail(
            user_id=data.get('user_id'),
            action=data['action'],
            details=data.get('details')
        )
        
        # Save to database
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            "message": "Audit log entry created successfully",
            "log_id": audit_log.id
        }), 201
    except Exception as e:
        logger.error(f"Error creating audit log entry: {str(e)}")
        return jsonify({"error": "Failed to create audit log entry"}), 500

if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true') 