"""
Contact Domain Entity

This module defines the Contact entity following Domain-Driven Design principles.
Represents a contact in the SMS marketing system with comprehensive validation
and business logic.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from decimal import Decimal

from pydantic import BaseModel, Field, validator, root_validator


class ContactStatus(str, Enum):
    """Contact status enumeration with comprehensive states."""

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


class QualityTier(str, Enum):
    """Lead quality tier classification."""

    PREMIUM = "PREMIUM"      # 90-100 points
    HIGH = "HIGH"           # 75-89 points
    MEDIUM = "MEDIUM"       # 50-74 points
    LOW = "LOW"             # 25-49 points
    POOR = "POOR"           # 0-24 points


@dataclass
class PlatformValidation:
    """Platform validation result for a contact."""

    platform: str
    is_active: bool
    confidence_score: float
    validated_at: datetime
    response_time_ms: int
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate platform validation data."""
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("Confidence score must be between 0 and 1")
        if self.response_time_ms < 0:
            raise ValueError("Response time cannot be negative")


@dataclass
class LeadScore:
    """Lead scoring information for a contact."""

    total_score: int
    platform_scores: Dict[str, int]
    quality_tier: QualityTier
    confidence_level: float
    calculated_at: datetime
    factors: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate lead score data."""
        if not 0 <= self.total_score <= 100:
            raise ValueError("Total score must be between 0 and 100")
        if not 0 <= self.confidence_level <= 1:
            raise ValueError("Confidence level must be between 0 and 1")


class Contact(BaseModel):
    """
    Contact domain entity representing a phone contact in the SMS marketing system.

    This entity encapsulates all contact-related data and business logic,
    following Clean Architecture principles and Domain-Driven Design.
    """

    # Identity
    id: int = Field(..., description="Unique contact identifier")

    # Phone Information
    phone_e164: str = Field(..., description="Phone in E.164 format (+52xxxxxxxxxx)")
    phone_national: str = Field(..., description="Phone in national format (xxxxxxxxxx)")
    phone_original: Optional[str] = Field(None, description="Original phone format from source")

    # Personal Information
    full_name: Optional[str] = Field(None, description="Full name of the contact")

    # Geographic Information
    address: Optional[str] = Field(None, description="Complete address")
    neighborhood: Optional[str] = Field(None, description="Neighborhood or colony")
    lada: Optional[str] = Field(None, description="Area code (3 digits)")
    state_code: Optional[str] = Field(None, description="State code (e.g., CDMX, JAL)")
    state_name: Optional[str] = Field(None, description="Full state name")
    municipality: Optional[str] = Field(None, description="Municipality or delegation")
    city: Optional[str] = Field(None, description="City name")

    # Technical Information
    is_mobile: bool = Field(default=True, description="Whether this is a mobile phone")
    operator: Optional[str] = Field(None, description="Phone operator (Telcel, Telmex, etc.)")

    # Status Management
    status: ContactStatus = Field(default=ContactStatus.UNKNOWN, description="Current contact status")
    status_updated_at: Optional[datetime] = Field(None, description="When status was last updated")
    status_source: Optional[str] = Field(None, description="Source of status update")

    # Campaign Management
    send_count: int = Field(default=0, description="Number of SMS messages sent")
    last_sent_at: Optional[datetime] = Field(None, description="When last SMS was sent")

    # Opt-out Management
    opt_out_at: Optional[datetime] = Field(None, description="When contact opted out")
    opt_out_method: Optional[str] = Field(None, description="Method used to opt out")

    # Validation Information
    last_validated_at: Optional[datetime] = Field(None, description="Last validation timestamp")
    validation_attempts: int = Field(default=0, description="Number of validation attempts")

    # Lead Scoring
    lead_score: Optional[LeadScore] = Field(None, description="Current lead scoring information")
    platform_validations: List[PlatformValidation] = Field(
        default_factory=list,
        description="Platform validation results"
    )

    # Metadata
    source: str = Field(default="TELCEL2022", description="Data source identifier")
    import_batch_id: Optional[str] = Field(None, description="Import batch identifier")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            Decimal: lambda v: float(v) if v else None,
        }
        schema_extra = {
            "example": {
                "id": 1,
                "phone_e164": "+525551234567",
                "phone_national": "5551234567",
                "full_name": "Juan Pérez",
                "state_name": "CDMX",
                "city": "Ciudad de México",
                "lada": "55",
                "is_mobile": True,
                "operator": "Telcel",
                "status": "VERIFIED",
                "lead_score": {
                    "total_score": 85,
                    "quality_tier": "HIGH",
                    "confidence_level": 0.92
                }
            }
        }

    @validator("phone_national")
    def validate_phone_national(cls, v: str) -> str:
        """Validate national phone format."""
        if v and len(v) != 10:
            raise ValueError("National phone must be exactly 10 digits")
        if v and not v.isdigit():
            raise ValueError("National phone must contain only digits")
        return v

    @validator("phone_e164")
    def validate_phone_e164(cls, v: str) -> str:
        """Validate E.164 phone format."""
        if not v.startswith("+52"):
            raise ValueError("E.164 phone must start with +52 for Mexico")
        if len(v) != 13:  # +52 + 10 digits
            raise ValueError("E.164 phone must be exactly 13 characters (+52xxxxxxxxxx)")
        if not v[3:].isdigit():
            raise ValueError("E.164 phone must contain only digits after +52")
        return v

    @validator("lada")
    def validate_lada(cls, v: Optional[str]) -> Optional[str]:
        """Validate LADA format."""
        if v and len(v) != 3:
            raise ValueError("LADA must be exactly 3 digits")
        if v and not v.isdigit():
            raise ValueError("LADA must contain only digits")
        return v

    @validator("send_count")
    def validate_send_count(cls, v: int) -> int:
        """Validate send count is non-negative."""
        if v < 0:
            raise ValueError("Send count cannot be negative")
        return v

    @validator("validation_attempts")
    def validate_validation_attempts(cls, v: int) -> int:
        """Validate validation attempts is non-negative."""
        if v < 0:
            raise ValueError("Validation attempts cannot be negative")
        return v

    @root_validator
    def validate_phone_consistency(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure phone formats are consistent."""
        phone_e164 = values.get("phone_e164")
        phone_national = values.get("phone_national")

        if phone_e164 and phone_national:
            expected_national = phone_e164[3:]  # Remove +52
            if phone_national != expected_national:
                raise ValueError("Phone E.164 and national formats are inconsistent")

        return values

    def get_formatted_phone(self, digits: int = 12) -> str:
        """
        Get phone number formatted to specified digits.

        Args:
            digits: Number of digits (10, 12, or 13)

        Returns:
            Formatted phone number

        Raises:
            ValueError: If digits parameter is invalid
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
        Get formatted location for display purposes.

        Returns:
            Formatted location string with priority: city > municipality > state > unknown
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
        Check if contact is available for campaign extraction.

        Returns:
            True if contact can be used in campaigns
        """
        return (
            self.status == ContactStatus.VERIFIED and
            self.opt_out_at is None and
            self.is_mobile
        )

    def can_receive_sms(self) -> bool:
        """
        Check if contact can receive SMS messages.

        Returns:
            True if contact can receive SMS
        """
        return (
            self.is_mobile and
            self.status in [ContactStatus.ACTIVE, ContactStatus.VERIFIED] and
            self.opt_out_at is None and
            self.status not in [ContactStatus.BLOCKED, ContactStatus.BLACKLISTED]
        )

    def get_platform_validation(self, platform: str) -> Optional[PlatformValidation]:
        """
        Get validation result for a specific platform.

        Args:
            platform: Platform name (whatsapp, instagram, etc.)

        Returns:
            Platform validation result or None if not found
        """
        for validation in self.platform_validations:
            if validation.platform.lower() == platform.lower():
                return validation
        return None

    def add_platform_validation(self, validation: PlatformValidation) -> None:
        """
        Add or update platform validation result.

        Args:
            validation: Platform validation result to add
        """
        # Remove existing validation for the same platform
        self.platform_validations = [
            v for v in self.platform_validations
            if v.platform.lower() != validation.platform.lower()
        ]

        # Add new validation
        self.platform_validations.append(validation)

    def calculate_quality_score(self) -> int:
        """
        Calculate quality score based on platform validations.

        Returns:
            Quality score from 0 to 100
        """
        if not self.platform_validations:
            return 0

        # Platform weights (total = 100)
        platform_weights = {
            "whatsapp": 25,
            "facebook": 20,
            "instagram": 20,
            "google": 20,
            "apple": 15
        }

        total_score = 0
        for validation in self.platform_validations:
            platform = validation.platform.lower()
            weight = platform_weights.get(platform, 0)

            if validation.is_active:
                # Apply confidence score as multiplier
                score = weight * validation.confidence_score
                total_score += score

        return min(100, int(total_score))

    def update_lead_score(self) -> None:
        """Update lead score based on current platform validations."""
        if not self.platform_validations:
            self.lead_score = None
            return

        total_score = self.calculate_quality_score()

        # Determine quality tier
        if total_score >= 90:
            tier = QualityTier.PREMIUM
        elif total_score >= 75:
            tier = QualityTier.HIGH
        elif total_score >= 50:
            tier = QualityTier.MEDIUM
        elif total_score >= 25:
            tier = QualityTier.LOW
        else:
            tier = QualityTier.POOR

        # Calculate confidence level based on number of validations
        confidence = min(1.0, len(self.platform_validations) / 5.0)

        # Create platform scores dictionary
        platform_scores = {}
        for validation in self.platform_validations:
            platform_weights = {
                "whatsapp": 25, "facebook": 20, "instagram": 20,
                "google": 20, "apple": 15
            }
            weight = platform_weights.get(validation.platform.lower(), 0)
            score = int(weight * validation.confidence_score) if validation.is_active else 0
            platform_scores[validation.platform] = score

        self.lead_score = LeadScore(
            total_score=total_score,
            platform_scores=platform_scores,
            quality_tier=tier,
            confidence_level=confidence,
            calculated_at=datetime.utcnow()
        )

    def mark_as_opted_out(self, method: str = "MANUAL") -> None:
        """
        Mark contact as opted out from campaigns.

        Args:
            method: Method used for opt-out (MANUAL, SMS_REPLY, WEB, etc.)
        """
        self.opt_out_at = datetime.utcnow()
        self.opt_out_method = method
        self.status = ContactStatus.OPTED_OUT
        self.status_updated_at = datetime.utcnow()
        self.status_source = f"OPT_OUT_{method}"

    def increment_send_count(self) -> None:
        """Increment SMS send count and update last sent timestamp."""
        self.send_count += 1
        self.last_sent_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_status(self, new_status: ContactStatus, source: str = "SYSTEM") -> None:
        """
        Update contact status with audit trail.

        Args:
            new_status: New status to set
            source: Source of the status update
        """
        if self.status != new_status:
            self.status = new_status
            self.status_updated_at = datetime.utcnow()
            self.status_source = source
            self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert contact to dictionary representation.

        Returns:
            Dictionary representation of the contact
        """
        return {
            "id": self.id,
            "phone_e164": self.phone_e164,
            "phone_national": self.phone_national,
            "full_name": self.full_name,
            "location": self.get_display_location(),
            "is_mobile": self.is_mobile,
            "operator": self.operator,
            "status": self.status.value,
            "lead_score": self.lead_score.total_score if self.lead_score else 0,
            "quality_tier": self.lead_score.quality_tier.value if self.lead_score else "UNKNOWN",
            "platform_count": len(self.platform_validations),
            "send_count": self.send_count,
            "last_sent_at": self.last_sent_at.isoformat() if self.last_sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __str__(self) -> str:
        """String representation of contact."""
        return f"Contact(id={self.id}, phone={self.phone_e164}, status={self.status.value})"

    def __repr__(self) -> str:
        """Detailed string representation of contact."""
        return (
            f"Contact(id={self.id}, phone_e164='{self.phone_e164}', "
            f"status={self.status.value}, location='{self.get_display_location()}', "
            f"score={self.lead_score.total_score if self.lead_score else 0})"
        )
