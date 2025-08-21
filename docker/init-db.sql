-- SMS Marketing Platform - Database Initialization Script
-- This script runs when PostgreSQL container starts for the first time

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create additional schemas if needed
-- CREATE SCHEMA IF NOT EXISTS analytics;
-- CREATE SCHEMA IF NOT EXISTS logs;

-- Set timezone
SET timezone = 'America/Mexico_City';

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Grant permissions to application user
GRANT ALL PRIVILEGES ON DATABASE sms_marketing TO sms_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sms_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sms_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO sms_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO sms_user;