"""
Message Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

class MessageBase(BaseModel):
    """Base message schema"""
    phone_e164: str = Field(..., description="Recipient phone number")
    message_content: str = Field(..., description="Message content")

class MessageCreate(MessageBase):
    """Create message schema"""
    campaign_id: Optional[int] = Field(None, description="Associated campaign ID")
    contact_id: Optional[int] = Field(None, description="Associated contact ID")

class MessageUpdate(BaseModel):
    """Update message schema"""
    status: Optional[str] = None
    delivery_status: Optional[str] = None
    error_message: Optional[str] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

class MessageResponse(MessageBase):
    """Message response schema"""
    id: int
    campaign_id: Optional[int] = None
    contact_id: Optional[int] = None
    status: str
    provider: Optional[str] = None
    external_id: Optional[str] = None
    delivery_status: Optional[str] = None
    error_message: Optional[str] = None
    cost_usd: Optional[Decimal] = None
    queued_at: datetime
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MessageStats(BaseModel):
    """Message statistics schema"""
    total_messages: int
    queued_messages: int
    sent_messages: int
    delivered_messages: int
    failed_messages: int
    delivery_rate: float
    total_cost_usd: Optional[Decimal] = None

class BulkMessageCreate(BaseModel):
    """Bulk message creation schema"""
    message_template: str = Field(..., description="Message template")
    contact_filters: dict = Field(..., description="Contact selection filters")
    campaign_id: Optional[int] = Field(None, description="Associated campaign ID")
    send_rate_per_minute: int = Field(100, description="Send rate per minute")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled send time")