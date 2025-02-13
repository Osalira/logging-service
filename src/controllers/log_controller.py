from datetime import datetime, timedelta
from flask import request, jsonify
from flask_restful import Resource
from marshmallow import Schema, fields, ValidationError
from sqlalchemy import create_engine, text
from ..config import Config

# Schema for validating log entries
class LogEntrySchema(Schema):
    timestamp = fields.DateTime(required=True)
    service = fields.Str(required=True)
    event_type = fields.Str(required=True)
    user_id = fields.Str(allow_none=True)
    details = fields.Dict(required=True)
    level = fields.Str(required=True)

# Initialize database connection
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

class LogController(Resource):
    def __init__(self):
        self.schema = LogEntrySchema()

    def post(self):
        """
        Store a new log entry
        
        Expected payload:
        {
            "timestamp": "2024-02-20T12:00:00Z",
            "service": "trading-service",
            "event_type": "order_placed",
            "user_id": "user123",
            "details": {
                "order_id": "ord_123",
                "symbol": "AAPL",
                "quantity": 100,
                "price": 150.00
            },
            "level": "INFO"
        }
        """
        try:
            # Validate request data
            data = request.get_json()
            validated_data = self.schema.load(data)
            
            # Insert log entry into database
            with engine.connect() as conn:
                query = text("""
                    INSERT INTO log_entries (
                        timestamp, service, event_type, user_id, details, level
                    ) VALUES (
                        :timestamp, :service, :event_type, :user_id, :details, :level
                    )
                """)
                
                conn.execute(query, validated_data)
                conn.commit()
            
            return {"message": "Log entry stored successfully"}, 201
            
        except ValidationError as e:
            return {"error": "Invalid log entry format", "details": str(e)}, 400
        except Exception as e:
            return {"error": "Failed to store log entry", "details": str(e)}, 500

    def get(self):
        """
        Retrieve log entries with optional filtering
        
        Query parameters:
        - start_time: ISO format datetime
        - end_time: ISO format datetime
        - service: Service name
        - event_type: Type of event
        - user_id: User identifier
        - level: Log level
        - limit: Maximum number of entries to return (default: 100)
        """
        try:
            # Parse query parameters
            start_time = request.args.get('start_time')
            end_time = request.args.get('end_time', datetime.utcnow().isoformat())
            service = request.args.get('service')
            event_type = request.args.get('event_type')
            user_id = request.args.get('user_id')
            level = request.args.get('level')
            limit = min(int(request.args.get('limit', 100)), 1000)  # Cap at 1000 entries
            
            # Build query
            query = """
                SELECT * FROM log_entries
                WHERE 1=1
            """
            params = {}
            
            if start_time:
                query += " AND timestamp >= :start_time"
                params['start_time'] = start_time
            
            if end_time:
                query += " AND timestamp <= :end_time"
                params['end_time'] = end_time
            
            if service:
                query += " AND service = :service"
                params['service'] = service
            
            if event_type:
                query += " AND event_type = :event_type"
                params['event_type'] = event_type
            
            if user_id:
                query += " AND user_id = :user_id"
                params['user_id'] = user_id
            
            if level:
                query += " AND level = :level"
                params['level'] = level
            
            query += " ORDER BY timestamp DESC LIMIT :limit"
            params['limit'] = limit
            
            # Execute query
            with engine.connect() as conn:
                result = conn.execute(text(query), params)
                logs = [dict(row) for row in result]
            
            return {"logs": logs}, 200
            
        except Exception as e:
            return {"error": "Failed to retrieve logs", "details": str(e)}, 500

class LogCleanupController(Resource):
    def post(self):
        """
        Clean up old log entries based on retention policy
        """
        try:
            retention_days = Config.LOG_RETENTION_DAYS
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            with engine.connect() as conn:
                query = text("""
                    DELETE FROM log_entries
                    WHERE timestamp < :cutoff_date
                """)
                
                result = conn.execute(query, {"cutoff_date": cutoff_date})
                conn.commit()
                
                deleted_count = result.rowcount
            
            return {
                "message": f"Cleaned up {deleted_count} log entries older than {retention_days} days"
            }, 200
            
        except Exception as e:
            return {"error": "Failed to clean up logs", "details": str(e)}, 500

class LogStatsController(Resource):
    def get(self):
        """
        Get statistics about logged events
        """
        try:
            with engine.connect() as conn:
                # Get counts by service
                service_query = text("""
                    SELECT service, COUNT(*) as count
                    FROM log_entries
                    GROUP BY service
                """)
                service_stats = [dict(row) for row in conn.execute(service_query)]
                
                # Get counts by event type
                event_query = text("""
                    SELECT event_type, COUNT(*) as count
                    FROM log_entries
                    GROUP BY event_type
                """)
                event_stats = [dict(row) for row in conn.execute(event_query)]
                
                # Get counts by log level
                level_query = text("""
                    SELECT level, COUNT(*) as count
                    FROM log_entries
                    GROUP BY level
                """)
                level_stats = [dict(row) for row in conn.execute(level_query)]
            
            return {
                "statistics": {
                    "by_service": service_stats,
                    "by_event_type": event_stats,
                    "by_level": level_stats
                }
            }, 200
            
        except Exception as e:
            return {"error": "Failed to retrieve log statistics", "details": str(e)}, 500 