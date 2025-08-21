# 📊 FASE 2: EXPANSIÓN DE BASE DE DATOS (Días 3-4)

## SMS Marketing Platform v2.0 - Migración Sistema Actual

---

## 🎯 OBJETIVO DE LA FASE

Expandir la base de datos PostgreSQL existente con nuevas tablas para validación multi-plataforma y lead scoring, manteniendo compatibilidad total con el sistema actual.

**Duración:** 2 días
**Complejidad:** ALTA
**Riesgo:** MEDIO - Modificaciones a BD en producción
**Prioridad:** CRÍTICA

---

## 📊 ANÁLISIS DE LA BASE ACTUAL

### **✅ ESTRUCTURA EXISTENTE:**

#### **Tabla `contacts` (31.8M registros):**

```sql
-- CAMPOS ACTUALES QUE SE MANTIENEN
id                  INTEGER PRIMARY KEY
phone_e164          VARCHAR(15) UNIQUE NOT NULL
phone_national      VARCHAR(12) NOT NULL
full_name           VARCHAR(255)
lada                VARCHAR(3)
state_name          VARCHAR(50)
municipality        VARCHAR(100)
is_mobile           BOOLEAN DEFAULT TRUE
status              CONTACTSTATUS DEFAULT 'UNKNOWN'
created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
-- ... más campos existentes
```

#### **Índices Críticos Existentes:**

- ✅ `contacts_phone_e164_key` (UNIQUE)
- ✅ `idx_contacts_premium_extraction`
- ✅ `idx_contacts_location_extraction`
- ✅ `idx_contacts_active_mobile`

### **🆕 EXPANSIONES NECESARIAS:**

#### **1. Nuevas Columnas en `contacts`:**

```sql
-- AGREGAR A TABLA EXISTENTE (sin afectar datos actuales)
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS
    whatsapp_validated BOOLEAN DEFAULT NULL;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS
    instagram_validated BOOLEAN DEFAULT NULL;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS
    facebook_validated BOOLEAN DEFAULT NULL;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS
    google_validated BOOLEAN DEFAULT NULL;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS
    apple_validated BOOLEAN DEFAULT NULL;

-- Metadatos de validación
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS
    last_platform_validation TIMESTAMP WITH TIME ZONE DEFAULT NULL;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS
    platform_validation_count INTEGER DEFAULT 0;

-- Lead scoring
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS
    lead_score INTEGER DEFAULT NULL CHECK (lead_score >= 0 AND lead_score <= 100);
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS
    lead_tier VARCHAR(20) DEFAULT 'UNKNOWN' CHECK (lead_tier IN ('PREMIUM', 'HIGH', 'MEDIUM', 'LOW', 'POOR', 'UNKNOWN'));
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS
    last_scored_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;
```

---

## 📅 DÍA 3: NUEVAS TABLAS Y MIGRACIONES

### 🌅 **MAÑANA (4 horas): Creación de Tablas Principales**

#### ✅ **BLOQUE 1: Tabla platform_validations (1.5 horas)**

**Tarea 1.1: Crear migración**

```python
# migrations/versions/003_platform_validations.py
"""Add platform validations table

Revision ID: 003
Revises: 002
Create Date: 2025-08-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade() -> None:
    # Create platform_validations table
    op.create_table(
        'platform_validations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('phone_e164', sa.String(length=15), nullable=False),
        sa.Column('platform', sa.String(length=20), nullable=False),

        # Validation results
        sa.Column('is_valid', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_business', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_premium', sa.Boolean(), nullable=True, default=False),
        sa.Column('confidence_score', sa.Numeric(precision=3, scale=2), nullable=False, default=0.50),

        # Platform-specific data
        sa.Column('platform_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default={}),
        sa.Column('profile_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default={}),

        # Validation metadata
        sa.Column('validation_method', sa.String(length=50), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('validation_source', sa.String(length=100), nullable=True),
        sa.Column('user_agent_used', sa.String(length=200), nullable=True),
        sa.Column('proxy_used', sa.String(length=100), nullable=True),

        # Cache and expiration
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=False, default=sa.text('NOW()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, default=sa.text("NOW() + INTERVAL '24 hours'")),

        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=sa.text('NOW()')),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('phone_e164', 'platform', name='uq_phone_platform'),
        sa.CheckConstraint('confidence_score >= 0.00 AND confidence_score <= 1.00', name='ck_confidence_range'),
        sa.CheckConstraint("platform IN ('whatsapp', 'instagram', 'facebook', 'google', 'apple')", name='ck_platform_values')
    )

    # Create optimized indexes
    op.create_index('idx_platform_validations_contact_id', 'platform_validations', ['contact_id'])
    op.create_index('idx_platform_validations_phone_platform', 'platform_validations', ['phone_e164', 'platform'])
    op.create_index('idx_platform_validations_valid', 'platform_validations', ['is_valid'], postgresql_where=sa.text('is_valid = TRUE'))
    op.create_index('idx_platform_validations_expires', 'platform_validations', ['expires_at'], postgresql_where=sa.text('expires_at > NOW()'))
    op.create_index('idx_platform_validations_platform', 'platform_validations', ['platform'])
    op.create_index('idx_platform_validations_business', 'platform_validations', ['is_business'], postgresql_where=sa.text('is_business = TRUE'))

def downgrade() -> None:
    op.drop_table('platform_validations')
```

**Tarea 1.2: Crear modelo SQLAlchemy**

```python
# app/models/platform_validation.py - NUEVO ARCHIVO
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import BaseModel

class PlatformValidation(BaseModel):
    """Platform validation results for contacts"""
    __tablename__ = "platform_validations"

    # Relationships
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    contact = relationship("Contact", back_populates="platform_validations")

    # Platform identification
    phone_e164 = Column(String(15), nullable=False, index=True)
    platform = Column(String(20), nullable=False, index=True)

    # Validation results
    is_valid = Column(Boolean, nullable=False, default=False, index=True)
    is_business = Column(Boolean, nullable=True, default=False)
    is_premium = Column(Boolean, nullable=True, default=False)
    confidence_score = Column(Numeric(3, 2), nullable=False, default=0.50)

    # Platform-specific data
    platform_details = Column(JSONB, nullable=True, default={})
    profile_info = Column(JSONB, nullable=True, default={})

    # Validation metadata
    validation_method = Column(String(50), nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    validation_source = Column(String(100), nullable=True)
    user_agent_used = Column(String(200), nullable=True)
    proxy_used = Column(String(100), nullable=True)

    # Cache and expiration
    validated_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, default=func.now() + func.make_interval(hours=24))

    # Constraints
    __table_args__ = (
        CheckConstraint('confidence_score >= 0.00 AND confidence_score <= 1.00', name='ck_confidence_range'),
        CheckConstraint("platform IN ('whatsapp', 'instagram', 'facebook', 'google', 'apple')", name='ck_platform_values'),
        CheckConstraint('response_time_ms >= 0', name='ck_response_time_positive'),
    )
```

#### ✅ **BLOQUE 2: Tabla lead_scores (1.5 horas)**

**Tarea 2.1: Crear migración de lead_scores**

```python
# migrations/versions/004_lead_scores.py
def upgrade() -> None:
    op.create_table(
        'lead_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('phone_e164', sa.String(length=15), nullable=False),

        # Platform scores (0-20 each)
        sa.Column('whatsapp_score', sa.Integer(), nullable=False, default=0),
        sa.Column('instagram_score', sa.Integer(), nullable=False, default=0),
        sa.Column('facebook_score', sa.Integer(), nullable=False, default=0),
        sa.Column('google_score', sa.Integer(), nullable=False, default=0),
        sa.Column('apple_score', sa.Integer(), nullable=False, default=0),

        # Total score and classification
        sa.Column('total_score', sa.Integer(), nullable=False, default=0),
        sa.Column('quality_tier', sa.String(length=20), nullable=False, default='UNKNOWN'),
        sa.Column('confidence_level', sa.Numeric(precision=3, scale=2), nullable=False, default=0.50),

        # Additional factors
        sa.Column('platform_count', sa.Integer(), nullable=False, default=0),
        sa.Column('business_account_count', sa.Integer(), nullable=False, default=0),
        sa.Column('premium_account_count', sa.Integer(), nullable=False, default=0),
        sa.Column('activity_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('geographic_consistency_score', sa.Numeric(precision=3, scale=2), nullable=True),

        # Calculation metadata
        sa.Column('last_calculated_at', sa.DateTime(timezone=True), nullable=False, default=sa.text('NOW()')),
        sa.Column('calculation_version', sa.Integer(), nullable=False, default=1),
        sa.Column('calculation_method', sa.String(length=50), nullable=True, default='standard'),

        # ML predictions (future)
        sa.Column('ml_prediction_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('ml_model_version', sa.String(length=20), nullable=True),

        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=sa.text('NOW()')),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('contact_id', name='uq_lead_score_contact'),

        # Score range constraints
        sa.CheckConstraint('whatsapp_score >= 0 AND whatsapp_score <= 20', name='ck_whatsapp_score_range'),
        sa.CheckConstraint('instagram_score >= 0 AND instagram_score <= 20', name='ck_instagram_score_range'),
        sa.CheckConstraint('facebook_score >= 0 AND facebook_score <= 20', name='ck_facebook_score_range'),
        sa.CheckConstraint('google_score >= 0 AND google_score <= 20', name='ck_google_score_range'),
        sa.CheckConstraint('apple_score >= 0 AND apple_score <= 20', name='ck_apple_score_range'),
        sa.CheckConstraint('total_score >= 0 AND total_score <= 100', name='ck_total_score_range'),
        sa.CheckConstraint("quality_tier IN ('PREMIUM', 'HIGH', 'MEDIUM', 'LOW', 'POOR', 'UNKNOWN')", name='ck_quality_tier_values'),
        sa.CheckConstraint('confidence_level >= 0.00 AND confidence_level <= 1.00', name='ck_confidence_range'),
        sa.CheckConstraint('platform_count >= 0 AND platform_count <= 5', name='ck_platform_count_range'),
    )

    # Performance indexes
    op.create_index('idx_lead_scores_total_score', 'lead_scores', ['total_score'], postgresql_order_by='total_score DESC')
    op.create_index('idx_lead_scores_quality_tier', 'lead_scores', ['quality_tier'])
    op.create_index('idx_lead_scores_platform_count', 'lead_scores', ['platform_count'], postgresql_order_by='platform_count DESC')
    op.create_index('idx_lead_scores_phone', 'lead_scores', ['phone_e164'])
    op.create_index('idx_lead_scores_calculated_at', 'lead_scores', ['last_calculated_at'])
```

#### ✅ **BLOQUE 3: Tabla validation_jobs (1 hora)**

**Tarea 3.1: Sistema de jobs de validación**

```python
# migrations/versions/005_validation_jobs.py
def upgrade() -> None:
    op.create_table(
        'validation_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_uuid', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),

        # Job configuration
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('platforms', postgresql.ARRAY(sa.String()), nullable=False, default={}),

        # Contact selection
        sa.Column('contact_filters', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default={}),
        sa.Column('max_contacts', sa.Integer(), nullable=False, default=1000),
        sa.Column('contact_ids', postgresql.ARRAY(sa.Integer()), nullable=True),

        # Job status
        sa.Column('status', sa.String(length=20), nullable=False, default='QUEUED'),
        sa.Column('progress_percentage', sa.Integer(), nullable=False, default=0),
        sa.Column('current_step', sa.String(length=100), nullable=True),

        # Results tracking
        sa.Column('total_contacts', sa.Integer(), nullable=False, default=0),
        sa.Column('processed_contacts', sa.Integer(), nullable=False, default=0),
        sa.Column('successful_validations', sa.Integer(), nullable=False, default=0),
        sa.Column('failed_validations', sa.Integer(), nullable=False, default=0),
        sa.Column('skipped_validations', sa.Integer(), nullable=False, default=0),

        # Processing configuration
        sa.Column('batch_size', sa.Integer(), nullable=False, default=25),
        sa.Column('max_concurrent', sa.Integer(), nullable=False, default=5),
        sa.Column('retry_attempts', sa.Integer(), nullable=False, default=3),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=False, default=100),

        # Timing and estimation
        sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),

        # User and source tracking
        sa.Column('created_by', sa.String(length=100), nullable=False, default='system'),
        sa.Column('created_via', sa.String(length=50), nullable=False, default='web'),
        sa.Column('priority', sa.Integer(), nullable=False, default=5),

        # Results and errors
        sa.Column('results_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default={}),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('warnings', postgresql.ARRAY(sa.Text()), nullable=True, default={}),

        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=sa.text('NOW()')),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_uuid', name='uq_validation_job_uuid'),
        sa.CheckConstraint("status IN ('QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'PAUSED')", name='ck_job_status_values'),
        sa.CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100', name='ck_progress_range'),
        sa.CheckConstraint('batch_size > 0 AND batch_size <= 1000', name='ck_batch_size_range'),
        sa.CheckConstraint('max_concurrent > 0 AND max_concurrent <= 50', name='ck_concurrent_range'),
        sa.CheckConstraint('priority >= 1 AND priority <= 10', name='ck_priority_range'),
    )

    # Indexes for performance and monitoring
    op.create_index('idx_validation_jobs_status', 'validation_jobs', ['status'])
    op.create_index('idx_validation_jobs_created_at', 'validation_jobs', ['created_at'], postgresql_order_by='created_at DESC')
    op.create_index('idx_validation_jobs_uuid', 'validation_jobs', ['job_uuid'])
    op.create_index('idx_validation_jobs_created_by', 'validation_jobs', ['created_by'])
    op.create_index('idx_validation_jobs_priority', 'validation_jobs', ['priority', 'created_at'])
    op.create_index('idx_validation_jobs_active', 'validation_jobs', ['status', 'started_at'], postgresql_where=sa.text("status IN ('QUEUED', 'RUNNING')"))
```

### 🌆 **TARDE (4 horas): Modelos y Relaciones**

#### ✅ **BLOQUE 4: Modelos SQLAlchemy (2 horas)**

**Tarea 4.1: Actualizar modelo Contact**

```python
# app/models/contact.py - MODIFICAR
class Contact(BaseModel):
    # ... campos existentes ...

    # NEW: Platform validation flags
    whatsapp_validated = Column(Boolean, nullable=True, default=None, index=True)
    instagram_validated = Column(Boolean, nullable=True, default=None, index=True)
    facebook_validated = Column(Boolean, nullable=True, default=None, index=True)
    google_validated = Column(Boolean, nullable=True, default=None, index=True)
    apple_validated = Column(Boolean, nullable=True, default=None, index=True)

    # NEW: Validation metadata
    last_platform_validation = Column(DateTime(timezone=True), nullable=True)
    platform_validation_count = Column(Integer, nullable=False, default=0)

    # NEW: Lead scoring
    lead_score = Column(Integer, nullable=True, index=True)
    lead_tier = Column(String(20), nullable=False, default='UNKNOWN', index=True)
    last_scored_at = Column(DateTime(timezone=True), nullable=True)

    # NEW: Relationships
    platform_validations = relationship("PlatformValidation", back_populates="contact", cascade="all, delete-orphan")
    lead_score_record = relationship("LeadScore", back_populates="contact", uselist=False, cascade="all, delete-orphan")

    # NEW: Computed properties
    @property
    def validated_platforms(self) -> List[str]:
        """Get list of platforms where contact is validated"""
        platforms = []
        if self.whatsapp_validated: platforms.append('whatsapp')
        if self.instagram_validated: platforms.append('instagram')
        if self.facebook_validated: platforms.append('facebook')
        if self.google_validated: platforms.append('google')
        if self.apple_validated: platforms.append('apple')
        return platforms

    @property
    def validation_completeness(self) -> float:
        """Get percentage of platforms validated (0.0-1.0)"""
        total_platforms = 5
        validated_count = len(self.validated_platforms)
        return validated_count / total_platforms

    @property
    def is_high_value_lead(self) -> bool:
        """Check if contact is high-value lead based on score"""
        return self.lead_score is not None and self.lead_score >= 70
```

**Tarea 4.2: Crear modelo LeadScore**

```python
# app/models/lead_score.py - NUEVO ARCHIVO
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import BaseModel

class LeadScore(BaseModel):
    """Lead scoring records for contacts"""
    __tablename__ = "lead_scores"

    # Relationship
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    contact = relationship("Contact", back_populates="lead_score_record")

    # Basic info
    phone_e164 = Column(String(15), nullable=False, index=True)

    # Platform scores (0-20 each)
    whatsapp_score = Column(Integer, nullable=False, default=0)
    instagram_score = Column(Integer, nullable=False, default=0)
    facebook_score = Column(Integer, nullable=False, default=0)
    google_score = Column(Integer, nullable=False, default=0)
    apple_score = Column(Integer, nullable=False, default=0)

    # Total score and tier
    total_score = Column(Integer, nullable=False, default=0, index=True)
    quality_tier = Column(String(20), nullable=False, default='UNKNOWN', index=True)
    confidence_level = Column(Numeric(3, 2), nullable=False, default=0.50)

    # Platform summary
    platform_count = Column(Integer, nullable=False, default=0, index=True)
    business_account_count = Column(Integer, nullable=False, default=0)
    premium_account_count = Column(Integer, nullable=False, default=0)

    # Additional scoring factors
    activity_score = Column(Numeric(3, 2), nullable=True)
    geographic_consistency_score = Column(Numeric(3, 2), nullable=True)
    temporal_consistency_score = Column(Numeric(3, 2), nullable=True)

    # Calculation metadata
    last_calculated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    calculation_version = Column(Integer, nullable=False, default=1)
    calculation_method = Column(String(50), nullable=True, default='standard')

    # ML predictions (prepared for future)
    ml_prediction_score = Column(Numeric(3, 2), nullable=True)
    ml_model_version = Column(String(20), nullable=True)
    ml_confidence = Column(Numeric(3, 2), nullable=True)

    # Score breakdown for transparency
    score_breakdown = Column(JSONB, nullable=True, default={})

    # Constraints
    __table_args__ = (
        CheckConstraint('whatsapp_score >= 0 AND whatsapp_score <= 20', name='ck_whatsapp_score_range'),
        CheckConstraint('instagram_score >= 0 AND instagram_score <= 20', name='ck_instagram_score_range'),
        CheckConstraint('facebook_score >= 0 AND facebook_score <= 20', name='ck_facebook_score_range'),
        CheckConstraint('google_score >= 0 AND google_score <= 20', name='ck_google_score_range'),
        CheckConstraint('apple_score >= 0 AND apple_score <= 20', name='ck_apple_score_range'),
        CheckConstraint('total_score >= 0 AND total_score <= 100', name='ck_total_score_range'),
        CheckConstraint("quality_tier IN ('PREMIUM', 'HIGH', 'MEDIUM', 'LOW', 'POOR', 'UNKNOWN')", name='ck_quality_tier_values'),
        CheckConstraint('platform_count >= 0 AND platform_count <= 5', name='ck_platform_count_range'),
        CheckConstraint('confidence_level >= 0.00 AND confidence_level <= 1.00', name='ck_confidence_range'),
    )

    # Methods for scoring logic
    def calculate_total_score(self) -> int:
        """Calculate total score from platform scores"""
        return (
            self.whatsapp_score +
            self.instagram_score +
            self.facebook_score +
            self.google_score +
            self.apple_score
        )

    def determine_quality_tier(self) -> str:
        """Determine quality tier based on total score"""
        if self.total_score >= 90:
            return 'PREMIUM'
        elif self.total_score >= 75:
            return 'HIGH'
        elif self.total_score >= 50:
            return 'MEDIUM'
        elif self.total_score >= 25:
            return 'LOW'
        else:
            return 'POOR'

    def update_derived_fields(self):
        """Update total_score, quality_tier, and platform_count"""
        self.total_score = self.calculate_total_score()
        self.quality_tier = self.determine_quality_tier()
        self.platform_count = sum([
            1 for score in [
                self.whatsapp_score, self.instagram_score,
                self.facebook_score, self.google_score, self.apple_score
            ] if score > 0
        ])
```

---

## 📅 DÍA 4: INTEGRACIÓN Y OPTIMIZACIÓN

### 🌅 **MAÑANA (4 horas): Schemas y Endpoints**

#### ✅ **BLOQUE 5: Schemas Pydantic Expandidos (1.5 horas)**

**Tarea 5.1: Schemas para validación**

```python
# app/schemas/platform_validation.py - NUEVO ARCHIVO
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class PlatformType(str, Enum):
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE = "google"
    APPLE = "apple"

class ValidationMethod(str, Enum):
    API = "api"
    SCRAPING = "scraping"
    BULK_CHECK = "bulk_check"
    MANUAL = "manual"

class PlatformValidationCreate(BaseModel):
    contact_id: int
    phone_e164: str = Field(..., regex=r'^\+52\d{10}$')
    platform: PlatformType
    is_valid: bool
    is_business: Optional[bool] = False
    is_premium: Optional[bool] = False
    confidence_score: float = Field(0.50, ge=0.0, le=1.0)
    platform_details: Optional[Dict[str, Any]] = {}
    profile_info: Optional[Dict[str, Any]] = {}
    validation_method: Optional[ValidationMethod] = None
    response_time_ms: Optional[int] = Field(None, ge=0)

class PlatformValidationResponse(BaseModel):
    id: int
    contact_id: int
    phone_e164: str
    platform: PlatformType
    is_valid: bool
    is_business: Optional[bool]
    is_premium: Optional[bool]
    confidence_score: float
    platform_details: Dict[str, Any]
    profile_info: Dict[str, Any]
    validation_method: Optional[str]
    response_time_ms: Optional[int]
    validated_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True
```

**Tarea 5.2: Schemas para lead scoring**

```python
# app/schemas/lead_score.py - NUEVO ARCHIVO
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class QualityTier(str, Enum):
    PREMIUM = "PREMIUM"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    POOR = "POOR"
    UNKNOWN = "UNKNOWN"

class LeadScoreCreate(BaseModel):
    contact_id: int
    phone_e164: str = Field(..., regex=r'^\+52\d{10}$')
    whatsapp_score: int = Field(0, ge=0, le=20)
    instagram_score: int = Field(0, ge=0, le=20)
    facebook_score: int = Field(0, ge=0, le=20)
    google_score: int = Field(0, ge=0, le=20)
    apple_score: int = Field(0, ge=0, le=20)
    calculation_method: Optional[str] = "standard"

class LeadScoreResponse(BaseModel):
    id: int
    contact_id: int
    phone_e164: str
    whatsapp_score: int
    instagram_score: int
    facebook_score: int
    google_score: int
    apple_score: int
    total_score: int
    quality_tier: QualityTier
    confidence_level: float
    platform_count: int
    business_account_count: int
    premium_account_count: int
    last_calculated_at: datetime
    score_breakdown: Dict[str, Any]

    class Config:
        from_attributes = True

class ContactWithScore(BaseModel):
    """Enhanced contact response with lead score"""
    # Basic contact fields
    id: int
    phone_e164: str
    phone_national: str
    full_name: Optional[str]
    state_name: Optional[str]
    municipality: Optional[str]
    lada: Optional[str]
    created_at: datetime

    # Platform validation status
    whatsapp_validated: Optional[bool]
    instagram_validated: Optional[bool]
    facebook_validated: Optional[bool]
    google_validated: Optional[bool]
    apple_validated: Optional[bool]

    # Lead scoring
    lead_score: Optional[int]
    lead_tier: Optional[QualityTier]
    last_scored_at: Optional[datetime]

    # Computed fields
    validated_platforms: List[str] = []
    validation_completeness: float = 0.0
    is_high_value_lead: bool = False

    class Config:
        from_attributes = True
```

#### ✅ **BLOQUE 6: Endpoints de Validación (1.5 horas)**

**Tarea 6.1: CRUD para platform_validations**

```python
# app/api/v1/endpoints/validations.py - NUEVO ARCHIVO
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.platform_validation import PlatformValidation
from app.schemas.platform_validation import PlatformValidationCreate, PlatformValidationResponse

router = APIRouter()

@router.post("/", response_model=PlatformValidationResponse)
async def create_platform_validation(
    validation: PlatformValidationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Create or update platform validation"""

    # Check if validation already exists
    existing_query = select(PlatformValidation).where(
        and_(
            PlatformValidation.phone_e164 == validation.phone_e164,
            PlatformValidation.platform == validation.platform
        )
    )
    existing_result = await db.execute(existing_query)
    existing_validation = existing_result.scalar_one_or_none()

    if existing_validation:
        # Update existing validation
        for field, value in validation.dict(exclude_unset=True).items():
            setattr(existing_validation, field, value)
        existing_validation.updated_at = func.now()
        db_validation = existing_validation
    else:
        # Create new validation
        db_validation = PlatformValidation(**validation.dict())
        db.add(db_validation)

    await db.commit()
    await db.refresh(db_validation)

    return db_validation

@router.get("/contact/{contact_id}", response_model=List[PlatformValidationResponse])
async def get_contact_validations(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get all platform validations for a contact"""

    query = select(PlatformValidation).where(
        PlatformValidation.contact_id == contact_id
    ).order_by(PlatformValidation.platform)

    result = await db.execute(query)
    validations = result.scalars().all()

    return validations

@router.get("/platform/{platform}", response_model=List[PlatformValidationResponse])
async def get_platform_validations(
    platform: str,
    limit: int = Query(100, le=1000),
    only_valid: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get validations for specific platform"""

    query = select(PlatformValidation).where(
        PlatformValidation.platform == platform
    )

    if only_valid:
        query = query.where(PlatformValidation.is_valid == True)

    query = query.limit(limit).order_by(PlatformValidation.validated_at.desc())

    result = await db.execute(query)
    validations = result.scalars().all()

    return validations
```

#### ✅ **BLOQUE 7: Servicios de Scoring (1 hora)**

**Tarea 7.1: Servicio base de scoring**

```python
# app/services/lead_scoring_service.py - NUEVO ARCHIVO
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.contact import Contact
from app.models.platform_validation import PlatformValidation
from app.models.lead_score import LeadScore

class LeadScoringService:
    """Service for calculating and managing lead scores"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.platform_weights = {
            'whatsapp': 25,    # Más peso por popularidad en México
            'instagram': 20,   # Alto engagement
            'facebook': 20,    # Amplia base de usuarios
            'google': 20,      # Servicios esenciales
            'apple': 15        # Menor penetración en México
        }

    async def calculate_contact_score(self, contact_id: int) -> Optional[LeadScore]:
        """Calculate comprehensive lead score for contact"""

        # Get contact
        contact_query = select(Contact).where(Contact.id == contact_id)
        contact_result = await self.db.execute(contact_query)
        contact = contact_result.scalar_one_or_none()

        if not contact:
            return None

        # Get platform validations
        validations_query = select(PlatformValidation).where(
            PlatformValidation.contact_id == contact_id
        )
        validations_result = await self.db.execute(validations_query)
        validations = validations_result.scalars().all()

        # Calculate platform scores
        platform_scores = {
            'whatsapp': 0,
            'instagram': 0,
            'facebook': 0,
            'google': 0,
            'apple': 0
        }

        business_count = 0
        premium_count = 0

        for validation in validations:
            if validation.is_valid:
                base_score = 15  # Base score for valid platform

                # Bonus for business account
                if validation.is_business:
                    base_score += 3
                    business_count += 1

                # Bonus for premium account
                if validation.is_premium:
                    base_score += 2
                    premium_count += 1

                # Confidence multiplier
                confidence_multiplier = validation.confidence_score
                final_score = int(base_score * confidence_multiplier)

                platform_scores[validation.platform] = min(20, final_score)

        # Calculate total score
        total_score = sum(platform_scores.values())

        # Platform count
        platform_count = sum(1 for score in platform_scores.values() if score > 0)

        # Combination bonuses
        combination_bonus = self._calculate_combination_bonus(platform_scores)
        total_score = min(100, total_score + combination_bonus)

        # Create or update lead score record
        existing_score_query = select(LeadScore).where(LeadScore.contact_id == contact_id)
        existing_score_result = await self.db.execute(existing_score_query)
        existing_score = existing_score_result.scalar_one_or_none()

        score_data = {
            'contact_id': contact_id,
            'phone_e164': contact.phone_e164,
            'whatsapp_score': platform_scores['whatsapp'],
            'instagram_score': platform_scores['instagram'],
            'facebook_score': platform_scores['facebook'],
            'google_score': platform_scores['google'],
            'apple_score': platform_scores['apple'],
            'total_score': total_score,
            'platform_count': platform_count,
            'business_account_count': business_count,
            'premium_account_count': premium_count,
            'score_breakdown': {
                'platform_scores': platform_scores,
                'combination_bonus': combination_bonus,
                'confidence_scores': {v.platform: v.confidence_score for v in validations}
            }
        }

        if existing_score:
            # Update existing
            for field, value in score_data.items():
                setattr(existing_score, field, value)
            existing_score.last_calculated_at = func.now()
            existing_score.calculation_version += 1
            lead_score = existing_score
        else:
            # Create new
            lead_score = LeadScore(**score_data)
            self.db.add(lead_score)

        # Update derived fields
        lead_score.update_derived_fields()

        # Update contact summary fields
        contact.lead_score = total_score
        contact.lead_tier = lead_score.quality_tier
        contact.last_scored_at = func.now()

        await self.db.commit()
        await self.db.refresh(lead_score)

        return lead_score

    def _calculate_combination_bonus(self, platform_scores: Dict[str, int]) -> int:
        """Calculate bonus points for platform combinations"""
        active_platforms = [p for p, score in platform_scores.items() if score > 0]

        bonus = 0

        # Bonus for multiple platforms
        if len(active_platforms) >= 4:
            bonus += 10
        elif len(active_platforms) >= 3:
            bonus += 5
        elif len(active_platforms) >= 2:
            bonus += 2

        # Specific combination bonuses
        if 'whatsapp' in active_platforms and 'facebook' in active_platforms:
            bonus += 3  # Meta ecosystem

        if 'instagram' in active_platforms and 'facebook' in active_platforms:
            bonus += 3  # Meta ecosystem

        if 'google' in active_platforms and 'apple' in active_platforms:
            bonus += 2  # Tech-savvy user

        return min(15, bonus)  # Cap bonus at 15 points
```

#### ✅ **BLOQUE 8: Endpoints de Lead Scoring (1.5 horas)**

**Tarea 8.1: API para lead scoring**

```python
# app/api/v1/endpoints/lead_scoring.py - NUEVO ARCHIVO
from fastapi import APIRouter, Depends, BackgroundTasks
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.lead_scoring_service import LeadScoringService
from app.schemas.lead_score import LeadScoreResponse, ContactWithScore

router = APIRouter()

@router.post("/calculate/{contact_id}", response_model=LeadScoreResponse)
async def calculate_lead_score(
    contact_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Calculate lead score for specific contact"""

    scoring_service = LeadScoringService(db)
    lead_score = await scoring_service.calculate_contact_score(contact_id)

    if not lead_score:
        raise HTTPException(404, detail="Contact not found")

    return lead_score

@router.post("/batch-calculate", response_model=Dict[str, str])
async def batch_calculate_scores(
    contact_ids: List[int],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Calculate scores for multiple contacts in background"""

    if len(contact_ids) > 1000:
        raise HTTPException(400, detail="Maximum 1000 contacts per batch")

    # Process in background
    background_tasks.add_task(
        process_batch_scoring,
        contact_ids,
        current_user
    )

    return {
        "message": f"Batch scoring started for {len(contact_ids)} contacts",
        "status": "processing"
    }

@router.get("/top-leads", response_model=List[ContactWithScore])
async def get_top_leads(
    limit: int = Query(50, le=500),
    min_score: int = Query(70, ge=0, le=100),
    tier: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get top-scoring leads"""

    query = select(Contact).join(LeadScore).where(
        LeadScore.total_score >= min_score
    )

    if tier:
        query = query.where(LeadScore.quality_tier == tier)

    query = query.order_by(LeadScore.total_score.desc()).limit(limit)

    result = await db.execute(query)
    contacts = result.scalars().all()

    return [ContactWithScore.from_orm(contact) for contact in contacts]
```

### 🌆 **TARDE (4 horas): Testing y Optimización**

#### ✅ **BLOQUE 9: Testing de Base de Datos (2 horas)**

**Tarea 9.1: Tests de migración**

```python
# tests/database/test_migrations.py - NUEVO
import pytest
from sqlalchemy import text
from app.core.database import get_db

@pytest.mark.asyncio
async def test_platform_validations_table_exists():
    """Test that platform_validations table was created correctly"""
    async for db in get_db():
        result = await db.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'platform_validations'
            ORDER BY ordinal_position
        """))
        columns = result.fetchall()

        expected_columns = [
            'id', 'contact_id', 'phone_e164', 'platform',
            'is_valid', 'is_business', 'confidence_score'
        ]

        actual_columns = [col.column_name for col in columns]
        for expected in expected_columns:
            assert expected in actual_columns

@pytest.mark.asyncio
async def test_lead_scores_constraints():
    """Test that lead_scores constraints work correctly"""
    async for db in get_db():
        # Test score range constraints
        with pytest.raises(Exception):
            await db.execute(text("""
                INSERT INTO lead_scores (contact_id, phone_e164, whatsapp_score)
                VALUES (1, '+5216671234567', 25)  -- Should fail: score > 20
            """))

        # Test quality tier constraint
        with pytest.raises(Exception):
            await db.execute(text("""
                INSERT INTO lead_scores (contact_id, phone_e164, quality_tier)
                VALUES (1, '+5216671234567', 'INVALID')  -- Should fail: invalid tier
            """))
```

**Tarea 9.2: Performance testing con datos reales**

```python
# tests/performance/test_database_performance.py - NUEVO
import pytest
import time
from sqlalchemy import text

@pytest.mark.asyncio
async def test_contacts_pagination_performance():
    """Test that pagination performs well with 31.8M records"""
    async for db in get_db():
        start_time = time.time()

        result = await db.execute(text("""
            SELECT * FROM contacts
            WHERE opt_out_at IS NULL
            ORDER BY created_at DESC
            LIMIT 50 OFFSET 1000
        """))

        execution_time = time.time() - start_time

        # Should complete in less than 2 seconds
        assert execution_time < 2.0
        assert len(result.fetchall()) <= 50

@pytest.mark.asyncio
async def test_stats_query_performance():
    """Test that stats queries are fast enough for dashboard"""
    async for db in get_db():
        start_time = time.time()

        result = await db.execute(text("""
            SELECT
                state_name,
                COUNT(*) as count
            FROM contacts
            WHERE state_name IS NOT NULL
            GROUP BY state_name
            ORDER BY count DESC
            LIMIT 15
        """))

        execution_time = time.time() - start_time

        # Stats should load in less than 1 second
        assert execution_time < 1.0
```

#### ✅ **BLOQUE 10: Optimización Final (2 horas)**

**Tarea 10.1: Optimización de índices**

```sql
-- scripts/optimize_indexes.sql
-- Analizar y optimizar índices existentes

-- Verificar uso de índices
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Identificar índices no utilizados
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND indexname NOT LIKE '%pkey%';

-- Crear índices compuestos específicos para dashboard
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_dashboard_combo
ON contacts(state_name, municipality, lada, is_mobile, opt_out_at)
WHERE opt_out_at IS NULL;
```

**Tarea 10.2: Configuración de PostgreSQL**

```sql
-- scripts/postgresql_optimization.sql
-- Optimizaciones específicas para el volumen de datos

-- Aumentar shared_buffers para mejor caching
-- ALTER SYSTEM SET shared_buffers = '2GB';

-- Optimizar work_mem para queries complejas
-- ALTER SYSTEM SET work_mem = '64MB';

-- Configurar effective_cache_size
-- ALTER SYSTEM SET effective_cache_size = '6GB';

-- Optimizar checkpoint settings
-- ALTER SYSTEM SET checkpoint_completion_target = 0.9;
-- ALTER SYSTEM SET wal_buffers = '64MB';

-- Reload configuration
-- SELECT pg_reload_conf();
```

---

## 🎯 CRITERIOS DE ACEPTACIÓN

### **✅ Al Final del Día 3:**

- [ ] Nuevas tablas creadas sin afectar datos existentes
- [ ] Migraciones ejecutadas exitosamente
- [ ] Modelos SQLAlchemy actualizados
- [ ] Relaciones entre tablas funcionando
- [ ] Constraints y validaciones operativas

### **✅ Al Final del Día 4:**

- [ ] Schemas Pydantic para nuevas entidades
- [ ] Endpoints de validación funcionando
- [ ] Servicio de lead scoring implementado
- [ ] Testing de performance pasando
- [ ] Base de datos optimizada para dashboard

---

## 🚨 TROUBLESHOOTING

### **Problema: Migración falla con datos existentes**

- **Solución:** Usar `IF NOT EXISTS` y `ADD COLUMN IF NOT EXISTS`
- **Backup:** Crear backup antes de migración
- **Rollback:** Script de rollback preparado

### **Problema: Performance degradada después de migración**

- **Solución:** Ejecutar `ANALYZE` después de crear índices
- **Optimizar:** Usar `CREATE INDEX CONCURRENTLY`
- **Monitor:** `pg_stat_activity` para queries lentas

### **Problema: Constraints fallan con datos existentes**

- **Solución:** Validar datos antes de agregar constraints
- **Limpiar:** Datos inconsistentes antes de migración
- **Gradual:** Agregar constraints en pasos separados

---

## 📊 MÉTRICAS DE PROGRESO

- **Nuevas Tablas:** 40% del total
- **Migraciones:** 25% del total
- **Modelos y Schemas:** 20% del total
- **Testing y Optimización:** 15% del total

**Total Fase 2:** 100% → **Preparado para Fase 3**

---

## 🚀 RESULTADO ESPERADO

### **Al Completar Fase 2:**

- ✅ **Base de datos expandida** con capacidades multi-plataforma
- ✅ **Estructura de scoring** lista para algoritmos
- ✅ **Performance mantenida** con 31.8M contactos
- ✅ **Compatibilidad total** con sistema existente
- ✅ **API endpoints** para nuevas funcionalidades

### **🎉 Preparado Para:**

- **Validadores multi-plataforma** con almacenamiento
- **Lead scoring** con datos estructurados
- **Dashboard expandido** con nuevas métricas
- **Sistema híbrido** actual + nuevas capacidades

**→ Continuar con [Fase 3: Validadores Core](./fase3-validadores-core.md)**

---

_Fase 2: Expansión de Base de Datos_
_SMS Marketing Platform v2.0 - Migración Sistema Actual_
_Implementación Detallada_
