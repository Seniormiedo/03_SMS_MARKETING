"""
Extraction model for Contact Extractor Bot
Represents extraction requests, results, and operations
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, validator

from .contact import Contact


class ExtractionType(str, Enum):
    """Extraction type enumeration"""
    PREMIUM = "premium"
    STATE = "state"
    CITY = "city"
    MUNICIPALITY = "municipality"
    LADA = "lada"


class ExportFormat(str, Enum):
    """Export format enumeration"""
    XLSX = "xlsx"
    TXT = "txt"


class ExtractionStatus(str, Enum):
    """Extraction status enumeration"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ExtractionRequest(BaseModel):
    """
    Extraction request model
    Represents a request to extract contacts
    """
    
    # Request parameters
    extraction_type: ExtractionType = Field(..., description="Type of extraction")
    amount: int = Field(..., ge=100, le=10000, description="Number of contacts to extract")
    export_format: ExportFormat = Field(..., description="Export file format")
    location: Optional[str] = Field(None, description="Location filter (state/city/municipality)")
    
    # Request metadata
    request_id: Optional[str] = Field(None, description="Unique request ID")
    requested_at: datetime = Field(default_factory=datetime.now, description="Request timestamp")
    user_id: Optional[str] = Field(None, description="User ID (if applicable)")
    
    # Processing options
    require_confirmation: bool = Field(default=False, description="Requires confirmation")
    confirmed: bool = Field(default=False, description="Confirmation status")
    
    @validator("location")
    def validate_location_required(cls, v, values):
        """Validate location is required for non-premium extractions"""
        extraction_type = values.get("extraction_type")
        if extraction_type != ExtractionType.PREMIUM and not v:
            raise ValueError(f"Location is required for {extraction_type} extraction")
        return v
    
    @validator("amount")
    def validate_amount_range(cls, v):
        """Validate extraction amount is within allowed range"""
        if not 100 <= v <= 10000:
            raise ValueError("Amount must be between 100 and 10000")
        return v
    
    def needs_confirmation(self) -> bool:
        """Check if this request needs confirmation"""
        return self.require_confirmation and self.amount > 5000
    
    def is_confirmed(self) -> bool:
        """Check if this request is confirmed"""
        return not self.needs_confirmation() or self.confirmed
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True


class ExtractionResult(BaseModel):
    """
    Extraction result model
    Represents the result of a contact extraction operation
    """
    
    # Request reference
    request: ExtractionRequest = Field(..., description="Original request")
    
    # Result data
    contacts: List[Contact] = Field(default_factory=list, description="Extracted contacts")
    contact_ids: List[int] = Field(default_factory=list, description="Extracted contact IDs")
    
    # Processing info
    status: ExtractionStatus = Field(default=ExtractionStatus.PENDING, description="Processing status")
    started_at: Optional[datetime] = Field(None, description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Processing completion time")
    
    # File info
    file_path: Optional[str] = Field(None, description="Generated file path")
    file_size: Optional[int] = Field(None, description="Generated file size in bytes")
    file_name: Optional[str] = Field(None, description="Generated file name")
    
    # Statistics
    total_requested: int = Field(default=0, description="Total contacts requested")
    total_found: int = Field(default=0, description="Total contacts found")
    total_extracted: int = Field(default=0, description="Total contacts extracted")
    total_updated: int = Field(default=0, description="Total contacts marked as opted out")
    
    # Performance metrics
    query_time_seconds: Optional[float] = Field(None, description="Database query time")
    export_time_seconds: Optional[float] = Field(None, description="File export time")
    total_time_seconds: Optional[float] = Field(None, description="Total processing time")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if failed")
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")
    
    def get_success_rate(self) -> float:
        """
        Calculate success rate of extraction
        
        Returns:
            float: Success rate as percentage (0-100)
        """
        if self.total_requested == 0:
            return 0.0
        return (self.total_extracted / self.total_requested) * 100
    
    def is_successful(self) -> bool:
        """
        Check if extraction was successful
        
        Returns:
            bool: True if extraction completed successfully
        """
        return (
            self.status == ExtractionStatus.COMPLETED and
            self.total_extracted > 0 and
            self.file_path is not None
        )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary
        
        Returns:
            dict: Performance metrics summary
        """
        return {
            "total_time": self.total_time_seconds,
            "query_time": self.query_time_seconds,
            "export_time": self.export_time_seconds,
            "contacts_per_second": (
                self.total_extracted / self.total_time_seconds 
                if self.total_time_seconds and self.total_time_seconds > 0 
                else 0
            ),
            "success_rate": self.get_success_rate()
        }
    
    def add_warning(self, warning: str):
        """Add a warning message"""
        self.warnings.append(f"{datetime.now().isoformat()}: {warning}")
    
    def mark_started(self):
        """Mark extraction as started"""
        self.status = ExtractionStatus.PROCESSING
        self.started_at = datetime.now()
    
    def mark_completed(self, file_path: str, file_size: int):
        """Mark extraction as completed"""
        self.status = ExtractionStatus.COMPLETED
        self.completed_at = datetime.now()
        self.file_path = file_path
        self.file_size = file_size
        self.file_name = file_path.split("/")[-1] if "/" in file_path else file_path
        
        if self.started_at:
            self.total_time_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def mark_failed(self, error_message: str):
        """Mark extraction as failed"""
        self.status = ExtractionStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error_message
        
        if self.started_at:
            self.total_time_seconds = (self.completed_at - self.started_at).total_seconds()
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ExtractionStats(BaseModel):
    """
    Extraction statistics model
    Represents system-wide extraction statistics
    """
    
    # Daily stats
    daily_extractions: int = Field(default=0, description="Extractions today")
    daily_contacts: int = Field(default=0, description="Contacts extracted today")
    
    # Hourly stats  
    hourly_extractions: int = Field(default=0, description="Extractions this hour")
    hourly_contacts: int = Field(default=0, description="Contacts extracted this hour")
    
    # System availability
    total_contacts_available: int = Field(default=0, description="Total contacts available")
    premium_contacts_available: int = Field(default=0, description="Premium contacts available")
    
    # Usage by type
    premium_extractions_today: int = Field(default=0, description="Premium extractions today")
    state_extractions_today: int = Field(default=0, description="State extractions today")
    city_extractions_today: int = Field(default=0, description="City extractions today")
    
    # Format preferences
    xlsx_exports_today: int = Field(default=0, description="XLSX exports today")
    txt_exports_today: int = Field(default=0, description="TXT exports today")
    
    # Performance
    average_extraction_time: Optional[float] = Field(None, description="Average extraction time")
    average_success_rate: Optional[float] = Field(None, description="Average success rate")
    
    def can_extract(self, amount: int, max_daily: int = 50000, max_hourly: int = 10) -> bool:
        """
        Check if extraction is allowed based on limits
        
        Args:
            amount: Requested extraction amount
            max_daily: Maximum daily extractions
            max_hourly: Maximum hourly extractions
            
        Returns:
            bool: True if extraction is allowed
        """
        return (
            self.daily_contacts + amount <= max_daily and
            self.hourly_extractions < max_hourly
        )
    
    def get_availability_summary(self) -> Dict[str, Any]:
        """
        Get availability summary
        
        Returns:
            dict: Availability summary
        """
        return {
            "total_available": self.total_contacts_available,
            "premium_available": self.premium_contacts_available,
            "daily_usage": f"{self.daily_contacts:,}",
            "daily_remaining": f"{50000 - self.daily_contacts:,}",
            "hourly_usage": f"{self.hourly_extractions}/10"
        }


# Export main classes
__all__ = [
    "ExtractionRequest",
    "ExtractionResult", 
    "ExtractionStats",
    "ExtractionType",
    "ExportFormat",
    "ExtractionStatus"
]