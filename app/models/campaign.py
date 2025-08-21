"""
Campaign Model - Represents SMS marketing campaigns
"""

from sqlalchemy import (
    Column, String, Text, Integer, DateTime, ARRAY,
    CheckConstraint, Index, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class CampaignStatus(str, enum.Enum):
    """Campaign status enumeration"""
    DRAFT = "DRAFT"                      # Campaign being created
    SCHEDULED = "SCHEDULED"              # Scheduled for future execution
    RUNNING = "RUNNING"                  # Currently sending messages
    PAUSED = "PAUSED"                    # Temporarily paused
    COMPLETED = "COMPLETED"              # Finished successfully
    CANCELLED = "CANCELLED"              # Cancelled before completion
    FAILED = "FAILED"                    # Failed due to errors


class Campaign(BaseModel):
    """
    Campaign model for managing SMS marketing campaigns
    """
    __tablename__ = "campaigns"

    # Basic campaign information
    name = Column(String(255), nullable=False, index=True,
                 comment="Campaign name")
    description = Column(Text, nullable=True,
                        comment="Campaign description")
    message_template = Column(Text, nullable=False,
                             comment="SMS message template with placeholders")

    # Targeting criteria
    target_states = Column(ARRAY(String(5)), nullable=True,
                          comment="Target state codes array")
    target_ladas = Column(ARRAY(String(3)), nullable=True,
                         comment="Target LADA codes array")
    target_cities = Column(ARRAY(String(100)), nullable=True,
                          comment="Target cities array")
    target_operators = Column(ARRAY(String(50)), nullable=True,
                             comment="Target operators array")

    # Advanced targeting
    min_last_contact_days = Column(Integer, nullable=True,
                                  comment="Minimum days since last contact")
    max_send_count = Column(Integer, nullable=True,
                           comment="Maximum previous send count")
    exclude_recent_contacts = Column(Integer, default=30, nullable=False,
                                   comment="Exclude contacts contacted in last N days")

    # Campaign settings
    max_recipients = Column(Integer, nullable=True,
                           comment="Maximum number of recipients")
    send_rate_per_minute = Column(Integer, default=100, nullable=False,
                                 comment="Send rate limit per minute")
    priority = Column(Integer, default=5, nullable=False,
                     comment="Campaign priority (1=highest, 10=lowest)")

    # Status and scheduling
    status = Column(SQLEnum(CampaignStatus), default=CampaignStatus.DRAFT,
                   nullable=False, index=True,
                   comment="Current campaign status")
    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True,
                         comment="When campaign is scheduled to start")
    started_at = Column(DateTime(timezone=True), nullable=True,
                       comment="When campaign actually started")
    completed_at = Column(DateTime(timezone=True), nullable=True,
                         comment="When campaign completed")

    # Progress tracking
    estimated_recipients = Column(Integer, default=0, nullable=False,
                                 comment="Estimated number of recipients")
    sent_count = Column(Integer, default=0, nullable=False,
                       comment="Number of messages sent")
    delivered_count = Column(Integer, default=0, nullable=False,
                            comment="Number of messages delivered")
    failed_count = Column(Integer, default=0, nullable=False,
                         comment="Number of messages failed")

    # Cost tracking
    estimated_cost_usd = Column(Integer, nullable=True,
                               comment="Estimated cost in USD cents")
    actual_cost_usd = Column(Integer, default=0, nullable=False,
                            comment="Actual cost in USD cents")

    # Approval and compliance
    approved_by = Column(String(100), nullable=True,
                        comment="Who approved the campaign")
    approved_at = Column(DateTime(timezone=True), nullable=True,
                        comment="When campaign was approved")
    compliance_checked = Column(String(50), nullable=True,
                               comment="Compliance check status")

    # Error handling
    error_message = Column(Text, nullable=True,
                          comment="Error message if campaign failed")
    retry_count = Column(Integer, default=0, nullable=False,
                        comment="Number of retry attempts")

    # Relationships (commented for now - Message model not implemented yet)
    # messages = relationship("Message", back_populates="campaign", lazy="dynamic")

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("send_rate_per_minute > 0", name="check_send_rate_positive"),
        CheckConstraint("priority >= 1 AND priority <= 10", name="check_priority_range"),
        CheckConstraint("sent_count >= 0", name="check_sent_count_positive"),
        CheckConstraint("delivered_count >= 0", name="check_delivered_count_positive"),
        CheckConstraint("failed_count >= 0", name="check_failed_count_positive"),
        CheckConstraint("estimated_recipients >= 0", name="check_estimated_recipients_positive"),
        CheckConstraint("actual_cost_usd >= 0", name="check_actual_cost_positive"),
        CheckConstraint("retry_count >= 0", name="check_retry_count_positive"),

        # Indexes for common queries
        Index("idx_campaigns_status_scheduled", "status", "scheduled_at"),
        Index("idx_campaigns_created_status", "created_at", "status"),
        Index("idx_campaigns_priority_status", "priority", "status"),
        Index("idx_campaigns_name_search", "name"),
    )

    @property
    def delivery_rate(self) -> float:
        """Calculate delivery rate percentage"""
        if self.sent_count == 0:
            return 0.0
        return (self.delivered_count / self.sent_count) * 100

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage"""
        if self.sent_count == 0:
            return 0.0
        return (self.failed_count / self.sent_count) * 100

    @property
    def progress_percentage(self) -> float:
        """Calculate campaign progress percentage"""
        if self.estimated_recipients == 0:
            return 0.0
        return (self.sent_count / self.estimated_recipients) * 100

    @property
    def is_active(self) -> bool:
        """Check if campaign is actively sending"""
        return self.status in [CampaignStatus.RUNNING, CampaignStatus.SCHEDULED]

    @property
    def can_be_started(self) -> bool:
        """Check if campaign can be started"""
        return self.status in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]

    @property
    def can_be_paused(self) -> bool:
        """Check if campaign can be paused"""
        return self.status == CampaignStatus.RUNNING

    def estimate_duration_minutes(self) -> int:
        """Estimate campaign duration in minutes"""
        if self.estimated_recipients == 0 or self.send_rate_per_minute == 0:
            return 0
        return int(self.estimated_recipients / self.send_rate_per_minute)

    def update_progress(self, sent: int = 0, delivered: int = 0, failed: int = 0):
        """Update campaign progress counters"""
        self.sent_count += sent
        self.delivered_count += delivered
        self.failed_count += failed

    def __repr__(self):
        return f"<Campaign(id={self.id}, name='{self.name}', status={self.status.value})>"
