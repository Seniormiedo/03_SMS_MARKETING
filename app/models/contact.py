"""
Contact Model - Represents phone numbers and contact information
"""

from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, Text, Index,
    CheckConstraint, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class ContactStatus(str, enum.Enum):
    """
    Contact status enumeration for phone line states
    """
    # Active statuses
    ACTIVE = "ACTIVE"                    # Línea activa y operativa
    VERIFIED = "VERIFIED"                # Línea verificada recientemente

    # Inactive statuses
    INACTIVE = "INACTIVE"                # Línea inactiva o suspendida
    DISCONNECTED = "DISCONNECTED"       # Línea desconectada permanentemente
    SUSPENDED = "SUSPENDED"              # Línea suspendida temporalmente

    # Unknown/Pending statuses
    UNKNOWN = "UNKNOWN"                  # Estado desconocido (necesita validación)
    PENDING_VALIDATION = "PENDING_VALIDATION"  # En proceso de validación

    # Blocked/Opted out statuses
    OPTED_OUT = "OPTED_OUT"             # Usuario solicitó exclusión (STOP/BAJA)
    BLOCKED = "BLOCKED"                 # Bloqueado por spam o abuso
    BLACKLISTED = "BLACKLISTED"         # En lista negra permanente

    # Error statuses
    INVALID_FORMAT = "INVALID_FORMAT"   # Formato de número inválido
    NOT_MOBILE = "NOT_MOBILE"          # No es número móvil
    CARRIER_ERROR = "CARRIER_ERROR"    # Error del carrier/operadora


class Contact(BaseModel):
    """
    Contact model for storing phone numbers and associated information
    """
    __tablename__ = "contacts"

    # Phone number fields (required)
    phone_e164 = Column(String(15), unique=True, nullable=False, index=True,
                       comment="Phone number in E.164 international format (+52...)")
    phone_national = Column(String(12), nullable=False, index=True,
                           comment="Phone number in national format (10 digits)")
    phone_original = Column(String(20), nullable=True,
                           comment="Original phone number as imported")

    # Contact information (optional)
    full_name = Column(String(255), nullable=True, index=True,
                      comment="Full name of the contact")
    address = Column(Text, nullable=True,
                    comment="Street address")
    neighborhood = Column(String(100), nullable=True,
                         comment="Neighborhood/Colony (Colonia)")

    # Geographic information
    lada = Column(String(3), nullable=True, index=True,
                 comment="LADA code (area code)")
    state_code = Column(String(5), nullable=True, index=True,
                       comment="State code (e.g., 'CDMX', 'JAL', 'NL')")
    state_name = Column(String(50), nullable=True,
                       comment="Full state name")
    municipality = Column(String(100), nullable=True, index=True,
                         comment="Municipality")
    city = Column(String(100), nullable=True, index=True,
                 comment="City name")

    # Phone line characteristics
    is_mobile = Column(Boolean, default=True, nullable=False, index=True,
                      comment="True if mobile number, False if landline")
    operator = Column(String(50), nullable=True, index=True,
                     comment="Mobile operator/carrier (Telcel, Movistar, AT&T, etc.)")

    # Status tracking (CRITICAL FIELD)
    status = Column(SQLEnum(ContactStatus), default=ContactStatus.UNKNOWN,
                   nullable=False, index=True,
                   comment="Current status of the phone line")
    status_updated_at = Column(DateTime(timezone=True), nullable=True,
                              comment="When status was last updated")
    status_source = Column(String(50), nullable=True,
                          comment="Source of status information (telnyx, twilio, manual)")

    # SMS sending control
    send_count = Column(Integer, default=0, nullable=False,
                       comment="Total number of SMS sent to this contact")
    last_sent_at = Column(DateTime(timezone=True), nullable=True, index=True,
                         comment="When last SMS was sent")

    # Opt-out management
    opt_out_at = Column(DateTime(timezone=True), nullable=True, index=True,
                       comment="When contact opted out (STOP/BAJA received)")
    opt_out_method = Column(String(20), nullable=True,
                           comment="How they opted out (SMS, WEB, CALL)")

    # Validation tracking
    last_validated_at = Column(DateTime(timezone=True), nullable=True,
                              comment="When number was last validated")
    validation_attempts = Column(Integer, default=0, nullable=False,
                                comment="Number of validation attempts")

    # Data source tracking
    source = Column(String(50), default="TELCEL2022", nullable=False,
                   comment="Original data source")
    import_batch_id = Column(String(50), nullable=True,
                            comment="Batch ID from import process")

    # Relationships (commented for now - Message model not implemented yet)
    # messages = relationship("Message", back_populates="contact", lazy="dynamic")

    # Constraints
    __table_args__ = (
        # Ensure phone numbers are properly formatted
        CheckConstraint("phone_e164 ~ '^\\+52[0-9]{10}$'", name="check_phone_e164_format"),
        CheckConstraint("phone_national ~ '^[0-9]{10}$'", name="check_phone_national_format"),
        CheckConstraint("send_count >= 0", name="check_send_count_positive"),
        CheckConstraint("validation_attempts >= 0", name="check_validation_attempts_positive"),

        # Indexes for common queries
        Index("idx_contacts_active_mobile", "status", "is_mobile",
              postgresql_where="status IN ('ACTIVE', 'VERIFIED') AND opt_out_at IS NULL"),
        Index("idx_contacts_state_status", "state_code", "status"),
        Index("idx_contacts_lada_status", "lada", "status"),
        Index("idx_contacts_city_status", "city", "status"),
        Index("idx_contacts_last_sent", "last_sent_at",
              postgresql_where="last_sent_at IS NOT NULL"),
        Index("idx_contacts_opt_out", "opt_out_at",
              postgresql_where="opt_out_at IS NOT NULL"),
        Index("idx_contacts_operator_status", "operator", "status"),
        Index("idx_contacts_send_frequency", "send_count", "last_sent_at"),

        # Full text search indexes
        Index("idx_contacts_name_search", "full_name",
              postgresql_using="gin", postgresql_ops={"full_name": "gin_trgm_ops"}),
        Index("idx_contacts_address_search", "address",
              postgresql_using="gin", postgresql_ops={"address": "gin_trgm_ops"}),
    )

    @property
    def is_contactable(self) -> bool:
        """Check if contact can receive SMS"""
        return (
            self.status in [ContactStatus.ACTIVE, ContactStatus.VERIFIED] and
            self.opt_out_at is None and
            self.is_mobile
        )

    @property
    def needs_validation(self) -> bool:
        """Check if contact needs status validation"""
        return self.status in [
            ContactStatus.UNKNOWN,
            ContactStatus.PENDING_VALIDATION
        ]

    @property
    def display_name(self) -> str:
        """Get display name for contact"""
        return self.full_name or self.phone_national

    @property
    def location_str(self) -> str:
        """Get formatted location string"""
        parts = []
        if self.city:
            parts.append(self.city)
        if self.state_name:
            parts.append(self.state_name)
        return ", ".join(parts) if parts else "Ubicación desconocida"

    def update_status(self, new_status: ContactStatus, source: str = None):
        """Update contact status with tracking"""
        from datetime import datetime
        self.status = new_status
        self.status_updated_at = datetime.utcnow()
        if source:
            self.status_source = source

    def mark_opted_out(self, method: str = "SMS"):
        """Mark contact as opted out"""
        from datetime import datetime
        self.status = ContactStatus.OPTED_OUT
        self.opt_out_at = datetime.utcnow()
        self.opt_out_method = method
        self.status_updated_at = datetime.utcnow()

    def __repr__(self):
        return f"<Contact(id={self.id}, phone={self.phone_national}, status={self.status.value})>"
