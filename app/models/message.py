"""
Message Model - Represents individual SMS messages
"""

from sqlalchemy import (
    Column, String, Text, Integer, DateTime, ForeignKey, 
    CheckConstraint, Index, Enum as SQLEnum, Numeric
)
from sqlalchemy.orm import relationship
from decimal import Decimal
import enum

from app.models.base import BaseModel


class MessageStatus(str, enum.Enum):
    """Message status enumeration"""
    QUEUED = "QUEUED"                    # Message queued for sending
    SENDING = "SENDING"                  # Message being sent
    SENT = "SENT"                        # Message sent to provider
    DELIVERED = "DELIVERED"              # Message delivered to recipient
    FAILED = "FAILED"                    # Message failed to send
    REJECTED = "REJECTED"                # Message rejected by provider
    EXPIRED = "EXPIRED"                  # Message expired before delivery
    CANCELLED = "CANCELLED"              # Message cancelled before sending


class DeliveryStatus(str, enum.Enum):
    """Delivery status from SMS provider"""
    PENDING = "PENDING"                  # Delivery pending
    DELIVERED = "DELIVERED"              # Successfully delivered
    FAILED = "FAILED"                    # Delivery failed
    UNDELIVERED = "UNDELIVERED"          # Could not be delivered
    REJECTED = "REJECTED"                # Rejected by carrier
    UNKNOWN = "UNKNOWN"                  # Unknown delivery status


class Message(BaseModel):
    """
    Message model for storing individual SMS messages
    """
    __tablename__ = "messages"
    
    # Relationships
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="SET NULL"), 
                        nullable=True, index=True,
                        comment="Associated campaign ID")
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), 
                       nullable=True, index=True,
                       comment="Associated contact ID")
    
    # Message details
    phone_e164 = Column(String(15), nullable=False, index=True,
                       comment="Recipient phone number in E.164 format")
    message_content = Column(Text, nullable=False,
                            comment="Actual message content sent")
    message_length = Column(Integer, nullable=False, default=0,
                           comment="Message length in characters")
    sms_parts = Column(Integer, nullable=False, default=1,
                      comment="Number of SMS parts (for long messages)")
    
    # Provider information
    provider = Column(String(50), nullable=True, index=True,
                     comment="SMS provider used (twilio, messagebird, etc.)")
    external_id = Column(String(100), nullable=True, index=True,
                        comment="Provider's message ID")
    provider_response = Column(Text, nullable=True,
                              comment="Raw provider response")
    
    # Status tracking
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.QUEUED,
                   nullable=False, index=True,
                   comment="Current message status")
    delivery_status = Column(SQLEnum(DeliveryStatus), default=DeliveryStatus.PENDING,
                            nullable=False, index=True,
                            comment="Delivery status from provider")
    
    # Error handling
    error_code = Column(String(20), nullable=True,
                       comment="Error code from provider")
    error_message = Column(Text, nullable=True,
                          comment="Error message description")
    retry_count = Column(Integer, default=0, nullable=False,
                        comment="Number of retry attempts")
    
    # Timing
    queued_at = Column(DateTime(timezone=True), nullable=False, index=True,
                      comment="When message was queued")
    sent_at = Column(DateTime(timezone=True), nullable=True, index=True,
                    comment="When message was sent to provider")
    delivered_at = Column(DateTime(timezone=True), nullable=True, index=True,
                         comment="When message was delivered")
    failed_at = Column(DateTime(timezone=True), nullable=True,
                      comment="When message failed")
    
    # Cost tracking
    cost_usd = Column(Numeric(10, 6), nullable=True,
                     comment="Cost in USD")
    cost_currency = Column(String(3), default="USD", nullable=False,
                          comment="Cost currency code")
    
    # Priority and routing
    priority = Column(Integer, default=5, nullable=False,
                     comment="Message priority (1=highest, 10=lowest)")
    route_id = Column(String(50), nullable=True,
                     comment="Routing identifier")
    
    # Compliance and tracking
    opt_out_detected = Column(String(20), nullable=True,
                             comment="Detected opt-out keywords (STOP, BAJA)")
    spam_score = Column(Numeric(3, 2), nullable=True,
                       comment="Spam probability score (0.0-1.0)")
    
    # Relationships
    campaign = relationship("Campaign", back_populates="messages")
    contact = relationship("Contact", back_populates="messages")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("message_length >= 0", name="check_message_length_positive"),
        CheckConstraint("sms_parts >= 1", name="check_sms_parts_positive"),
        CheckConstraint("retry_count >= 0", name="check_retry_count_positive"),
        CheckConstraint("priority >= 1 AND priority <= 10", name="check_priority_range"),
        CheckConstraint("cost_usd >= 0", name="check_cost_positive"),
        CheckConstraint("spam_score >= 0.0 AND spam_score <= 1.0", name="check_spam_score_range"),
        
        # Indexes for common queries
        Index("idx_messages_campaign_status", "campaign_id", "status"),
        Index("idx_messages_contact_status", "contact_id", "status"),
        Index("idx_messages_phone_status", "phone_e164", "status"),
        Index("idx_messages_provider_status", "provider", "status"),
        Index("idx_messages_queued_priority", "queued_at", "priority"),
        Index("idx_messages_sent_delivery", "sent_at", "delivery_status"),
        Index("idx_messages_external_id", "external_id"),
        Index("idx_messages_error_code", "error_code", 
              postgresql_where="error_code IS NOT NULL"),
        Index("idx_messages_retry", "retry_count", "status",
              postgresql_where="retry_count > 0"),
        Index("idx_messages_cost_tracking", "cost_usd", "created_at"),
        
        # Performance indexes for analytics
        Index("idx_messages_analytics", "created_at", "status", "delivery_status"),
        Index("idx_messages_daily_stats", "queued_at", "campaign_id", "status"),
    )
    
    @property
    def is_delivered(self) -> bool:
        """Check if message was successfully delivered"""
        return self.delivery_status == DeliveryStatus.DELIVERED
    
    @property
    def is_failed(self) -> bool:
        """Check if message failed"""
        return self.status in [MessageStatus.FAILED, MessageStatus.REJECTED, MessageStatus.EXPIRED]
    
    @property
    def is_pending(self) -> bool:
        """Check if message is still pending"""
        return self.status in [MessageStatus.QUEUED, MessageStatus.SENDING, MessageStatus.SENT]
    
    @property
    def delivery_time_seconds(self) -> int:
        """Calculate delivery time in seconds"""
        if self.sent_at and self.delivered_at:
            return int((self.delivered_at - self.sent_at).total_seconds())
        return 0
    
    @property
    def queue_time_seconds(self) -> int:
        """Calculate queue time in seconds"""
        if self.queued_at and self.sent_at:
            return int((self.sent_at - self.queued_at).total_seconds())
        return 0
    
    def calculate_sms_parts(self):
        """Calculate number of SMS parts based on message length"""
        if not self.message_content:
            return 1
        
        # Standard SMS is 160 characters, but with unicode it's 70
        # For simplicity, we'll use 160 as base
        length = len(self.message_content)
        if length <= 160:
            return 1
        else:
            return (length - 1) // 153 + 1  # 153 chars for subsequent parts
    
    def update_status(self, new_status: MessageStatus, error_code: str = None, 
                     error_message: str = None):
        """Update message status with error handling"""
        from datetime import datetime
        
        self.status = new_status
        
        if error_code:
            self.error_code = error_code
        if error_message:
            self.error_message = error_message
            
        if new_status == MessageStatus.SENT and not self.sent_at:
            self.sent_at = datetime.utcnow()
        elif new_status in [MessageStatus.FAILED, MessageStatus.REJECTED] and not self.failed_at:
            self.failed_at = datetime.utcnow()
    
    def update_delivery_status(self, delivery_status: DeliveryStatus):
        """Update delivery status"""
        from datetime import datetime
        
        self.delivery_status = delivery_status
        
        if delivery_status == DeliveryStatus.DELIVERED and not self.delivered_at:
            self.delivered_at = datetime.utcnow()
            self.status = MessageStatus.DELIVERED
    
    def __repr__(self):
        return f"<Message(id={self.id}, phone={self.phone_e164}, status={self.status.value})>"