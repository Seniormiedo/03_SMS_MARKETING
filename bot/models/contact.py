"""
Contact model for Contact Extractor Bot
Represents contact data structure and validation
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator


class ContactStatus(str, Enum):
    """Contact status enumeration"""
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


class Contact(BaseModel):
    """
    Contact data model for extraction operations
    Represents a single contact with all relevant information
    """
    
    id: int = Field(..., description="Unique contact ID")
    phone_e164: str = Field(..., description="Phone in E.164 format (+52xxxxxxxxxx)")
    phone_national: str = Field(..., description="Phone in national format (xxxxxxxxxx)")
    phone_original: Optional[str] = Field(None, description="Original phone format")
    
    # Personal information
    full_name: Optional[str] = Field(None, description="Full name of contact")
    
    # Geographic information
    address: Optional[str] = Field(None, description="Full address")
    neighborhood: Optional[str] = Field(None, description="Neighborhood/Colony")
    lada: Optional[str] = Field(None, description="Area code (3 digits)")
    state_code: Optional[str] = Field(None, description="State code (e.g., CDMX, JAL)")
    state_name: Optional[str] = Field(None, description="Full state name")
    municipality: Optional[str] = Field(None, description="Municipality/Delegation")
    city: Optional[str] = Field(None, description="City name")
    
    # Technical information
    is_mobile: bool = Field(default=True, description="Is mobile phone")
    operator: Optional[str] = Field(None, description="Phone operator (Telcel, Telmex)")
    
    # Status and management
    status: ContactStatus = Field(default=ContactStatus.UNKNOWN, description="Contact status")
    status_updated_at: Optional[datetime] = Field(None, description="Status update timestamp")
    status_source: Optional[str] = Field(None, description="Status update source")
    
    # Usage tracking
    send_count: int = Field(default=0, description="Number of SMS sent")
    last_sent_at: Optional[datetime] = Field(None, description="Last SMS sent timestamp")
    
    # Opt-out management
    opt_out_at: Optional[datetime] = Field(None, description="Opt-out timestamp")
    opt_out_method: Optional[str] = Field(None, description="Opt-out method")
    
    # Validation
    last_validated_at: Optional[datetime] = Field(None, description="Last validation timestamp")
    validation_attempts: int = Field(default=0, description="Validation attempts count")
    
    # Metadata
    source: str = Field(default="TELCEL2022", description="Data source")
    import_batch_id: Optional[str] = Field(None, description="Import batch ID")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")
    
    @validator("phone_national")
    def validate_phone_national(cls, v):
        """Validate national phone format"""
        if v and len(v) != 10:
            raise ValueError("National phone must be 10 digits")
        return v
    
    @validator("phone_e164")
    def validate_phone_e164(cls, v):
        """Validate E.164 phone format"""
        if not v.startswith("+52"):
            raise ValueError("E.164 phone must start with +52")
        if len(v) != 13:  # +52 + 10 digits
            raise ValueError("E.164 phone must be 13 characters (+52xxxxxxxxxx)")
        return v
    
    @validator("lada")
    def validate_lada(cls, v):
        """Validate LADA format"""
        if v and len(v) != 3:
            raise ValueError("LADA must be 3 digits")
        return v
    
    def get_formatted_phone(self, digits: int = 12) -> str:
        """
        Get phone number formatted to specified digits
        
        Args:
            digits: Number of digits (10, 12, or 13)
            
        Returns:
            str: Formatted phone number
        """
        if digits == 10:
            return self.phone_national
        elif digits == 12:
            return "52" + self.phone_national
        elif digits == 13:
            return self.phone_e164
        else:
            raise ValueError("Digits must be 10, 12, or 13")
    
    def get_display_location(self) -> str:
        """
        Get formatted location for display
        
        Returns:
            str: Formatted location string
        """
        # Special handling for validation numbers
        if self.state_name == "VALIDACION":
            return "VALIDACION"
            
        if self.city:
            return self.city.upper()
        elif self.municipality:
            return self.municipality.upper()
        elif self.state_name:
            return self.state_name.upper()
        else:
            return "UNKNOWN"
    
    def is_available_for_extraction(self) -> bool:
        """
        Check if contact is available for extraction
        
        Returns:
            bool: True if contact can be extracted
        """
        return (
            self.status == ContactStatus.VERIFIED and
            self.opt_out_at is None
        )
    
    def can_be_used_for_sms(self) -> bool:
        """
        Check if contact can be used for SMS campaigns
        
        Returns:
            bool: True if contact can receive SMS
        """
        return (
            self.is_mobile and
            self.status in [ContactStatus.ACTIVE, ContactStatus.VERIFIED] and
            self.opt_out_at is None
        )
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ContactFilter(BaseModel):
    """
    Filter model for contact queries
    Used to filter contacts by various criteria
    """
    
    # Geographic filters
    state_name: Optional[str] = Field(None, description="Filter by state name")
    state_code: Optional[str] = Field(None, description="Filter by state code")
    city: Optional[str] = Field(None, description="Filter by city")
    municipality: Optional[str] = Field(None, description="Filter by municipality")
    lada: Optional[str] = Field(None, description="Filter by LADA")
    
    # Status filters
    status: Optional[ContactStatus] = Field(None, description="Filter by status")
    is_mobile: Optional[bool] = Field(None, description="Filter by mobile/landline")
    operator: Optional[str] = Field(None, description="Filter by operator")
    
    # Availability filters
    available_only: bool = Field(default=True, description="Only available contacts")
    exclude_opted_out: bool = Field(default=True, description="Exclude opted out contacts")
    
    # Limits
    limit: int = Field(default=1000, ge=1, le=10000, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Results offset")
    
    def to_sql_conditions(self) -> tuple:
        """
        Convert filter to SQL WHERE conditions
        
        Returns:
            tuple: (conditions_list, parameters_dict)
        """
        conditions = []
        params = {}
        
        if self.state_name:
            conditions.append("state_name ILIKE %(state_name)s")
            params["state_name"] = f"%{self.state_name}%"
        
        if self.state_code:
            conditions.append("state_code ILIKE %(state_code)s")
            params["state_code"] = f"%{self.state_code}%"
        
        if self.city:
            conditions.append("city ILIKE %(city)s")
            params["city"] = f"%{self.city}%"
        
        if self.municipality:
            conditions.append("municipality ILIKE %(municipality)s")
            params["municipality"] = f"%{self.municipality}%"
        
        if self.lada:
            conditions.append("lada = %(lada)s")
            params["lada"] = self.lada
        
        if self.status:
            conditions.append("status = %(status)s")
            params["status"] = self.status.value
        
        if self.is_mobile is not None:
            conditions.append("is_mobile = %(is_mobile)s")
            params["is_mobile"] = self.is_mobile
        
        if self.operator:
            conditions.append("operator ILIKE %(operator)s")
            params["operator"] = f"%{self.operator}%"
        
        if self.available_only:
            conditions.append("status = 'VERIFIED'")
        
        if self.exclude_opted_out:
            conditions.append("opt_out_at IS NULL")
        
        return conditions, params


# Export main classes
__all__ = [
    "Contact",
    "ContactStatus", 
    "ContactFilter"
]