"""
Contact Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
import math

class ContactStatusEnum(str, Enum):
    """Contact status for API responses"""
    ACTIVE = "ACTIVE"
    VERIFIED = "VERIFIED"
    INACTIVE = "INACTIVE"
    DISCONNECTED = "DISCONNECTED"
    SUSPENDED = "SUSPENDED"
    UNKNOWN = "UNKNOWN"
    PENDING_VALIDATION = "PENDING_VALIDATION"
    OPTED_OUT = "OPTED_OUT"
    BLOCKED = "BLOCKED"
    BLACKLISTED = "BLACKLISTED"
    INVALID_FORMAT = "INVALID_FORMAT"
    NOT_MOBILE = "NOT_MOBILE"
    CARRIER_ERROR = "CARRIER_ERROR"

class ContactBase(BaseModel):
    """Base contact schema"""
    phone_e164: str = Field(..., description="Phone number in E.164 format")
    phone_national: str = Field(..., description="Phone number in national format")
    full_name: Optional[str] = Field(None, description="Full name of the contact")
    address: Optional[str] = Field(None, description="Address")
    neighborhood: Optional[str] = Field(None, description="Neighborhood/Colony")
    municipality: Optional[str] = Field(None, description="Municipality")
    state_code: Optional[str] = Field(None, description="State code")
    state_name: Optional[str] = Field(None, description="State name")
    city: Optional[str] = Field(None, description="City")
    lada: Optional[str] = Field(None, description="LADA code")

class ContactCreate(ContactBase):
    """Create contact schema"""
    pass

class ContactUpdate(BaseModel):
    """Update contact schema"""
    full_name: Optional[str] = None
    address: Optional[str] = None
    neighborhood: Optional[str] = None
    municipality: Optional[str] = None
    state_code: Optional[str] = None
    state_name: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = None

class ContactResponse(ContactBase):
    """Contact response schema"""
    id: int
    is_mobile: bool
    status: ContactStatusEnum
    status_updated_at: Optional[datetime] = None
    status_source: Optional[str] = None
    operator: Optional[str] = None
    send_count: int = 0
    last_sent_at: Optional[datetime] = None
    opt_out_at: Optional[datetime] = None
    opt_out_method: Optional[str] = None
    last_validated_at: Optional[datetime] = None
    validation_attempts: int = 0
    source: str = "UNKNOWN"
    created_at: datetime
    updated_at: datetime

    # Computed properties
    is_contactable: bool = False
    needs_validation: bool = False
    location_str: str = "Ubicación desconocida"

    class Config:
        from_attributes = True

class ContactsStats(BaseModel):
    """Contacts statistics schema"""
    total_contacts: int
    active_contacts: int
    mobile_contacts: int
    opt_out_contacts: int
    top_states: List[dict]

class ContactFilter(BaseModel):
    """Contact filter schema"""
    state_codes: Optional[List[str]] = None
    ladas: Optional[List[str]] = None
    cities: Optional[List[str]] = None
    operators: Optional[List[str]] = None
    status: Optional[List[ContactStatusEnum]] = None
    is_mobile: Optional[bool] = None
    exclude_recent_contacts: bool = True
    exclude_recent_days: int = 30
    max_send_count: Optional[int] = None
    needs_validation: Optional[bool] = None
    source: Optional[str] = None

class ContactStatusUpdate(BaseModel):
    """Contact status update schema"""
    status: ContactStatusEnum
    source: Optional[str] = None
    reason: Optional[str] = None

class ContactOptOut(BaseModel):
    """Contact opt-out schema"""
    method: str = Field(..., description="Opt-out method (SMS, WEB, CALL)")
    reason: Optional[str] = Field(None, description="Opt-out reason")

class ContactValidation(BaseModel):
    """Contact validation result schema"""
    phone_e164: str
    is_valid: bool
    is_mobile: bool
    operator: Optional[str] = None
    status: ContactStatusEnum
    validation_source: str
    error_message: Optional[str] = None

# NEW SCHEMAS FOR DASHBOARD
class PaginatedContactResponse(BaseModel):
    """Paginated contacts response for dashboard"""
    data: List[ContactResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class ContactStatsEnhanced(BaseModel):
    """Enhanced contacts statistics for dashboard"""
    total_contacts: int
    active_contacts: int
    mobile_contacts: int
    contacts_by_state: Dict[str, int]
    contacts_by_lada: Dict[str, int]
    recent_extractions: int
    growth_rate: float = 0.0

class ContactFilters(BaseModel):
    """Contact filters for dashboard"""
    search_query: Optional[str] = None
    state: Optional[str] = None
    municipality: Optional[str] = None
    lada: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
