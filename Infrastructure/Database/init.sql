-- SMS Marketing Platform v2.0 - Database Initialization
-- This script initializes the PostgreSQL database with optimizations
-- for the restructured system
-- =============================================================================
-- DATABASE SETUP
-- =============================================================================
-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
-- For fuzzy text matching
CREATE EXTENSION IF NOT EXISTS "btree_gin";
-- For composite indexes
-- Set timezone
SET timezone = 'UTC';
-- =============================================================================
-- PERFORMANCE OPTIMIZATIONS
-- =============================================================================
-- Increase work_mem for this session (for index creation)
SET work_mem = '256MB';
SET maintenance_work_mem = '512MB';
-- =============================================================================
-- CUSTOM FUNCTIONS FOR SMS MARKETING PLATFORM
-- =============================================================================
-- Function to generate contact IDs
CREATE OR REPLACE FUNCTION generate_contact_id() RETURNS TRIGGER AS $$ BEGIN IF NEW.id IS NULL THEN NEW.id = nextval('contacts_id_seq');
END IF;
RETURN NEW;
END;
$$ LANGUAGE plpgsql;
-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = CURRENT_TIMESTAMP;
RETURN NEW;
END;
$$ LANGUAGE plpgsql;
-- Function to validate phone numbers
CREATE OR REPLACE FUNCTION validate_phone_e164(phone_number TEXT) RETURNS BOOLEAN AS $$ BEGIN -- Check if phone number matches E.164 format for Mexico (+52xxxxxxxxxx)
    RETURN phone_number ~ '^\+52[0-9]{10}$';
END;
$$ LANGUAGE plpgsql IMMUTABLE;
-- Function to extract LADA from phone number
CREATE OR REPLACE FUNCTION extract_lada(phone_e164 TEXT) RETURNS TEXT AS $$ BEGIN -- Extract LADA (area code) from E.164 format
    IF validate_phone_e164(phone_e164) THEN RETURN substring(
        phone_e164
        from 4 for 3
    );
END IF;
RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
-- Function to format phone number to national format
CREATE OR REPLACE FUNCTION format_phone_national(phone_e164 TEXT) RETURNS TEXT AS $$ BEGIN -- Convert E.164 to national format (remove +52)
    IF validate_phone_e164(phone_e164) THEN RETURN substring(
        phone_e164
        from 4
    );
END IF;
RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
-- =============================================================================
-- PERFORMANCE MONITORING FUNCTIONS
-- =============================================================================
-- Function to get table statistics
CREATE OR REPLACE FUNCTION get_table_stats(table_name TEXT) RETURNS TABLE (
        table_name TEXT,
        row_count BIGINT,
        total_size TEXT,
        index_size TEXT,
        toast_size TEXT
    ) AS $$ BEGIN RETURN QUERY
SELECT schemaname || '.' || tablename as table_name,
    n_tup_ins - n_tup_del as row_count,
    pg_size_pretty(
        pg_total_relation_size(schemaname || '.' || tablename)
    ) as total_size,
    pg_size_pretty(pg_indexes_size(schemaname || '.' || tablename)) as index_size,
    pg_size_pretty(
        pg_total_relation_size(schemaname || '.' || tablename) - pg_relation_size(schemaname || '.' || tablename)
    ) as toast_size
FROM pg_stat_user_tables
WHERE schemaname || '.' || tablename = table_name;
END;
$$ LANGUAGE plpgsql;
-- Function to analyze contact distribution by state
CREATE OR REPLACE FUNCTION analyze_contact_distribution() RETURNS TABLE (
        state_name TEXT,
        contact_count BIGINT,
        percentage NUMERIC(5, 2)
    ) AS $$ BEGIN RETURN QUERY WITH total_contacts AS (
        SELECT COUNT(*) as total
        FROM contacts
        WHERE status = 'VERIFIED'
    )
SELECT COALESCE(c.state_name, 'UNKNOWN') as state_name,
    COUNT(*) as contact_count,
    ROUND((COUNT(*) * 100.0 / t.total), 2) as percentage
FROM contacts c
    CROSS JOIN total_contacts t
WHERE c.status = 'VERIFIED'
GROUP BY c.state_name,
    t.total
ORDER BY contact_count DESC;
END;
$$ LANGUAGE plpgsql;
-- =============================================================================
-- VALIDATION AND CLEANUP FUNCTIONS
-- =============================================================================
-- Function to clean up invalid contacts
CREATE OR REPLACE FUNCTION cleanup_invalid_contacts() RETURNS INTEGER AS $$
DECLARE deleted_count INTEGER;
BEGIN -- Delete contacts with invalid phone numbers
DELETE FROM contacts
WHERE NOT validate_phone_e164(phone_e164)
    OR phone_national IS NULL
    OR LENGTH(phone_national) != 10;
GET DIAGNOSTICS deleted_count = ROW_COUNT;
RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
-- Function to update contact statistics
CREATE OR REPLACE FUNCTION update_contact_statistics() RETURNS TABLE (
        total_contacts BIGINT,
        verified_contacts BIGINT,
        mobile_contacts BIGINT,
        available_contacts BIGINT
    ) AS $$ BEGIN RETURN QUERY
SELECT COUNT(*) as total_contacts,
    COUNT(*) FILTER (
        WHERE status = 'VERIFIED'
    ) as verified_contacts,
    COUNT(*) FILTER (
        WHERE is_mobile = true
    ) as mobile_contacts,
    COUNT(*) FILTER (
        WHERE status = 'VERIFIED'
            AND is_mobile = true
            AND opt_out_at IS NULL
    ) as available_contacts
FROM contacts;
END;
$$ LANGUAGE plpgsql;
-- =============================================================================
-- AUDIT AND LOGGING FUNCTIONS
-- =============================================================================
-- Function to log contact changes
CREATE OR REPLACE FUNCTION log_contact_change() RETURNS TRIGGER AS $$ BEGIN -- Insert audit record for contact changes
INSERT INTO contact_audit_log (
        contact_id,
        operation,
        old_values,
        new_values,
        changed_by,
        changed_at
    )
VALUES (
        COALESCE(NEW.id, OLD.id),
        TG_OP,
        CASE
            WHEN TG_OP = 'DELETE' THEN row_to_json(OLD)
            ELSE NULL
        END,
        CASE
            WHEN TG_OP != 'DELETE' THEN row_to_json(NEW)
            ELSE NULL
        END,
        current_user,
        CURRENT_TIMESTAMP
    );
RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;
-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================
-- Note: Indexes will be created by the application migration scripts
-- This section documents the recommended indexes for reference
/*
 -- Primary indexes (created automatically with tables)
 CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_pkey ON contacts (id);
 CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_phone_e164 ON contacts (phone_e164);
 
 -- Performance indexes for contact queries
 CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_status ON contacts (status);
 CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_state_status ON contacts (state_name, status);
 CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_lada_status ON contacts (lada, status);
 CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_is_mobile ON contacts (is_mobile);
 CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_opt_out ON contacts (opt_out_at) WHERE opt_out_at IS NOT NULL;
 
 -- Composite indexes for common queries
 CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_extraction ON contacts (status, is_mobile, opt_out_at)
 WHERE status = 'VERIFIED' AND is_mobile = true AND opt_out_at IS NULL;
 
 -- Indexes for validation operations
 CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_last_validated ON contacts (last_validated_at);
 CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_validation_attempts ON contacts (validation_attempts);
 
 -- Indexes for campaign management
 CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_send_count ON contacts (send_count);
 CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_last_sent ON contacts (last_sent_at);
 
 -- Text search indexes
 CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_name_gin ON contacts USING gin (full_name gin_trgm_ops);
 CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_address_gin ON contacts USING gin (address gin_trgm_ops);
 
 -- Partial indexes for active contacts
 CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_active ON contacts (id, phone_e164, state_name)
 WHERE status = 'VERIFIED' AND is_mobile = true AND opt_out_at IS NULL;
 */
-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================
-- View for available contacts (ready for extraction)
CREATE OR REPLACE VIEW available_contacts AS
SELECT id,
    phone_e164,
    phone_national,
    full_name,
    state_name,
    municipality,
    city,
    lada,
    operator,
    send_count,
    last_sent_at,
    created_at
FROM contacts
WHERE status = 'VERIFIED'
    AND is_mobile = true
    AND opt_out_at IS NULL;
-- View for contact statistics by state
CREATE OR REPLACE VIEW contact_stats_by_state AS
SELECT COALESCE(state_name, 'UNKNOWN') as state_name,
    COUNT(*) as total_contacts,
    COUNT(*) FILTER (
        WHERE status = 'VERIFIED'
    ) as verified_contacts,
    COUNT(*) FILTER (
        WHERE is_mobile = true
    ) as mobile_contacts,
    COUNT(*) FILTER (
        WHERE status = 'VERIFIED'
            AND is_mobile = true
            AND opt_out_at IS NULL
    ) as available_contacts,
    ROUND(AVG(send_count), 2) as avg_send_count
FROM contacts
GROUP BY state_name
ORDER BY available_contacts DESC;
-- View for validation statistics
CREATE OR REPLACE VIEW validation_stats AS
SELECT COUNT(*) as total_contacts,
    COUNT(*) FILTER (
        WHERE last_validated_at IS NOT NULL
    ) as validated_contacts,
    COUNT(*) FILTER (
        WHERE last_validated_at > CURRENT_DATE - INTERVAL '30 days'
    ) as recently_validated,
    ROUND(AVG(validation_attempts), 2) as avg_validation_attempts,
    MAX(last_validated_at) as last_validation_date
FROM contacts;
-- =============================================================================
-- CONFIGURATION SETTINGS
-- =============================================================================
-- Set application-specific settings
ALTER DATABASE sms_marketing
SET timezone = 'UTC';
ALTER DATABASE sms_marketing
SET log_statement = 'mod';
ALTER DATABASE sms_marketing
SET log_min_duration_statement = 1000;
-- =============================================================================
-- GRANTS AND PERMISSIONS
-- =============================================================================
-- Grant permissions to application user
GRANT USAGE ON SCHEMA public TO sms_user;
GRANT SELECT,
    INSERT,
    UPDATE,
    DELETE ON ALL TABLES IN SCHEMA public TO sms_user;
GRANT USAGE,
    SELECT ON ALL SEQUENCES IN SCHEMA public TO sms_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO sms_user;
-- Grant permissions for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT,
    INSERT,
    UPDATE,
    DELETE ON TABLES TO sms_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE,
    SELECT ON SEQUENCES TO sms_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT EXECUTE ON FUNCTIONS TO sms_user;
-- =============================================================================
-- MAINTENANCE PROCEDURES
-- =============================================================================
-- Procedure for regular maintenance
CREATE OR REPLACE FUNCTION perform_maintenance() RETURNS TEXT AS $$
DECLARE result TEXT := '';
BEGIN -- Update table statistics
ANALYZE contacts;
ANALYZE ift_rangos;
ANALYZE ladas_reference;
result := result || 'Statistics updated. ';
-- Vacuum if needed
-- Note: Autovacuum should handle this, but manual vacuum can be forced
-- VACUUM ANALYZE contacts;
result := result || 'Maintenance completed.';
RETURN result;
END;
$$ LANGUAGE plpgsql;
-- =============================================================================
-- INITIALIZATION COMPLETE
-- =============================================================================
-- Reset work_mem to default
RESET work_mem;
RESET maintenance_work_mem;
-- Log initialization completion
DO $$ BEGIN RAISE NOTICE 'SMS Marketing Platform v2.0 database initialization completed successfully';
RAISE NOTICE 'Database: %',
current_database();
RAISE NOTICE 'User: %',
current_user;
RAISE NOTICE 'Timestamp: %',
CURRENT_TIMESTAMP;
END $$;
