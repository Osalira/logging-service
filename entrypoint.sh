#!/bin/bash
set -e

# Try to run one-time initialization if it hasn't been run before
if [ ! -f "/app/.db_initialized" ]; then
    echo "Attempting one-time database initialization..."
    /app/init-db-once.sh || echo "Will continue with normal initialization flow"
fi

# Prioritize explicit DB variables if provided, otherwise parse from DATABASE_URL
if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ] && [ -n "$DB_USER" ] && [ -n "$DB_PASSWORD" ] && [ -n "$DB_NAME" ]; then
    echo "Using explicit database connection variables"
else
    echo "Explicit DB variables not fully provided, attempting to parse from DATABASE_URL"
    # Parse DATABASE_URL to extract components
    # Format: postgresql://username:password@host:port/dbname
    if [ -n "$DATABASE_URL" ]; then
        DB_USER=$(echo $DATABASE_URL | sed -e 's/^postgresql:\/\///' -e 's/:.*$//')
        DB_PASSWORD=$(echo $DATABASE_URL | sed -e 's/^.*://' -e 's/@.*$//')
        DB_HOST=$(echo $DATABASE_URL | sed -e 's/^.*@//' -e 's/:.*$//')
        DB_PORT=$(echo $DATABASE_URL | sed -e 's/^.*://' -e 's/\/.*$//')
        DB_NAME=$(echo $DATABASE_URL | sed -e 's/^.*\///' -e 's/\?.*$//')
    else
        # Use default values if DATABASE_URL is not set
        DB_USER=${DB_USER:-postgres}
        DB_PASSWORD=${DB_PASSWORD:-password}
        DB_HOST=${DB_HOST:-db}
        DB_PORT=${DB_PORT:-5432}
        DB_NAME=${DB_NAME:-logging_db}
    fi
fi

echo "Database connection info: host=$DB_HOST, port=$DB_PORT, user=$DB_USER, database=$DB_NAME"
echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
ATTEMPT=0
MAX_ATTEMPTS=30
until PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "\q" > /dev/null 2>&1; do
    ATTEMPT=$((ATTEMPT+1))
    if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
        echo "PostgreSQL is not available after $MAX_ATTEMPTS attempts. Exiting."
        exit 1
    fi
    echo "PostgreSQL is unavailable - retrying in 5s (attempt $ATTEMPT/$MAX_ATTEMPTS)"
    sleep 5
done
echo "PostgreSQL is up and running!"

# Check if schema.sql exists
if [ ! -f "/app/schema.sql" ]; then
    echo "Error: schema.sql file not found!"
    echo "Creating a default schema..."
    
    # Create a basic schema if the file is missing
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
    echo "Default schema created."
fi

# Check if tables exist in database
echo "Checking if tables exist in database..."
TABLE_COUNT=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)

if [ "$TABLE_COUNT" -eq "0" ]; then
    echo "No tables found, initializing database schema..."
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f schema.sql
    echo "Schema initialized successfully!"
else
    echo "Tables already exist, skipping schema initialization."
fi

echo "Starting application..."
exec gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 2 app:app 