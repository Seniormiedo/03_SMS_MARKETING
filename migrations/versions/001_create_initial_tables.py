"""Create initial tables with contact status tracking

Revision ID: 001
Revises: 
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

# Contact status enum
contact_status_enum = postgresql.ENUM(
    'ACTIVE', 'VERIFIED', 'INACTIVE', 'DISCONNECTED', 'SUSPENDED',
    'UNKNOWN', 'PENDING_VALIDATION', 'OPTED_OUT', 'BLOCKED', 'BLACKLISTED',
    'INVALID_FORMAT', 'NOT_MOBILE', 'CARRIER_ERROR',
    name='contactstatus'
)

# Campaign status enum
campaign_status_enum = postgresql.ENUM(
    'DRAFT', 'SCHEDULED', 'RUNNING', 'PAUSED', 'COMPLETED', 'CANCELLED', 'FAILED',
    name='campaignstatus'
)

# Message status enum
message_status_enum = postgresql.ENUM(
    'QUEUED', 'SENDING', 'SENT', 'DELIVERED', 'FAILED', 'REJECTED', 'EXPIRED', 'CANCELLED',
    name='messagestatus'
)

# Delivery status enum
delivery_status_enum = postgresql.ENUM(
    'PENDING', 'DELIVERED', 'FAILED', 'UNDELIVERED', 'REJECTED', 'UNKNOWN',
    name='deliverystatus'
)


def upgrade() -> None:
    # Create enums
    contact_status_enum.create(op.get_bind())
    campaign_status_enum.create(op.get_bind())
    message_status_enum.create(op.get_bind())
    delivery_status_enum.create(op.get_bind())
    
    # Create contacts table
    op.create_table(
        'contacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        # Phone number fields
        sa.Column('phone_e164', sa.String(length=15), nullable=False),
        sa.Column('phone_national', sa.String(length=12), nullable=False),
        sa.Column('phone_original', sa.String(length=20), nullable=True),
        
        # Contact information
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('neighborhood', sa.String(length=100), nullable=True),
        
        # Geographic information
        sa.Column('lada', sa.String(length=3), nullable=True),
        sa.Column('state_code', sa.String(length=5), nullable=True),
        sa.Column('state_name', sa.String(length=50), nullable=True),
        sa.Column('municipality', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        
        # Phone characteristics
        sa.Column('is_mobile', sa.Boolean(), nullable=False, default=True),
        sa.Column('operator', sa.String(length=50), nullable=True),
        
        # Status tracking (CRITICAL FIELD)
        sa.Column('status', contact_status_enum, nullable=False, default='UNKNOWN'),
        sa.Column('status_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status_source', sa.String(length=50), nullable=True),
        
        # SMS control
        sa.Column('send_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_sent_at', sa.DateTime(timezone=True), nullable=True),
        
        # Opt-out management
        sa.Column('opt_out_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('opt_out_method', sa.String(length=20), nullable=True),
        
        # Validation tracking
        sa.Column('last_validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('validation_attempts', sa.Integer(), nullable=False, default=0),
        
        # Data source
        sa.Column('source', sa.String(length=50), nullable=False, default='TELCEL2022'),
        sa.Column('import_batch_id', sa.String(length=50), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone_e164'),
        sa.CheckConstraint("phone_e164 ~ '^\\+52[0-9]{10}$'", name='check_phone_e164_format'),
        sa.CheckConstraint("phone_national ~ '^[0-9]{10}$'", name='check_phone_national_format'),
        sa.CheckConstraint('send_count >= 0', name='check_send_count_positive'),
        sa.CheckConstraint('validation_attempts >= 0', name='check_validation_attempts_positive')
    )
    
    # Create campaigns table
    op.create_table(
        'campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        # Campaign info
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('message_template', sa.Text(), nullable=False),
        
        # Targeting
        sa.Column('target_states', postgresql.ARRAY(sa.String(length=5)), nullable=True),
        sa.Column('target_ladas', postgresql.ARRAY(sa.String(length=3)), nullable=True),
        sa.Column('target_cities', postgresql.ARRAY(sa.String(length=100)), nullable=True),
        sa.Column('target_operators', postgresql.ARRAY(sa.String(length=50)), nullable=True),
        
        # Advanced targeting
        sa.Column('min_last_contact_days', sa.Integer(), nullable=True),
        sa.Column('max_send_count', sa.Integer(), nullable=True),
        sa.Column('exclude_recent_contacts', sa.Integer(), nullable=False, default=30),
        
        # Settings
        sa.Column('max_recipients', sa.Integer(), nullable=True),
        sa.Column('send_rate_per_minute', sa.Integer(), nullable=False, default=100),
        sa.Column('priority', sa.Integer(), nullable=False, default=5),
        
        # Status and scheduling
        sa.Column('status', campaign_status_enum, nullable=False, default='DRAFT'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        
        # Progress tracking
        sa.Column('estimated_recipients', sa.Integer(), nullable=False, default=0),
        sa.Column('sent_count', sa.Integer(), nullable=False, default=0),
        sa.Column('delivered_count', sa.Integer(), nullable=False, default=0),
        sa.Column('failed_count', sa.Integer(), nullable=False, default=0),
        
        # Cost tracking
        sa.Column('estimated_cost_usd', sa.Integer(), nullable=True),
        sa.Column('actual_cost_usd', sa.Integer(), nullable=False, default=0),
        
        # Approval and compliance
        sa.Column('approved_by', sa.String(length=100), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('compliance_checked', sa.String(length=50), nullable=True),
        
        # Error handling
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('send_rate_per_minute > 0', name='check_send_rate_positive'),
        sa.CheckConstraint('priority >= 1 AND priority <= 10', name='check_priority_range'),
        sa.CheckConstraint('sent_count >= 0', name='check_sent_count_positive'),
        sa.CheckConstraint('delivered_count >= 0', name='check_delivered_count_positive'),
        sa.CheckConstraint('failed_count >= 0', name='check_failed_count_positive'),
        sa.CheckConstraint('estimated_recipients >= 0', name='check_estimated_recipients_positive'),
        sa.CheckConstraint('actual_cost_usd >= 0', name='check_actual_cost_positive'),
        sa.CheckConstraint('retry_count >= 0', name='check_retry_count_positive')
    )
    
    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        # Relationships
        sa.Column('campaign_id', sa.Integer(), nullable=True),
        sa.Column('contact_id', sa.Integer(), nullable=True),
        
        # Message details
        sa.Column('phone_e164', sa.String(length=15), nullable=False),
        sa.Column('message_content', sa.Text(), nullable=False),
        sa.Column('message_length', sa.Integer(), nullable=False, default=0),
        sa.Column('sms_parts', sa.Integer(), nullable=False, default=1),
        
        # Provider info
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('external_id', sa.String(length=100), nullable=True),
        sa.Column('provider_response', sa.Text(), nullable=True),
        
        # Status tracking
        sa.Column('status', message_status_enum, nullable=False, default='QUEUED'),
        sa.Column('delivery_status', delivery_status_enum, nullable=False, default='PENDING'),
        
        # Error handling
        sa.Column('error_code', sa.String(length=20), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        
        # Timing
        sa.Column('queued_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        
        # Cost tracking
        sa.Column('cost_usd', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('cost_currency', sa.String(length=3), nullable=False, default='USD'),
        
        # Priority and routing
        sa.Column('priority', sa.Integer(), nullable=False, default=5),
        sa.Column('route_id', sa.String(length=50), nullable=True),
        
        # Compliance
        sa.Column('opt_out_detected', sa.String(length=20), nullable=True),
        sa.Column('spam_score', sa.Numeric(precision=3, scale=2), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
        sa.CheckConstraint('message_length >= 0', name='check_message_length_positive'),
        sa.CheckConstraint('sms_parts >= 1', name='check_sms_parts_positive'),
        sa.CheckConstraint('retry_count >= 0', name='check_retry_count_positive'),
        sa.CheckConstraint('priority >= 1 AND priority <= 10', name='check_priority_range'),
        sa.CheckConstraint('cost_usd >= 0', name='check_cost_positive'),
        sa.CheckConstraint('spam_score >= 0.0 AND spam_score <= 1.0', name='check_spam_score_range')
    )
    
    # Create indexes for contacts table
    op.create_index('idx_contacts_phone_e164', 'contacts', ['phone_e164'])
    op.create_index('idx_contacts_phone_national', 'contacts', ['phone_national'])
    op.create_index('idx_contacts_full_name', 'contacts', ['full_name'])
    op.create_index('idx_contacts_lada', 'contacts', ['lada'])
    op.create_index('idx_contacts_state_code', 'contacts', ['state_code'])
    op.create_index('idx_contacts_municipality', 'contacts', ['municipality'])
    op.create_index('idx_contacts_city', 'contacts', ['city'])
    op.create_index('idx_contacts_is_mobile', 'contacts', ['is_mobile'])
    op.create_index('idx_contacts_operator', 'contacts', ['operator'])
    op.create_index('idx_contacts_status', 'contacts', ['status'])
    op.create_index('idx_contacts_last_sent_at', 'contacts', ['last_sent_at'])
    op.create_index('idx_contacts_opt_out_at', 'contacts', ['opt_out_at'])
    op.create_index('idx_contacts_state_status', 'contacts', ['state_code', 'status'])
    op.create_index('idx_contacts_lada_status', 'contacts', ['lada', 'status'])
    op.create_index('idx_contacts_city_status', 'contacts', ['city', 'status'])
    op.create_index('idx_contacts_operator_status', 'contacts', ['operator', 'status'])
    
    # Create indexes for campaigns table
    op.create_index('idx_campaigns_name', 'campaigns', ['name'])
    op.create_index('idx_campaigns_status', 'campaigns', ['status'])
    op.create_index('idx_campaigns_scheduled_at', 'campaigns', ['scheduled_at'])
    op.create_index('idx_campaigns_status_scheduled', 'campaigns', ['status', 'scheduled_at'])
    op.create_index('idx_campaigns_created_status', 'campaigns', ['created_at', 'status'])
    op.create_index('idx_campaigns_priority_status', 'campaigns', ['priority', 'status'])
    
    # Create indexes for messages table
    op.create_index('idx_messages_campaign_id', 'messages', ['campaign_id'])
    op.create_index('idx_messages_contact_id', 'messages', ['contact_id'])
    op.create_index('idx_messages_phone_e164', 'messages', ['phone_e164'])
    op.create_index('idx_messages_provider', 'messages', ['provider'])
    op.create_index('idx_messages_external_id', 'messages', ['external_id'])
    op.create_index('idx_messages_status', 'messages', ['status'])
    op.create_index('idx_messages_delivery_status', 'messages', ['delivery_status'])
    op.create_index('idx_messages_queued_at', 'messages', ['queued_at'])
    op.create_index('idx_messages_sent_at', 'messages', ['sent_at'])
    op.create_index('idx_messages_delivered_at', 'messages', ['delivered_at'])
    op.create_index('idx_messages_campaign_status', 'messages', ['campaign_id', 'status'])
    op.create_index('idx_messages_contact_status', 'messages', ['contact_id', 'status'])
    op.create_index('idx_messages_phone_status', 'messages', ['phone_e164', 'status'])
    op.create_index('idx_messages_provider_status', 'messages', ['provider', 'status'])
    op.create_index('idx_messages_queued_priority', 'messages', ['queued_at', 'priority'])
    op.create_index('idx_messages_sent_delivery', 'messages', ['sent_at', 'delivery_status'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('messages')
    op.drop_table('campaigns')
    op.drop_table('contacts')
    
    # Drop enums
    delivery_status_enum.drop(op.get_bind())
    message_status_enum.drop(op.get_bind())
    campaign_status_enum.drop(op.get_bind())
    contact_status_enum.drop(op.get_bind())