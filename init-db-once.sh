#!/bin/bash
set -e

# This script runs once on container startup to initialize the database if needed
# It's designed to be robust and handle various edge cases

echo "Running one-time database initialization check..."

# Database connection parameters
DB_USER=${DB_USER:-user}
DB_PASSWORD=${DB_PASSWORD:-password}
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-logging_db}

# Check if we can connect to the database
if ! PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1" >/dev/null 2>&1; then
    echo "Cannot connect to database. Will retry during main startup."
    exit 0
fi

# Check if tables exist
TABLE_COUNT=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)

if [ "$TABLE_COUNT" -eq "0" ]; then
    echo "Database is empty, initializing now..."
    
    # Ensure schema.sql exists
    if [ ! -f "/app/schema.sql" ]; then
        echo "Creating default schema.sql..."
        cat > /app/schema.sql << EOF
-- Drop existing tables
DROP TABLE IF EXISTS audit_trail CASCADE;
DROP TABLE IF EXISTS log_entries CASCADE;

-- Create log_entries table
CREATE TABLE log_entries (
    id SERIAL PRIMARY KEY,
    service VARCHAR(50) NOT NULL,
    log_level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for log_entries
CREATE INDEX idx_log_entries_service ON log_entries(service);
CREATE INDEX idx_log_entries_log_level ON log_entries(log_level);
CREATE INDEX idx_log_entries_timestamp ON log_entries(timestamp);

-- Create audit_trail table
CREATE TABLE audit_trail (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for audit_trail
CREATE INDEX idx_audit_trail_user_id ON audit_trail(user_id);
CREATE INDEX idx_audit_trail_action ON audit_trail(action);
CREATE INDEX idx_audit_trail_timestamp ON audit_trail(timestamp);
EOF
    fi
    
    # Apply schema
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f /app/schema.sql
    echo "Schema initialization complete!"
    
    # Create a marker file to indicate successful initialization
    touch /app/.db_initialized
else
    echo "Database already has tables. No initialization needed."
    touch /app/.db_initialized
fi 