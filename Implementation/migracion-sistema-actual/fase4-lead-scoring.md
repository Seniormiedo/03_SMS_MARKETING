# 🧠 FASE 4: LEAD SCORING INTELIGENTE (Días 8-9)

## SMS Marketing Platform v2.0 - Migración Sistema Actual

---

## 🎯 OBJETIVO DE LA FASE

Implementar un sistema de lead scoring inteligente que calcule puntuaciones de 0-100 basadas en validaciones multi-plataforma, enriqueciendo los 31.8M contactos existentes con datos de calidad.

**Duración:** 2 días
**Complejidad:** ALTA
**Riesgo:** BAJO - No afecta funcionalidad existente
**Prioridad:** ALTA

---

## 🧮 ALGORITMO DE SCORING DETALLADO

### **📊 Distribución de Puntuación (0-100 puntos):**

#### **🏆 Puntuación por Plataforma (80 puntos máximo):**

```python
PLATFORM_WEIGHTS = {
    'whatsapp': 25,    # 25% - Más popular en México
    'instagram': 20,   # 20% - Alto engagement jóvenes
    'facebook': 20,    # 20% - Base amplia usuarios
    'google': 20,      # 20% - Servicios esenciales
    'apple': 15        # 15% - Menor penetración México
}

# Puntuación base por plataforma válida:
# - Cuenta válida: 15 puntos base
# - Cuenta de negocio: +3 puntos bonus
# - Cuenta premium/verificada: +2 puntos bonus
# - Multiplicador de confianza: confidence_score (0.0-1.0)
```

#### **🎁 Bonificaciones por Combinación (20 puntos máximo):**

```python
COMBINATION_BONUSES = {
    'multiple_platforms': {
        5: 10,  # 5 plataformas = +10 puntos
        4: 7,   # 4 plataformas = +7 puntos
        3: 5,   # 3 plataformas = +5 puntos
        2: 2    # 2 plataformas = +2 puntos
    },
    'ecosystem_synergy': {
        ('whatsapp', 'facebook'): 3,      # Meta ecosystem
        ('instagram', 'facebook'): 3,     # Meta ecosystem
        ('whatsapp', 'instagram'): 2,     # Jóvenes activos
        ('google', 'apple'): 2,           # Tech-savvy
    },
    'business_premium': {
        'all_business': 5,    # Todas las cuentas son de negocio
        'mixed_business': 3,  # Mezcla de personal/negocio
        'all_premium': 5,     # Todas las cuentas premium
    }
}
```

#### **🎯 Clasificación por Tiers:**

```python
QUALITY_TIERS = {
    'PREMIUM': (90, 100),  # 90-100 puntos
    'HIGH': (75, 89),      # 75-89 puntos
    'MEDIUM': (50, 74),    # 50-74 puntos
    'LOW': (25, 49),       # 25-49 puntos
    'POOR': (1, 24),       # 1-24 puntos
    'UNKNOWN': (0, 0)      # Sin validaciones
}
```

---

## 📅 DÍA 8: MOTOR DE SCORING

### 🌅 **MAÑANA (4 horas): Algoritmo Core**

#### ✅ **BLOQUE 1: Servicio de Scoring Avanzado (2 horas)**

**Tarea 1.1: Implementar algoritmo completo**

```python
# app/services/advanced_lead_scoring.py - NUEVO ARCHIVO
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.contact import Contact
from app.models.platform_validation import PlatformValidation
from app.models.lead_score import LeadScore

class AdvancedLeadScoringService:
    """Advanced lead scoring with ML-ready features"""

    def __init__(self, db: AsyncSession):
        self.db = db

        # Scoring configuration
        self.platform_weights = {
            'whatsapp': 25,    # Más peso por popularidad en México
            'instagram': 20,   # Alto engagement
            'facebook': 20,    # Amplia base de usuarios
            'google': 20,      # Servicios esenciales
            'apple': 15        # Menor penetración en México
        }

        self.quality_factors = {
            'account_age_bonus': 0.1,        # Bonus por antigüedad
            'activity_level_bonus': 0.15,    # Bonus por actividad
            'profile_completeness': 0.1,     # Perfil completo
            'verification_status': 0.15,     # Cuenta verificada
            'social_connections': 0.05,      # Número de conexiones
            'engagement_rate': 0.1,          # Tasa de engagement
            'geographic_consistency': 0.1,   # Consistencia geográfica
            'temporal_patterns': 0.05        # Patrones temporales
        }

    async def calculate_comprehensive_score(self, contact_id: int) -> Optional[LeadScore]:
        """Calculate comprehensive lead score with all factors"""

        # Get contact and validations
        contact = await self._get_contact_with_validations(contact_id)
        if not contact:
            return None

        # Calculate base platform scores
        platform_scores = await self._calculate_platform_scores(contact.platform_validations)

        # Calculate quality factors
        quality_multipliers = await self._calculate_quality_factors(contact)

        # Apply quality multipliers to platform scores
        adjusted_scores = self._apply_quality_multipliers(platform_scores, quality_multipliers)

        # Calculate combination bonuses
        combination_bonus = self._calculate_combination_bonuses(adjusted_scores, contact.platform_validations)

        # Calculate final score
        base_score = sum(adjusted_scores.values())
        total_score = min(100, base_score + combination_bonus)

        # Determine quality tier
        quality_tier = self._determine_quality_tier(total_score)

        # Calculate confidence level
        confidence_level = self._calculate_confidence_level(contact.platform_validations, quality_multipliers)

        # Count metrics
        platform_count = sum(1 for score in adjusted_scores.values() if score > 0)
        business_count = sum(1 for v in contact.platform_validations if v.is_business)
        premium_count = sum(1 for v in contact.platform_validations if v.is_premium)

        # Create detailed score breakdown
        score_breakdown = {
            'platform_scores': adjusted_scores,
            'quality_multipliers': quality_multipliers,
            'combination_bonus': combination_bonus,
            'base_score': base_score,
            'final_score': total_score,
            'calculation_timestamp': datetime.utcnow().isoformat(),
            'factors_analyzed': len(quality_multipliers),
            'confidence_sources': [v.validation_method for v in contact.platform_validations]
        }

        # Create or update lead score
        lead_score_data = {
            'contact_id': contact_id,
            'phone_e164': contact.phone_e164,
            'whatsapp_score': adjusted_scores.get('whatsapp', 0),
            'instagram_score': adjusted_scores.get('instagram', 0),
            'facebook_score': adjusted_scores.get('facebook', 0),
            'google_score': adjusted_scores.get('google', 0),
            'apple_score': adjusted_scores.get('apple', 0),
            'total_score': total_score,
            'quality_tier': quality_tier,
            'confidence_level': confidence_level,
            'platform_count': platform_count,
            'business_account_count': business_count,
            'premium_account_count': premium_count,
            'score_breakdown': score_breakdown,
            'calculation_method': 'advanced_v1',
            'calculation_version': 1
        }

        return await self._save_lead_score(lead_score_data)

    async def _calculate_platform_scores(self, validations: List[PlatformValidation]) -> Dict[str, int]:
        """Calculate base scores for each platform"""
        scores = {platform: 0 for platform in self.platform_weights.keys()}

        for validation in validations:
            if not validation.is_valid:
                continue

            # Base score for valid platform
            base_score = 15

            # Business account bonus
            if validation.is_business:
                base_score += 3

            # Premium account bonus
            if validation.is_premium:
                base_score += 2

            # Apply confidence multiplier
            confidence_adjusted = base_score * validation.confidence_score

            # Cap at platform maximum
            platform_max = 20
            final_score = min(platform_max, int(confidence_adjusted))

            scores[validation.platform] = final_score

        return scores

    async def _calculate_quality_factors(self, contact: Contact) -> Dict[str, float]:
        """Calculate quality factors for scoring enhancement"""
        factors = {}

        # Geographic consistency
        if contact.state_name and contact.municipality and contact.lada:
            # Check if LADA matches state (geographic consistency)
            consistency_score = await self._check_geographic_consistency(
                contact.lada, contact.state_name
            )
            factors['geographic_consistency'] = consistency_score

        # Account age estimation (based on creation date as proxy)
        if contact.created_at:
            days_since_creation = (datetime.utcnow() - contact.created_at).days
            age_factor = min(1.0, days_since_creation / 365)  # Max factor at 1 year
            factors['account_age_estimation'] = age_factor

        # Profile completeness
        completeness_score = self._calculate_profile_completeness(contact)
        factors['profile_completeness'] = completeness_score

        # Validation recency
        if contact.last_platform_validation:
            days_since_validation = (datetime.utcnow() - contact.last_platform_validation).days
            recency_factor = max(0.5, 1.0 - (days_since_validation / 30))  # Decay over 30 days
            factors['validation_recency'] = recency_factor

        return factors

    def _calculate_profile_completeness(self, contact: Contact) -> float:
        """Calculate profile completeness score"""
        fields_to_check = [
            contact.full_name,
            contact.address,
            contact.state_name,
            contact.municipality,
            contact.lada,
            contact.operator
        ]

        filled_fields = sum(1 for field in fields_to_check if field is not None and field.strip())
        total_fields = len(fields_to_check)

        return filled_fields / total_fields

    async def _check_geographic_consistency(self, lada: str, state_name: str) -> float:
        """Check if LADA code matches the state (geographic consistency)"""

        # Query ladas_reference table for consistency check
        query = select(func.count()).select_from(
            # Assuming ladas_reference table exists with lada -> state mapping
            text("""
                SELECT 1 FROM ladas_reference
                WHERE lada = :lada
                AND UPPER(state_name) = UPPER(:state_name)
            """)
        )

        result = await self.db.execute(query, {"lada": lada, "state_name": state_name})
        is_consistent = result.scalar() > 0

        return 1.0 if is_consistent else 0.3  # Penalty for inconsistency

    def _calculate_combination_bonuses(self, platform_scores: Dict[str, int], validations: List[PlatformValidation]) -> int:
        """Calculate bonuses for platform combinations"""
        active_platforms = [p for p, score in platform_scores.items() if score > 0]
        bonus = 0

        # Multi-platform bonus
        platform_count = len(active_platforms)
        if platform_count >= 5:
            bonus += 10
        elif platform_count >= 4:
            bonus += 7
        elif platform_count >= 3:
            bonus += 5
        elif platform_count >= 2:
            bonus += 2

        # Ecosystem synergy bonuses
        if 'whatsapp' in active_platforms and 'facebook' in active_platforms:
            bonus += 3  # Meta ecosystem

        if 'instagram' in active_platforms and 'facebook' in active_platforms:
            bonus += 3  # Meta ecosystem

        if 'whatsapp' in active_platforms and 'instagram' in active_platforms:
            bonus += 2  # Social media active user

        if 'google' in active_platforms and 'apple' in active_platforms:
            bonus += 2  # Tech ecosystem user

        # Business account bonuses
        business_accounts = [v for v in validations if v.is_business]
        if len(business_accounts) >= 3:
            bonus += 5  # Multiple business accounts
        elif len(business_accounts) >= 2:
            bonus += 3

        # Premium account bonuses
        premium_accounts = [v for v in validations if v.is_premium]
        if len(premium_accounts) >= 2:
            bonus += 3

        return min(20, bonus)  # Cap at 20 points

    def _determine_quality_tier(self, total_score: int) -> str:
        """Determine quality tier based on total score"""
        if total_score >= 90:
            return 'PREMIUM'
        elif total_score >= 75:
            return 'HIGH'
        elif total_score >= 50:
            return 'MEDIUM'
        elif total_score >= 25:
            return 'LOW'
        elif total_score > 0:
            return 'POOR'
        else:
            return 'UNKNOWN'

    def _calculate_confidence_level(self, validations: List[PlatformValidation], quality_factors: Dict[str, float]) -> float:
        """Calculate overall confidence in the score"""
        if not validations:
            return 0.0

        # Average confidence from validations
        validation_confidence = sum(v.confidence_score for v in validations) / len(validations)

        # Factor in quality factors
        quality_confidence = sum(quality_factors.values()) / len(quality_factors) if quality_factors else 0.5

        # Bonus for multiple validations
        validation_count_bonus = min(0.2, len(validations) * 0.05)

        # Combined confidence
        total_confidence = (validation_confidence * 0.6) + (quality_confidence * 0.3) + validation_count_bonus

        return min(1.0, total_confidence)
```

#### ✅ **BLOQUE 2: Machine Learning Pipeline Base (2 horas)**

**Tarea 2.1: Preparar datos para ML**

```python
# app/services/ml_scoring_service.py - NUEVO ARCHIVO
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import json

class MLLeadScoringService:
    """Machine Learning service for lead scoring prediction"""

    def __init__(self):
        self.model: Optional[RandomForestRegressor] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: List[str] = []
        self.model_version: str = "1.0.0"
        self.model_path = "/app/models/lead_scoring_model.pkl"
        self.scaler_path = "/app/models/lead_scoring_scaler.pkl"

        # Define features for ML model
        self.feature_definitions = {
            # Platform presence (binary features)
            'has_whatsapp': 'bool',
            'has_instagram': 'bool',
            'has_facebook': 'bool',
            'has_google': 'bool',
            'has_apple': 'bool',

            # Platform scores (numeric features)
            'whatsapp_score': 'int',
            'instagram_score': 'int',
            'facebook_score': 'int',
            'google_score': 'int',
            'apple_score': 'int',

            # Aggregate features
            'platform_count': 'int',
            'business_account_count': 'int',
            'premium_account_count': 'int',
            'avg_confidence_score': 'float',

            # Contact features
            'profile_completeness': 'float',
            'geographic_consistency': 'float',
            'account_age_days': 'int',
            'validation_recency_days': 'int',

            # Derived features
            'has_business_accounts': 'bool',
            'has_premium_accounts': 'bool',
            'is_multi_platform': 'bool',
            'meta_ecosystem_user': 'bool',  # WhatsApp + Facebook/Instagram
            'tech_ecosystem_user': 'bool',  # Google + Apple
        }

    async def prepare_training_data(self, db: AsyncSession) -> pd.DataFrame:
        """Prepare training data from existing contacts and validations"""

        # Query contacts with validations and scores
        query = """
        SELECT
            c.id as contact_id,
            c.phone_e164,
            c.full_name,
            c.state_name,
            c.municipality,
            c.lada,
            c.created_at,
            c.last_platform_validation,

            -- Platform validation flags
            c.whatsapp_validated,
            c.instagram_validated,
            c.facebook_validated,
            c.google_validated,
            c.apple_validated,

            -- Lead score (target variable)
            ls.total_score,
            ls.whatsapp_score,
            ls.instagram_score,
            ls.facebook_score,
            ls.google_score,
            ls.apple_score,
            ls.platform_count,
            ls.business_account_count,
            ls.premium_account_count,
            ls.confidence_level,

            -- Platform validation details
            COALESCE(
                json_agg(
                    json_build_object(
                        'platform', pv.platform,
                        'is_valid', pv.is_valid,
                        'is_business', pv.is_business,
                        'is_premium', pv.is_premium,
                        'confidence_score', pv.confidence_score,
                        'response_time_ms', pv.response_time_ms
                    )
                ) FILTER (WHERE pv.id IS NOT NULL),
                '[]'::json
            ) as platform_validations

        FROM contacts c
        LEFT JOIN lead_scores ls ON c.id = ls.contact_id
        LEFT JOIN platform_validations pv ON c.id = pv.contact_id
        WHERE ls.total_score IS NOT NULL  -- Only contacts with scores
        GROUP BY c.id, ls.id
        ORDER BY c.id
        LIMIT 10000  -- Limit for training data
        """

        result = await db.execute(text(query))
        raw_data = result.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame([dict(row) for row in raw_data])

        # Feature engineering
        df = self._engineer_features(df)

        return df

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer features for ML model"""

        # Platform presence features
        df['has_whatsapp'] = df['whatsapp_validated'].fillna(False).astype(bool)
        df['has_instagram'] = df['instagram_validated'].fillna(False).astype(bool)
        df['has_facebook'] = df['facebook_validated'].fillna(False).astype(bool)
        df['has_google'] = df['google_validated'].fillna(False).astype(bool)
        df['has_apple'] = df['apple_validated'].fillna(False).astype(bool)

        # Fill missing scores with 0
        score_columns = ['whatsapp_score', 'instagram_score', 'facebook_score', 'google_score', 'apple_score']
        for col in score_columns:
            df[col] = df[col].fillna(0)

        # Calculate profile completeness
        profile_fields = ['full_name', 'state_name', 'municipality', 'lada']
        df['profile_completeness'] = df[profile_fields].notna().sum(axis=1) / len(profile_fields)

        # Calculate account age in days
        df['account_age_days'] = (pd.Timestamp.now() - pd.to_datetime(df['created_at'])).dt.days

        # Calculate validation recency
        df['validation_recency_days'] = (
            pd.Timestamp.now() - pd.to_datetime(df['last_platform_validation'])
        ).dt.days.fillna(999)  # 999 for never validated

        # Derived boolean features
        df['has_business_accounts'] = df['business_account_count'] > 0
        df['has_premium_accounts'] = df['premium_account_count'] > 0
        df['is_multi_platform'] = df['platform_count'] >= 2
        df['meta_ecosystem_user'] = df['has_whatsapp'] & (df['has_facebook'] | df['has_instagram'])
        df['tech_ecosystem_user'] = df['has_google'] & df['has_apple']

        # Calculate average confidence from platform validations
        def extract_avg_confidence(validations_json):
            try:
                validations = json.loads(validations_json) if isinstance(validations_json, str) else validations_json
                if validations:
                    confidences = [v.get('confidence_score', 0.5) for v in validations if v.get('is_valid')]
                    return np.mean(confidences) if confidences else 0.5
                return 0.5
            except:
                return 0.5

        df['avg_confidence_score'] = df['platform_validations'].apply(extract_avg_confidence)

        # Geographic consistency (simplified)
        major_ladas_by_state = {
            'SINALOA': ['667', '668', '669'],
            'JALISCO': ['33', '322', '374'],
            'CDMX': ['55', '56'],
            'NUEVO LEON': ['81', '826', '828'],
            # Add more mappings
        }

        def check_geo_consistency(row):
            state = row['state_name']
            lada = row['lada']
            if state and lada and state in major_ladas_by_state:
                return 1.0 if lada in major_ladas_by_state[state] else 0.3
            return 0.5  # Unknown

        df['geographic_consistency'] = df.apply(check_geo_consistency, axis=1)

        return df

    async def train_model(self, db: AsyncSession) -> Dict[str, Any]:
        """Train ML model with current data"""

        # Prepare training data
        df = await self.prepare_training_data(db)

        if len(df) < 100:
            raise ValueError("Insufficient training data (need at least 100 samples)")

        # Select features
        feature_columns = [col for col in df.columns if col in self.feature_definitions.keys()]
        X = df[feature_columns]
        y = df['total_score']

        # Handle missing values
        X = X.fillna(0)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train model
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )

        self.model.fit(X_train_scaled, y_train)

        # Evaluate model
        y_pred = self.model.predict(X_test_scaled)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # Save model and scaler
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)

        # Store feature names
        self.feature_names = feature_columns

        training_results = {
            "model_version": self.model_version,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "mse": float(mse),
            "r2_score": float(r2),
            "feature_count": len(feature_columns),
            "feature_names": feature_columns,
            "feature_importance": dict(zip(feature_columns, self.model.feature_importances_)),
            "training_timestamp": datetime.utcnow().isoformat()
        }

        return training_results

    async def predict_lead_score(self, contact_features: Dict[str, Any]) -> Tuple[int, float]:
        """Predict lead score using trained ML model"""

        if not self.model or not self.scaler:
            # Load model if not in memory
            try:
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
            except:
                # Fallback to rule-based scoring
                return self._fallback_rule_based_score(contact_features)

        # Prepare features
        feature_vector = []
        for feature_name in self.feature_names:
            value = contact_features.get(feature_name, 0)
            feature_vector.append(value)

        # Scale features
        feature_array = np.array(feature_vector).reshape(1, -1)
        scaled_features = self.scaler.transform(feature_array)

        # Predict
        prediction = self.model.predict(scaled_features)[0]

        # Get prediction confidence (using model's prediction variance)
        # For Random Forest, we can use the variance across trees
        tree_predictions = [tree.predict(scaled_features)[0] for tree in self.model.estimators_]
        prediction_std = np.std(tree_predictions)
        confidence = max(0.5, 1.0 - (prediction_std / 50))  # Normalize std to confidence

        # Ensure score is in valid range
        final_score = max(0, min(100, int(prediction)))

        return final_score, confidence

    def _fallback_rule_based_score(self, features: Dict[str, Any]) -> Tuple[int, float]:
        """Fallback to rule-based scoring if ML model unavailable"""

        score = 0
        confidence = 0.7  # Lower confidence for rule-based

        # Simple rule-based calculation
        platform_scores = [
            features.get('whatsapp_score', 0),
            features.get('instagram_score', 0),
            features.get('facebook_score', 0),
            features.get('google_score', 0),
            features.get('apple_score', 0)
        ]

        base_score = sum(platform_scores)

        # Platform count bonus
        platform_count = features.get('platform_count', 0)
        if platform_count >= 3:
            base_score += 10
        elif platform_count >= 2:
            base_score += 5

        # Business account bonus
        if features.get('has_business_accounts', False):
            base_score += 5

        final_score = min(100, base_score)

        return final_score, confidence
```

### 🌆 **TARDE (4 horas): Integración y Automatización**

#### ✅ **BLOQUE 3: Background Processing (2 horas)**

**Tarea 3.1: Sistema de scoring automático**

```python
# app/workers/scoring_worker.py - NUEVO ARCHIVO
import asyncio
from celery import Celery
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.services.advanced_lead_scoring import AdvancedLeadScoringService
from app.services.ml_scoring_service import MLLeadScoringService

# Celery app
celery_app = Celery('lead_scoring_worker')

@celery_app.task(bind=True, max_retries=3)
def calculate_lead_score_task(self, contact_id: int):
    """Celery task to calculate lead score for contact"""

    async def _calculate():
        async for db in get_async_db():
            scoring_service = AdvancedLeadScoringService(db)
            result = await scoring_service.calculate_comprehensive_score(contact_id)
            return result

    try:
        result = asyncio.run(_calculate())
        return {
            "status": "success",
            "contact_id": contact_id,
            "score": result.total_score if result else None
        }
    except Exception as e:
        # Retry with exponential backoff
        self.retry(countdown=60 * (2 ** self.request.retries))

@celery_app.task(bind=True)
def batch_calculate_scores_task(self, contact_ids: List[int]):
    """Celery task to calculate scores for multiple contacts"""

    async def _batch_calculate():
        results = []
        async for db in get_async_db():
            scoring_service = AdvancedLeadScoringService(db)

            for contact_id in contact_ids:
                try:
                    result = await scoring_service.calculate_comprehensive_score(contact_id)
                    results.append({
                        "contact_id": contact_id,
                        "status": "success",
                        "score": result.total_score if result else None
                    })
                except Exception as e:
                    results.append({
                        "contact_id": contact_id,
                        "status": "error",
                        "error": str(e)
                    })

                # Small delay to avoid overwhelming the system
                await asyncio.sleep(0.1)

        return results

    return asyncio.run(_batch_calculate())

@celery_app.task(bind=True)
def retrain_ml_model_task(self):
    """Periodic task to retrain ML model with new data"""

    async def _retrain():
        async for db in get_async_db():
            ml_service = MLLeadScoringService()
            training_results = await ml_service.train_model(db)
            return training_results

    return asyncio.run(_retrain())
```

#### ✅ **BLOQUE 4: Dashboard Integration (2 horas)**

**Tarea 4.1: Expandir dashboard con lead scoring**

```typescript
// WebDashboard/src/components/contacts/LeadScoreCard.tsx - NUEVO
import React from "react";
import { StarIcon, TrophyIcon, FireIcon } from "@heroicons/react/24/outline";
import { StarIcon as StarSolidIcon } from "@heroicons/react/24/solid";

interface LeadScoreCardProps {
  leadScore: LeadScore;
  compact?: boolean;
}

export const LeadScoreCard: React.FC<LeadScoreCardProps> = ({
  leadScore,
  compact = false,
}) => {
  const getScoreColor = (score: number) => {
    if (score >= 90) return "text-purple-600 bg-purple-50";
    if (score >= 75) return "text-green-600 bg-green-50";
    if (score >= 50) return "text-yellow-600 bg-yellow-50";
    if (score >= 25) return "text-orange-600 bg-orange-50";
    return "text-red-600 bg-red-50";
  };

  const getTierIcon = (tier: string) => {
    switch (tier) {
      case "PREMIUM":
        return <TrophyIcon className="h-5 w-5 text-purple-600" />;
      case "HIGH":
        return <StarSolidIcon className="h-5 w-5 text-green-600" />;
      case "MEDIUM":
        return <StarIcon className="h-5 w-5 text-yellow-600" />;
      default:
        return <FireIcon className="h-5 w-5 text-gray-600" />;
    }
  };

  const platformScores = [
    { name: "WhatsApp", score: leadScore.whatsappScore, max: 25 },
    { name: "Instagram", score: leadScore.instagramScore, max: 20 },
    { name: "Facebook", score: leadScore.facebookScore, max: 20 },
    { name: "Google", score: leadScore.googleScore, max: 20 },
    { name: "Apple", score: leadScore.appleScore, max: 15 },
  ];

  if (compact) {
    return (
      <div
        className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(
          leadScore.totalScore
        )}`}
      >
        {getTierIcon(leadScore.qualityTier)}
        <span className="ml-1">{leadScore.totalScore}</span>
      </div>
    );
  }

  return (
    <div className="bg-white border rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">
          Lead Score Analysis
        </h3>
        <div
          className={`flex items-center px-3 py-1 rounded-full ${getScoreColor(
            leadScore.totalScore
          )}`}
        >
          {getTierIcon(leadScore.qualityTier)}
          <span className="ml-2 font-bold">{leadScore.totalScore}/100</span>
        </div>
      </div>

      {/* Platform Breakdown */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-gray-700">
          Platform Breakdown
        </h4>
        {platformScores.map((platform) => (
          <div
            key={platform.name}
            className="flex items-center justify-between"
          >
            <span className="text-sm text-gray-600">{platform.name}</span>
            <div className="flex items-center">
              <div className="w-24 bg-gray-200 rounded-full h-2 mr-3">
                <div
                  className={`h-2 rounded-full ${
                    platform.score > 0 ? "bg-blue-600" : "bg-gray-300"
                  }`}
                  style={{ width: `${(platform.score / platform.max) * 100}%` }}
                />
              </div>
              <span className="text-sm font-medium text-gray-900 w-8 text-right">
                {platform.score}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Summary Stats */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Platforms</span>
            <div className="font-medium">{leadScore.platformCount}/5</div>
          </div>
          <div>
            <span className="text-gray-500">Business Accounts</span>
            <div className="font-medium">{leadScore.businessAccountCount}</div>
          </div>
          <div>
            <span className="text-gray-500">Confidence</span>
            <div className="font-medium">
              {(leadScore.confidenceLevel * 100).toFixed(1)}%
            </div>
          </div>
          <div>
            <span className="text-gray-500">Last Updated</span>
            <div className="font-medium">
              {new Date(leadScore.lastCalculatedAt).toLocaleDateString()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
```

---

## 📅 DÍA 9: AUTOMATIZACIÓN Y OPTIMIZACIÓN

### 🌅 **MAÑANA (4 horas): Scoring Automático**

#### ✅ **BLOQUE 5: Triggers de Base de Datos (1.5 horas)**

**Tarea 5.1: Triggers para scoring automático**

```sql
-- migrations/versions/006_scoring_triggers.sql
-- Trigger para calcular score automáticamente cuando se actualiza validación

CREATE OR REPLACE FUNCTION trigger_recalculate_lead_score()
RETURNS TRIGGER AS $$
BEGIN
    -- Schedule lead score recalculation
    INSERT INTO scoring_queue (contact_id, priority, created_at)
    VALUES (NEW.contact_id, 5, NOW())
    ON CONFLICT (contact_id) DO UPDATE SET
        priority = GREATEST(scoring_queue.priority, 5),
        updated_at = NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on platform_validations
CREATE TRIGGER trigger_platform_validation_scoring
    AFTER INSERT OR UPDATE ON platform_validations
    FOR EACH ROW
    EXECUTE FUNCTION trigger_recalculate_lead_score();

-- Create scoring queue table
CREATE TABLE scoring_queue (
    contact_id INTEGER PRIMARY KEY REFERENCES contacts(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_scoring_queue_priority ON scoring_queue(priority DESC, created_at ASC);
```

#### ✅ **BLOQUE 6: Worker de Scoring (1.5 horas)**

**Tarea 6.1: Worker para procesar queue de scoring**

```python
# app/workers/lead_scoring_worker.py - EXPANDIR
@celery_app.task(bind=True)
def process_scoring_queue_task(self):
    """Process pending lead score calculations"""

    async def _process_queue():
        async for db in get_async_db():
            # Get pending items from queue
            queue_query = """
            SELECT contact_id, priority
            FROM scoring_queue
            ORDER BY priority DESC, created_at ASC
            LIMIT 100
            """

            result = await db.execute(text(queue_query))
            pending_items = result.fetchall()

            if not pending_items:
                return {"message": "No items in scoring queue"}

            scoring_service = AdvancedLeadScoringService(db)
            processed = 0
            errors = 0

            for item in pending_items:
                contact_id = item.contact_id
                try:
                    # Calculate score
                    await scoring_service.calculate_comprehensive_score(contact_id)

                    # Remove from queue
                    await db.execute(
                        text("DELETE FROM scoring_queue WHERE contact_id = :contact_id"),
                        {"contact_id": contact_id}
                    )

                    processed += 1

                except Exception as e:
                    # Update attempt count
                    await db.execute(
                        text("""
                        UPDATE scoring_queue
                        SET attempts = attempts + 1, last_attempt_at = NOW()
                        WHERE contact_id = :contact_id
                        """),
                        {"contact_id": contact_id}
                    )

                    errors += 1

                    # Remove from queue if too many attempts
                    if item.attempts >= 3:
                        await db.execute(
                            text("DELETE FROM scoring_queue WHERE contact_id = :contact_id"),
                            {"contact_id": contact_id}
                        )

                # Small delay to avoid overwhelming system
                await asyncio.sleep(0.1)

            await db.commit()

            return {
                "processed": processed,
                "errors": errors,
                "total_items": len(pending_items)
            }

    return asyncio.run(_process_queue())

# Schedule periodic scoring queue processing
@celery_app.task
def schedule_scoring_queue_processing():
    """Periodic task to process scoring queue"""
    process_scoring_queue_task.delay()

# Setup periodic task (every 5 minutes)
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'process-scoring-queue': {
        'task': 'app.workers.lead_scoring_worker.schedule_scoring_queue_processing',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'retrain-ml-model': {
        'task': 'app.workers.lead_scoring_worker.retrain_ml_model_task',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
```

#### ✅ **BLOQUE 7: Dashboard Lead Scoring UI (1 hora)**

**Tarea 7.1: Expandir ContactList con scores**

```typescript
// WebDashboard/src/components/contacts/ContactList.tsx - AGREGAR COLUMNA
// Agregar columna de Lead Score a la tabla

const columns = [
  // ... columnas existentes ...
  {
    header: "Lead Score",
    accessor: "leadScore",
    sortable: true,
    render: (contact: ContactWithValidations) => (
      <div className="flex items-center">
        {contact.leadScore ? (
          <LeadScoreCard leadScore={contact.leadScoreRecord} compact={true} />
        ) : (
          <button
            onClick={() => triggerScoreCalculation(contact.id)}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            Calculate
          </button>
        )}
      </div>
    ),
  },
  {
    header: "Platforms",
    accessor: "validatedPlatforms",
    render: (contact: ContactWithValidations) => (
      <ValidationStatus contact={contact} compact={true} />
    ),
  },
];
```

#### ✅ **BLOQUE 8: Analytics de Lead Scoring (1.5 hours)**

**Tarea 8.1: Dashboard de lead scoring**

```typescript
// WebDashboard/src/pages/Analytics/LeadScoringAnalytics.tsx - NUEVO
import React, { useEffect, useState } from "react";
import { Bar, Doughnut, Line } from "react-chartjs-2";

interface LeadScoringAnalyticsProps {}

export const LeadScoringAnalytics: React.FC = () => {
  const [scoringStats, setScoringStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchScoringStats();
  }, []);

  const fetchScoringStats = async () => {
    try {
      const response = await fetch("/api/v1/lead-scoring/analytics");
      const data = await response.json();
      setScoringStats(data);
    } catch (error) {
      console.error("Error fetching scoring stats:", error);
    } finally {
      setLoading(false);
    }
  };

  // Score distribution chart
  const scoreDistributionData = {
    labels: ["0-20", "21-40", "41-60", "61-80", "81-100"],
    datasets: [
      {
        label: "Lead Distribution",
        data: scoringStats?.scoreDistribution || [0, 0, 0, 0, 0],
        backgroundColor: [
          "#ef4444",
          "#f97316",
          "#eab308",
          "#22c55e",
          "#8b5cf6",
        ],
      },
    ],
  };

  // Platform validation success rates
  const platformSuccessData = {
    labels: ["WhatsApp", "Instagram", "Facebook", "Google", "Apple"],
    datasets: [
      {
        label: "Validation Success Rate",
        data: scoringStats?.platformSuccessRates || [0, 0, 0, 0, 0],
        backgroundColor: "#3b82f6",
      },
    ],
  };

  return (
    <div className="space-y-6">
      <div className="sm:flex sm:items-center sm:justify-between">
        <h2 className="text-2xl font-bold text-gray-900">
          Lead Scoring Analytics
        </h2>
        <button onClick={fetchScoringStats} className="btn-primary">
          Refresh Data
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrophyIcon className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Premium Leads
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {scoringStats?.premiumLeadsCount?.toLocaleString() || "0"}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <StarIcon className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Average Score
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {scoringStats?.averageScore?.toFixed(1) || "0.0"}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FireIcon className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Validated Contacts
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {scoringStats?.validatedContactsCount?.toLocaleString() ||
                      "0"}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <StarIcon className="h-6 w-6 text-yellow-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Multi-Platform
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {scoringStats?.multiPlatformCount?.toLocaleString() || "0"}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Score Distribution
          </h3>
          <div className="h-80">
            <Doughnut data={scoreDistributionData} />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Platform Success Rates
          </h3>
          <div className="h-80">
            <Bar data={platformSuccessData} />
          </div>
        </div>
      </div>
    </div>
  );
};
```

---

## 🎯 CRITERIOS DE ACEPTACIÓN

### **✅ Al Final del Día 8:**

- [ ] Algoritmo de scoring avanzado funcionando
- [ ] ML pipeline base implementado
- [ ] Background processing con Celery
- [ ] Triggers automáticos en base de datos
- [ ] Sistema de queue para scoring

### **✅ Al Final del Día 9:**

- [ ] Dashboard mostrando lead scores
- [ ] Analytics de scoring funcionando
- [ ] Componentes de visualización operativos
- [ ] Scoring automático para nuevas validaciones
- [ ] Performance optimizada para gran volumen

---

## 🚨 TROUBLESHOOTING

### **Problema: ML model no converge**

- **Solución:** Usar fallback rule-based scoring
- **Datos:** Verificar calidad de training data
- **Features:** Revisar feature engineering

### **Problema: Scoring queue se acumula**

- **Solución:** Aumentar workers de Celery
- **Optimizar:** Batch processing más eficiente
- **Monitor:** Queue length metrics

### **Problema: Scores inconsistentes**

- **Solución:** Validar algoritmo con casos conocidos
- **Audit:** Log de cálculos para debugging
- **Calibrar:** Ajustar pesos de plataformas

---

## 📊 MÉTRICAS DE PROGRESO

- **Algoritmo de Scoring:** 40% del total
- **ML Pipeline:** 25% del total
- **Background Processing:** 20% del total
- **Dashboard Integration:** 15% del total

**Total Fase 4:** 100% → **Preparado para Fase 5**

---

## 🚀 RESULTADO ESPERADO

### **Al Completar Fase 4:**

- ✅ **Lead scoring inteligente** operativo
- ✅ **31.8M contactos enriquecidos** con puntuaciones
- ✅ **ML pipeline** preparado para mejoras
- ✅ **Dashboard analytics** con insights de calidad
- ✅ **Scoring automático** para nuevas validaciones

### **🎉 Valor de Negocio:**

- **Leads calificados** automáticamente
- **ROI mejorado** en campañas SMS
- **Targeting inteligente** basado en scores
- **Insights únicos** sobre calidad de base de datos

**→ Continuar con [Fase 5: Integración Completa](./fase5-integracion-completa.md)**

---

_Fase 4: Lead Scoring Inteligente_
_SMS Marketing Platform v2.0 - Migración Sistema Actual_
_Implementación Detallada_
