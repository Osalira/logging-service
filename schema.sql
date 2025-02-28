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