# Logging Service

This service handles logging and auditing for the Day Trading System, capturing and storing logs of all transactions and events.

## Features

- Store and retrieve log entries
- Filter logs by various criteria (time, service, event type, etc.)
- Automatic log rotation and cleanup
- Log statistics and analytics
- PostgreSQL database for persistent storage

## Prerequisites

- Python 3.8+
- PostgreSQL
- Virtual Environment (recommended)

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (create a .env file):
```env
# Database settings
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/daytrading_logs
FLASK_SECRET_KEY=your-secret-key-here
FLASK_DEBUG=True

# Logging settings
LOG_LEVEL=INFO
LOG_FILE=logs/daytrading.log
LOG_RETENTION_DAYS=90

# Service settings
PORT=5002
BATCH_SIZE=1000

# Other service URLs
AUTH_SERVICE_URL=http://localhost:5000
TRADING_SERVICE_URL=http://localhost:8000
MATCHING_ENGINE_URL=http://localhost:8080
```

4. Initialize the database:
The service will automatically create the required tables on startup.

## Running the Service

Start the service:
```bash
python app.py
```

The service will run on `http://localhost:5002`

## API Endpoints

### Log Management

- `POST /api/v1/logs` - Store a new log entry
  ```json
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
  ```

- `GET /api/v1/logs` - Retrieve log entries with filtering
  Query parameters:
  - start_time: ISO format datetime
  - end_time: ISO format datetime
  - service: Service name
  - event_type: Type of event
  - user_id: User identifier
  - level: Log level
  - limit: Maximum number of entries (default: 100)

### Maintenance

- `POST /api/v1/logs/cleanup` - Clean up old log entries
- `GET /api/v1/logs/stats` - Get log statistics

### Health Check

- `GET /health` - Service health check

## Database Schema

### Log Entries Table
```sql
CREATE TABLE log_entries (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    service VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(50),
    details JSONB NOT NULL,
    level VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Indexes are created for efficient querying on commonly filtered fields.

## Development

- Run tests:
```bash
python -m pytest
```

- Format code:
```bash
black .
```

## Security Notes

- All sensitive configuration is managed through environment variables
- Database connection uses secure credentials
- Input validation is performed on all log entries
- Log rotation prevents disk space issues
- Retention policy automatically cleans up old logs 