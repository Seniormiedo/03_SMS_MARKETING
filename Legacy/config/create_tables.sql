-- SMS Marketing Platform - Create Tables Script
-- Contact Status Tracking System

-- Create enums
CREATE TYPE contactstatus AS ENUM (
    'ACTIVE', 'VERIFIED', 'INACTIVE', 'DISCONNECTED', 'SUSPENDED',
    'UNKNOWN', 'PENDING_VALIDATION', 'OPTED_OUT', 'BLOCKED', 'BLACKLISTED',
    'INVALID_FORMAT', 'NOT_MOBILE', 'CARRIER_ERROR'
);

CREATE TYPE campaignstatus AS ENUM (
    'DRAFT', 'SCHEDULED', 'RUNNING', 'PAUSED', 'COMPLETED', 'CANCELLED', 'FAILED'
);

CREATE TYPE messagestatus AS ENUM (
    'QUEUED', 'SENDING', 'SENT', 'DELIVERED', 'FAILED', 'REJECTED', 'EXPIRED', 'CANCELLED'
);

CREATE TYPE deliverystatus AS ENUM (
    'PENDING', 'DELIVERED', 'FAILED', 'UNDELIVERED', 'REJECTED', 'UNKNOWN'
);

-- Create contacts table
CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Phone number fields (required)
    phone_e164 VARCHAR(15) UNIQUE NOT NULL,
    phone_national VARCHAR(12) NOT NULL,
    phone_original VARCHAR(20),
    
    -- Contact information (optional)
    full_name VARCHAR(255),
    address TEXT,
    neighborhood VARCHAR(100),
    
    -- Geographic information
    lada VARCHAR(3),
    state_code VARCHAR(5),
    state_name VARCHAR(50),
    municipality VARCHAR(100),
    city VARCHAR(100),
    
    -- Phone line characteristics
    is_mobile BOOLEAN DEFAULT TRUE NOT NULL,
    operator VARCHAR(50),
    
    -- Status tracking (CRITICAL FIELD)
    status contactstatus DEFAULT 'UNKNOWN' NOT NULL,
    status_updated_at TIMESTAMP WITH TIME ZONE,
    status_source VARCHAR(50),
    
    -- SMS sending control
    send_count INTEGER DEFAULT 0 NOT NULL,
    last_sent_at TIMESTAMP WITH TIME ZONE,
    
    -- Opt-out management
    opt_out_at TIMESTAMP WITH TIME ZONE,
    opt_out_method VARCHAR(20),
    
    -- Validation tracking
    last_validated_at TIMESTAMP WITH TIME ZONE,
    validation_attempts INTEGER DEFAULT 0 NOT NULL,
    
    -- Data source tracking
    source VARCHAR(50) DEFAULT 'TELCEL2022' NOT NULL,
    import_batch_id VARCHAR(50),
    
    -- Constraints
    CONSTRAINT check_phone_e164_format CHECK (phone_e164 ~ '^\+52[0-9]{10}$'),
    CONSTRAINT check_phone_national_format CHECK (phone_national ~ '^[0-9]{10}$'),
    CONSTRAINT check_send_count_positive CHECK (send_count >= 0),
    CONSTRAINT check_validation_attempts_positive CHECK (validation_attempts >= 0)
);

-- Create campaigns table
CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Basic campaign information
    name VARCHAR(255) NOT NULL,
    description TEXT,
    message_template TEXT NOT NULL,
    
    -- Targeting criteria
    target_states VARCHAR(5)[],
    target_ladas VARCHAR(3)[],
    target_cities VARCHAR(100)[],
    target_operators VARCHAR(50)[],
    
    -- Advanced targeting
    min_last_contact_days INTEGER,
    max_send_count INTEGER,
    exclude_recent_contacts INTEGER DEFAULT 30 NOT NULL,
    
    -- Campaign settings
    max_recipients INTEGER,
    send_rate_per_minute INTEGER DEFAULT 100 NOT NULL,
    priority INTEGER DEFAULT 5 NOT NULL,
    
    -- Status and scheduling
    status campaignstatus DEFAULT 'DRAFT' NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Progress tracking
    estimated_recipients INTEGER DEFAULT 0 NOT NULL,
    sent_count INTEGER DEFAULT 0 NOT NULL,
    delivered_count INTEGER DEFAULT 0 NOT NULL,
    failed_count INTEGER DEFAULT 0 NOT NULL,
    
    -- Cost tracking
    estimated_cost_usd INTEGER,
    actual_cost_usd INTEGER DEFAULT 0 NOT NULL,
    
    -- Approval and compliance
    approved_by VARCHAR(100),
    approved_at TIMESTAMP WITH TIME ZONE,
    compliance_checked VARCHAR(50),
    
    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0 NOT NULL,
    
    -- Constraints
    CONSTRAINT check_send_rate_positive CHECK (send_rate_per_minute > 0),
    CONSTRAINT check_priority_range CHECK (priority >= 1 AND priority <= 10),
    CONSTRAINT check_sent_count_positive CHECK (sent_count >= 0),
    CONSTRAINT check_delivered_count_positive CHECK (delivered_count >= 0),
    CONSTRAINT check_failed_count_positive CHECK (failed_count >= 0),
    CONSTRAINT check_estimated_recipients_positive CHECK (estimated_recipients >= 0),
    CONSTRAINT check_actual_cost_positive CHECK (actual_cost_usd >= 0),
    CONSTRAINT check_retry_count_positive CHECK (retry_count >= 0)
);

-- Create messages table
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Relationships
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE SET NULL,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    
    -- Message details
    phone_e164 VARCHAR(15) NOT NULL,
    message_content TEXT NOT NULL,
    message_length INTEGER DEFAULT 0 NOT NULL,
    sms_parts INTEGER DEFAULT 1 NOT NULL,
    
    -- Provider information
    provider VARCHAR(50),
    external_id VARCHAR(100),
    provider_response TEXT,
    
    -- Status tracking
    status messagestatus DEFAULT 'QUEUED' NOT NULL,
    delivery_status deliverystatus DEFAULT 'PENDING' NOT NULL,
    
    -- Error handling
    error_code VARCHAR(20),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0 NOT NULL,
    
    -- Timing
    queued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    
    -- Cost tracking
    cost_usd NUMERIC(10, 6),
    cost_currency VARCHAR(3) DEFAULT 'USD' NOT NULL,
    
    -- Priority and routing
    priority INTEGER DEFAULT 5 NOT NULL,
    route_id VARCHAR(50),
    
    -- Compliance and tracking
    opt_out_detected VARCHAR(20),
    spam_score NUMERIC(3, 2),
    
    -- Constraints
    CONSTRAINT check_message_length_positive CHECK (message_length >= 0),
    CONSTRAINT check_sms_parts_positive CHECK (sms_parts >= 1),
    CONSTRAINT check_retry_count_positive CHECK (retry_count >= 0),
    CONSTRAINT check_priority_range CHECK (priority >= 1 AND priority <= 10),
    CONSTRAINT check_cost_positive CHECK (cost_usd >= 0),
    CONSTRAINT check_spam_score_range CHECK (spam_score >= 0.0 AND spam_score <= 1.0)
);

-- Create indexes for contacts table
CREATE INDEX idx_contacts_phone_e164 ON contacts(phone_e164);
CREATE INDEX idx_contacts_phone_national ON contacts(phone_national);
CREATE INDEX idx_contacts_full_name ON contacts(full_name);
CREATE INDEX idx_contacts_lada ON contacts(lada);
CREATE INDEX idx_contacts_state_code ON contacts(state_code);
CREATE INDEX idx_contacts_municipality ON contacts(municipality);
CREATE INDEX idx_contacts_city ON contacts(city);
CREATE INDEX idx_contacts_is_mobile ON contacts(is_mobile);
CREATE INDEX idx_contacts_operator ON contacts(operator);
CREATE INDEX idx_contacts_status ON contacts(status);
CREATE INDEX idx_contacts_last_sent_at ON contacts(last_sent_at);
CREATE INDEX idx_contacts_opt_out_at ON contacts(opt_out_at);
CREATE INDEX idx_contacts_state_status ON contacts(state_code, status);
CREATE INDEX idx_contacts_lada_status ON contacts(lada, status);
CREATE INDEX idx_contacts_city_status ON contacts(city, status);
CREATE INDEX idx_contacts_operator_status ON contacts(operator, status);

-- Create partial indexes for active contacts
CREATE INDEX idx_contacts_active_mobile ON contacts(status, is_mobile) 
WHERE status IN ('ACTIVE', 'VERIFIED') AND opt_out_at IS NULL;

CREATE INDEX idx_contacts_last_sent_filter ON contacts(last_sent_at) 
WHERE last_sent_at IS NOT NULL;

CREATE INDEX idx_contacts_opt_out_filter ON contacts(opt_out_at) 
WHERE opt_out_at IS NOT NULL;

-- Create indexes for campaigns table
CREATE INDEX idx_campaigns_name ON campaigns(name);
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_scheduled_at ON campaigns(scheduled_at);
CREATE INDEX idx_campaigns_status_scheduled ON campaigns(status, scheduled_at);
CREATE INDEX idx_campaigns_created_status ON campaigns(created_at, status);
CREATE INDEX idx_campaigns_priority_status ON campaigns(priority, status);

-- Create indexes for messages table
CREATE INDEX idx_messages_campaign_id ON messages(campaign_id);
CREATE INDEX idx_messages_contact_id ON messages(contact_id);
CREATE INDEX idx_messages_phone_e164 ON messages(phone_e164);
CREATE INDEX idx_messages_provider ON messages(provider);
CREATE INDEX idx_messages_external_id ON messages(external_id);
CREATE INDEX idx_messages_status ON messages(status);
CREATE INDEX idx_messages_delivery_status ON messages(delivery_status);
CREATE INDEX idx_messages_queued_at ON messages(queued_at);
CREATE INDEX idx_messages_sent_at ON messages(sent_at);
CREATE INDEX idx_messages_delivered_at ON messages(delivered_at);
CREATE INDEX idx_messages_campaign_status ON messages(campaign_id, status);
CREATE INDEX idx_messages_contact_status ON messages(contact_id, status);
CREATE INDEX idx_messages_phone_status ON messages(phone_e164, status);
CREATE INDEX idx_messages_provider_status ON messages(provider, status);
CREATE INDEX idx_messages_queued_priority ON messages(queued_at, priority);
CREATE INDEX idx_messages_sent_delivery ON messages(sent_at, delivery_status);

-- Create indexes for analytics
CREATE INDEX idx_messages_analytics ON messages(created_at, status, delivery_status);
CREATE INDEX idx_messages_daily_stats ON messages(queued_at, campaign_id, status);

-- Create error code index with filter
CREATE INDEX idx_messages_error_code ON messages(error_code) 
WHERE error_code IS NOT NULL;

-- Create retry index with filter
CREATE INDEX idx_messages_retry ON messages(retry_count, status) 
WHERE retry_count > 0;

-- Create cost tracking index
CREATE INDEX idx_messages_cost_tracking ON messages(cost_usd, created_at);

-- Create function to update updated_at automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_contacts_updated_at BEFORE UPDATE ON contacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_messages_updated_at BEFORE UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create alembic version table
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Insert initial version
INSERT INTO alembic_version (version_num) VALUES ('001');

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sms_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sms_user;

-- Display table information
SELECT 
    schemaname,
    tablename,
    tableowner,
    tablespace,
    hasindexes,
    hasrules,
    hastriggers
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;