"""
Campaign Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CampaignBase(BaseModel):
    """Base campaign schema"""
    name: str = Field(..., description="Campaign name")
    message_template: str = Field(..., description="SMS message template")
    target_states: Optional[List[str]] = Field(None, description="Target state codes")
    target_ladas: Optional[List[str]] = Field(None, description="Target LADA codes")
    target_cities: Optional[List[str]] = Field(None, description="Target cities")
    max_recipients: Optional[int] = Field(None, description="Maximum number of recipients")
    send_rate_per_minute: int = Field(100, description="Send rate per minute")

class CampaignCreate(CampaignBase):
    """Create campaign schema"""
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled send time")

class CampaignUpdate(BaseModel):
    """Update campaign schema"""
    name: Optional[str] = None
    message_template: Optional[str] = None
    target_states: Optional[List[str]] = None
    target_ladas: Optional[List[str]] = None
    target_cities: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None
    max_recipients: Optional[int] = None
    send_rate_per_minute: Optional[int] = None
    status: Optional[str] = None

class CampaignResponse(CampaignBase):
    """Campaign response schema"""
    id: int
    status: str
    scheduled_at: Optional[datetime] = None
    sent_count: int = 0
    delivered_count: int = 0
    failed_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CampaignStats(BaseModel):
    """Campaign statistics schema"""
    campaign_id: int
    total_recipients: int
    delivered_count: int
    failed_count: int
    pending_count: int
    delivery_rate: float

class CampaignPreview(BaseModel):
    """Campaign preview schema"""
    estimated_recipients: int
    estimated_cost: float
    estimated_duration_minutes: int
    sample_contacts: List[dict]