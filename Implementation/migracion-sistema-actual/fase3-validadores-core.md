# 🔍 FASE 3: VALIDADORES CORE (Días 5-7)

## SMS Marketing Platform v2.0 - Migración Sistema Actual

---

## 🎯 OBJETIVO DE LA FASE

Implementar los validadores core (WhatsApp e Instagram) como microservicios, crear el orquestador de validaciones e integrar con el sistema existente para enriquecer los 31.8M contactos.

**Duración:** 3 días
**Complejidad:** ALTA
**Riesgo:** MEDIO - Servicios externos
**Prioridad:** CRÍTICA

---

## 🏗️ ARQUITECTURA DE VALIDADORES

### **📱 Estrategia Multi-Método:**

Cada validador implementa múltiples métodos para maximizar éxito y evitar detección:

#### **WhatsApp Validator:**

1. **Business API** (método premium)
2. **Web scraping** (método backup)
3. **Bulk validation** (método eficiente)

#### **Instagram Validator:**

1. **Login check** (verificar existencia)
2. **Password reset** (método sigiloso)
3. **Signup availability** (verificar disponibilidad)

### **🔄 Orquestador Central:**

- **Load balancing** entre validadores
- **Retry logic** inteligente
- **Rate limiting** adaptativo
- **Result aggregation** y scoring

---

## 📅 DÍA 5: WHATSAPP VALIDATOR

### 🌅 **MAÑANA (4 horas): WhatsApp Validator Base**

#### ✅ **BLOQUE 1: Estructura del Microservicio (1.5 horas)**

**Tarea 1.1: Crear estructura del proyecto**

```bash
# Crear estructura
mkdir -p Services/WhatsAppValidator
cd Services/WhatsAppValidator

# Estructura del microservicio
Services/WhatsAppValidator/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Configuración
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request.py          # Pydantic models
│   │   ├── response.py         # Response schemas
│   │   └── validation.py       # Business models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── validator.py        # Core validation logic
│   │   ├── proxy_manager.py    # Proxy rotation
│   │   ├── rate_limiter.py     # Rate limiting
│   │   └── cache_manager.py    # Caching layer
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── phone_utils.py      # Phone formatting
│   │   ├── retry_utils.py      # Retry logic
│   │   └── metrics.py          # Prometheus metrics
│   └── api/
│       ├── __init__.py
│       └── routes.py           # API endpoints
├── tests/
├── Dockerfile
├── requirements.txt
└── docker-compose.test.yml
```

**Tarea 1.2: Configuración base**

```python
# Services/WhatsAppValidator/app/config.py
from pydantic import BaseSettings
from typing import List, Dict, Any

class WhatsAppValidatorConfig(BaseSettings):
    # Service configuration
    service_name: str = "whatsapp-validator"
    port: int = 8001
    debug: bool = False

    # Database connections
    database_url: str
    redis_url: str

    # WhatsApp specific
    whatsapp_business_api_token: str = ""
    whatsapp_business_api_url: str = "https://graph.facebook.com/v18.0"

    # Rate limiting
    rate_limit_per_minute: int = 200
    rate_limit_per_hour: int = 2000
    rate_limit_per_day: int = 20000

    # Proxy configuration
    proxy_enabled: bool = True
    proxy_pool_size: int = 50
    proxy_rotation_interval: int = 300  # 5 minutes
    proxy_health_check_interval: int = 60  # 1 minute
    proxy_urls: List[str] = []

    # Caching
    cache_ttl_hours: int = 24
    cache_max_entries: int = 100000

    # Retry logic
    max_retries: int = 3
    retry_delay_seconds: int = 1
    retry_backoff_factor: float = 2.0

    # Monitoring
    metrics_enabled: bool = True
    prometheus_port: int = 9001

    # Security
    api_key_header: str = "X-API-Key"
    allowed_ips: List[str] = ["127.0.0.1", "localhost"]

    class Config:
        env_file = ".env"
        env_prefix = "WHATSAPP_"
```

**Tarea 1.3: FastAPI app principal**

```python
# Services/WhatsAppValidator/app/main.py
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import uvicorn

from app.config import WhatsAppValidatorConfig
from app.api.routes import router as api_router
from app.services.validator import WhatsAppValidationService
from app.utils.metrics import setup_metrics

# Load configuration
config = WhatsAppValidatorConfig()

# Create FastAPI app
app = FastAPI(
    title="WhatsApp Validator Service",
    description="Microservice for validating WhatsApp numbers",
    version="1.0.0",
    docs_url="/docs" if config.debug else None,
    redoc_url="/redoc" if config.debug else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Setup metrics
if config.metrics_enabled:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": config.service_name,
        "version": "1.0.0",
        "timestamp": datetime.utcnow()
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # Initialize validation service
    validation_service = WhatsAppValidationService(config)
    await validation_service.initialize()

    # Setup metrics
    setup_metrics()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=config.port,
        reload=config.debug
    )
```

#### ✅ **BLOQUE 2: Core Validation Service (2.5 horas)**

**Tarea 2.1: WhatsApp validation logic**

```python
# Services/WhatsAppValidator/app/services/validator.py
import asyncio
import httpx
import random
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.models.response import ValidationResult, ValidationError
from app.services.proxy_manager import ProxyManager
from app.services.rate_limiter import RateLimiter
from app.services.cache_manager import CacheManager
from app.utils.phone_utils import format_phone_for_whatsapp
from app.config import WhatsAppValidatorConfig

class WhatsAppValidationService:
    """Core WhatsApp validation service with multiple methods"""

    def __init__(self, config: WhatsAppValidatorConfig):
        self.config = config
        self.proxy_manager = ProxyManager(config)
        self.rate_limiter = RateLimiter(config)
        self.cache_manager = CacheManager(config)
        self.client: Optional[httpx.AsyncClient] = None

        # Method priority (try in order)
        self.validation_methods = [
            self._validate_via_business_api,
            self._validate_via_web_check,
            self._validate_via_existence_check
        ]

    async def initialize(self):
        """Initialize the validation service"""
        await self.proxy_manager.initialize()
        await self.rate_limiter.initialize()
        await self.cache_manager.initialize()

        # Create HTTP client with optimized settings
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            headers={
                "User-Agent": "WhatsApp/2.23.20.0 (iPhone; iOS 16.0; Scale/3.00)"
            }
        )

    async def validate_number(self, phone_e164: str) -> ValidationResult:
        """Validate WhatsApp number using best available method"""

        # Check cache first
        cached_result = await self.cache_manager.get_validation(phone_e164, "whatsapp")
        if cached_result and not cached_result.is_expired():
            return cached_result

        # Apply rate limiting
        await self.rate_limiter.acquire()

        # Format phone for WhatsApp
        formatted_phone = format_phone_for_whatsapp(phone_e164)

        # Try validation methods in priority order
        last_error = None
        for method in self.validation_methods:
            try:
                result = await method(formatted_phone)

                # Cache successful result
                await self.cache_manager.set_validation(phone_e164, "whatsapp", result)

                return result

            except ValidationError as e:
                last_error = e
                continue
            except Exception as e:
                last_error = ValidationError(f"Unexpected error in {method.__name__}: {str(e)}")
                continue

        # All methods failed
        error_result = ValidationResult(
            phone_e164=phone_e164,
            platform="whatsapp",
            is_valid=False,
            confidence_score=0.0,
            error=str(last_error) if last_error else "All validation methods failed",
            validated_at=datetime.utcnow()
        )

        # Cache failed result with shorter TTL
        await self.cache_manager.set_validation(phone_e164, "whatsapp", error_result, ttl_hours=1)

        return error_result

    async def _validate_via_business_api(self, phone: str) -> ValidationResult:
        """Validate using WhatsApp Business API (most reliable)"""
        if not self.config.whatsapp_business_api_token:
            raise ValidationError("Business API token not configured")

        headers = {
            "Authorization": f"Bearer {self.config.whatsapp_business_api_token}",
            "Content-Type": "application/json"
        }

        # WhatsApp Business API endpoint for checking number
        url = f"{self.config.whatsapp_business_api_url}/contacts"
        payload = {
            "blocking": "wait",
            "contacts": [phone],
            "force_check": True
        }

        start_time = datetime.utcnow()

        async with self.client as client:
            response = await client.post(url, json=payload, headers=headers)

            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            if response.status_code == 200:
                data = response.json()
                contacts = data.get("contacts", [])

                if contacts:
                    contact_info = contacts[0]
                    return ValidationResult(
                        phone_e164=phone,
                        platform="whatsapp",
                        is_valid=contact_info.get("status") == "valid",
                        is_business=contact_info.get("wa_id", "").endswith("@c.us"),
                        confidence_score=0.95,  # High confidence for Business API
                        platform_details={
                            "wa_id": contact_info.get("wa_id"),
                            "status": contact_info.get("status"),
                            "api_method": "business_api"
                        },
                        validation_method="business_api",
                        response_time_ms=int(response_time),
                        validated_at=datetime.utcnow()
                    )

            raise ValidationError(f"Business API returned {response.status_code}: {response.text}")

    async def _validate_via_web_check(self, phone: str) -> ValidationResult:
        """Validate using web scraping method (backup)"""

        # Get random proxy
        proxy = await self.proxy_manager.get_random_proxy()

        # Simulate WhatsApp Web check
        headers = {
            "User-Agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            ]),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
            "Referer": "https://web.whatsapp.com/",
        }

        start_time = datetime.utcnow()

        # Simulate validation (replace with actual implementation)
        await asyncio.sleep(random.uniform(1.0, 3.0))  # Simulate network delay

        # Mock validation result (replace with real logic)
        is_valid = random.choice([True, False, True])  # 66% success rate

        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ValidationResult(
            phone_e164=phone,
            platform="whatsapp",
            is_valid=is_valid,
            is_business=random.choice([True, False]) if is_valid else False,
            confidence_score=0.75,  # Medium confidence for web scraping
            platform_details={
                "method": "web_scraping",
                "proxy_used": proxy.get("url") if proxy else None,
                "user_agent": headers["User-Agent"]
            },
            validation_method="web_scraping",
            response_time_ms=int(response_time),
            validated_at=datetime.utcnow()
        )

    async def _validate_via_existence_check(self, phone: str) -> ValidationResult:
        """Basic existence check (fallback method)"""

        start_time = datetime.utcnow()

        # Basic phone format validation
        if not phone.startswith("+52") or len(phone) != 13:
            raise ValidationError("Invalid phone format for WhatsApp")

        # Simulate basic existence check
        await asyncio.sleep(random.uniform(0.5, 1.5))

        # Simple heuristic based on LADA and format
        lada = phone[3:6]
        known_mobile_ladas = ["667", "33", "55", "81", "229"]  # Major cities

        is_likely_valid = lada in known_mobile_ladas

        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ValidationResult(
            phone_e164=phone,
            platform="whatsapp",
            is_valid=is_likely_valid,
            is_business=False,  # Cannot determine from basic check
            confidence_score=0.60,  # Low confidence for basic check
            platform_details={
                "method": "existence_check",
                "lada": lada,
                "heuristic": "mobile_lada_check"
            },
            validation_method="existence_check",
            response_time_ms=int(response_time),
            validated_at=datetime.utcnow()
        )

    async def validate_batch(self, phones: List[str]) -> List[ValidationResult]:
        """Validate multiple numbers efficiently"""

        if len(phones) > 100:
            raise ValidationError("Batch size cannot exceed 100 numbers")

        # Process in smaller concurrent batches
        batch_size = min(10, len(phones))
        results = []

        for i in range(0, len(phones), batch_size):
            batch = phones[i:i + batch_size]

            # Process batch concurrently
            batch_tasks = [self.validate_number(phone) for phone in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Handle results and exceptions
            for phone, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    error_result = ValidationResult(
                        phone_e164=phone,
                        platform="whatsapp",
                        is_valid=False,
                        confidence_score=0.0,
                        error=str(result),
                        validated_at=datetime.utcnow()
                    )
                    results.append(error_result)
                else:
                    results.append(result)

            # Rate limiting between batches
            if i + batch_size < len(phones):
                await asyncio.sleep(1.0)

        return results
```

#### ✅ **BLOQUE 3: Proxy Management (1 hora)**

**Tarea 3.1: Sistema de proxies**

```python
# Services/WhatsAppValidator/app/services/proxy_manager.py
import asyncio
import httpx
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class ProxyManager:
    """Manage proxy rotation and health checking"""

    def __init__(self, config):
        self.config = config
        self.proxies: List[Dict] = []
        self.healthy_proxies: List[Dict] = []
        self.proxy_stats: Dict[str, Dict] = {}
        self.health_check_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize proxy manager"""
        if not self.config.proxy_enabled:
            return

        # Load proxies from configuration
        for proxy_url in self.config.proxy_urls:
            proxy_info = {
                "url": proxy_url,
                "healthy": True,
                "last_check": None,
                "success_count": 0,
                "error_count": 0,
                "avg_response_time": 0.0
            }
            self.proxies.append(proxy_info)
            self.healthy_proxies.append(proxy_info)

        # Start health check task
        if self.proxies:
            self.health_check_task = asyncio.create_task(self._health_check_loop())

    async def get_random_proxy(self) -> Optional[Dict]:
        """Get random healthy proxy"""
        if not self.healthy_proxies:
            return None

        return random.choice(self.healthy_proxies)

    async def _health_check_loop(self):
        """Continuously check proxy health"""
        while True:
            try:
                await self._check_all_proxies()
                await asyncio.sleep(self.config.proxy_health_check_interval)
            except Exception as e:
                # Log error but continue
                print(f"Proxy health check error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def _check_all_proxies(self):
        """Check health of all proxies"""
        tasks = [self._check_proxy_health(proxy) for proxy in self.proxies]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Update healthy proxies list
        self.healthy_proxies = [p for p in self.proxies if p["healthy"]]

    async def _check_proxy_health(self, proxy: Dict):
        """Check individual proxy health"""
        try:
            start_time = datetime.utcnow()

            async with httpx.AsyncClient(proxies=proxy["url"], timeout=10.0) as client:
                response = await client.get("https://httpbin.org/ip")

                if response.status_code == 200:
                    response_time = (datetime.utcnow() - start_time).total_seconds()

                    proxy["healthy"] = True
                    proxy["last_check"] = datetime.utcnow()
                    proxy["success_count"] += 1
                    proxy["avg_response_time"] = (
                        proxy["avg_response_time"] + response_time
                    ) / 2
                else:
                    proxy["healthy"] = False
                    proxy["error_count"] += 1

        except Exception:
            proxy["healthy"] = False
            proxy["error_count"] += 1
            proxy["last_check"] = datetime.utcnow()
```

### 🌆 **TARDE (4 horas): Instagram Validator**

#### ✅ **BLOQUE 4: Instagram Validator Structure (2 horas)**

**Tarea 4.1: Instagram validation service**

```python
# Services/InstagramValidator/app/services/validator.py
import asyncio
import httpx
import random
from typing import Optional, List, Dict, Any
from datetime import datetime

class InstagramValidationService:
    """Instagram validation with anti-detection measures"""

    def __init__(self, config):
        self.config = config
        self.session_manager = InstagramSessionManager(config)
        self.rate_limiter = RateLimiter(config)
        self.cache_manager = CacheManager(config)

    async def validate_number(self, phone_e164: str) -> ValidationResult:
        """Validate Instagram account associated with phone"""

        # Check cache
        cached_result = await self.cache_manager.get_validation(phone_e164, "instagram")
        if cached_result and not cached_result.is_expired():
            return cached_result

        # Rate limiting
        await self.rate_limiter.acquire()

        # Try validation methods
        methods = [
            self._validate_via_login_check,
            self._validate_via_signup_check,
            self._validate_via_password_reset
        ]

        for method in methods:
            try:
                result = await method(phone_e164)
                await self.cache_manager.set_validation(phone_e164, "instagram", result)
                return result
            except Exception as e:
                continue

        # All methods failed
        return ValidationResult(
            phone_e164=phone_e164,
            platform="instagram",
            is_valid=False,
            confidence_score=0.0,
            error="All validation methods failed",
            validated_at=datetime.utcnow()
        )

    async def _validate_via_login_check(self, phone: str) -> ValidationResult:
        """Check if phone is associated with Instagram account"""

        start_time = datetime.utcnow()

        # Get session with rotation
        session = await self.session_manager.get_session()

        # Instagram login check endpoint
        url = "https://www.instagram.com/accounts/account_recovery_send_ajax/"

        payload = {
            "email_or_username": phone,
            "recaptcha_challenge_field": "",
        }

        headers = session["headers"]

        async with httpx.AsyncClient(
            proxies=session.get("proxy"),
            cookies=session.get("cookies", {}),
            timeout=15.0
        ) as client:

            response = await client.post(url, data=payload, headers=headers)
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            if response.status_code == 200:
                data = response.json()

                # Check response for account existence indicators
                is_valid = data.get("user", {}).get("pk") is not None

                return ValidationResult(
                    phone_e164=phone,
                    platform="instagram",
                    is_valid=is_valid,
                    is_business=False,  # Would need additional check
                    confidence_score=0.80,
                    platform_details={
                        "method": "login_check",
                        "response_status": response.status_code,
                        "user_found": is_valid
                    },
                    validation_method="login_check",
                    response_time_ms=int(response_time),
                    validated_at=datetime.utcnow()
                )

            raise ValidationError(f"Instagram API returned {response.status_code}")

    async def _validate_via_signup_check(self, phone: str) -> ValidationResult:
        """Check if phone is available for signup (inverse validation)"""

        start_time = datetime.utcnow()

        url = "https://www.instagram.com/accounts/web_create_ajax/attempt/"

        payload = {
            "phone_number": phone,
            "first_name": "Test",
            "username": f"test{random.randint(10000, 99999)}",
            "password": "TempPassword123!",
            "client_id": datetime.utcnow().timestamp(),
            "seamless_login_enabled": "1"
        }

        headers = {
            "X-CSRFToken": "test",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/accounts/emailsignup/",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, data=payload, headers=headers)
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            if response.status_code == 200:
                data = response.json()

                # If phone is already in use, account exists
                errors = data.get("errors", {})
                phone_error = errors.get("phone_number", [])

                is_valid = any("already" in error.lower() for error in phone_error)

                return ValidationResult(
                    phone_e164=phone,
                    platform="instagram",
                    is_valid=is_valid,
                    confidence_score=0.70,
                    platform_details={
                        "method": "signup_check",
                        "errors": phone_error,
                        "account_exists": is_valid
                    },
                    validation_method="signup_check",
                    response_time_ms=int(response_time),
                    validated_at=datetime.utcnow()
                )

            raise ValidationError(f"Instagram signup check failed: {response.status_code}")
```

#### ✅ **BLOQUE 5: Validation Orchestrator (2 horas)**

**Tarea 5.1: Orquestador central**

```python
# Services/ValidationOrchestrator/app/main.py
from fastapi import FastAPI, BackgroundTasks, Depends
from typing import List, Dict
import asyncio
import httpx

class ValidationOrchestrator:
    """Central orchestrator for all platform validations"""

    def __init__(self):
        self.validators = {
            "whatsapp": "http://whatsapp-validator:8001",
            "instagram": "http://instagram-validator:8002",
            # Future validators
            "facebook": "http://facebook-validator:8003",
            "google": "http://google-validator:8004",
            "apple": "http://apple-validator:8005"
        }
        self.client = httpx.AsyncClient(timeout=30.0)

    async def validate_contact_all_platforms(
        self,
        phone_e164: str,
        platforms: List[str] = None
    ) -> Dict[str, ValidationResult]:
        """Validate contact across multiple platforms"""

        if platforms is None:
            platforms = ["whatsapp", "instagram"]  # Start with core platforms

        # Create validation tasks
        tasks = []
        for platform in platforms:
            if platform in self.validators:
                task = self._validate_single_platform(phone_e164, platform)
                tasks.append((platform, task))

        # Execute validations concurrently
        results = {}
        completed_tasks = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )

        # Process results
        for (platform, _), result in zip(tasks, completed_tasks):
            if isinstance(result, Exception):
                results[platform] = ValidationResult(
                    phone_e164=phone_e164,
                    platform=platform,
                    is_valid=False,
                    confidence_score=0.0,
                    error=str(result),
                    validated_at=datetime.utcnow()
                )
            else:
                results[platform] = result

        return results

    async def _validate_single_platform(self, phone: str, platform: str) -> ValidationResult:
        """Validate on single platform"""
        validator_url = self.validators[platform]

        try:
            response = await self.client.post(
                f"{validator_url}/api/v1/validate",
                json={"phone_e164": phone},
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                return ValidationResult(**data)
            else:
                raise Exception(f"Validator returned {response.status_code}")

        except Exception as e:
            raise Exception(f"Failed to validate {phone} on {platform}: {str(e)}")

# FastAPI app
app = FastAPI(title="Validation Orchestrator", version="1.0.0")
orchestrator = ValidationOrchestrator()

@app.post("/validate/contact")
async def validate_contact(
    phone_e164: str,
    platforms: List[str] = ["whatsapp", "instagram"]
):
    """Main validation endpoint"""
    results = await orchestrator.validate_contact_all_platforms(phone_e164, platforms)
    return {
        "phone_e164": phone_e164,
        "platforms_validated": len(results),
        "results": results,
        "timestamp": datetime.utcnow()
    }

@app.post("/validate/batch")
async def validate_batch(
    phones: List[str],
    platforms: List[str] = ["whatsapp", "instagram"],
    background_tasks: BackgroundTasks = None
):
    """Batch validation endpoint"""

    if len(phones) > 500:
        # Process large batches in background
        background_tasks.add_task(process_large_batch, phones, platforms)
        return {
            "message": f"Large batch of {len(phones)} phones queued for processing",
            "status": "queued"
        }

    # Process smaller batches immediately
    all_results = {}
    for phone in phones:
        results = await orchestrator.validate_contact_all_platforms(phone, platforms)
        all_results[phone] = results

    return {
        "total_phones": len(phones),
        "platforms": platforms,
        "results": all_results,
        "timestamp": datetime.utcnow()
    }
```

---

## 📅 DÍA 6-7: INTEGRACIÓN CON SISTEMA ACTUAL

### 🌅 **DÍA 6 MAÑANA: Integración con Backend Principal**

#### ✅ **BLOQUE 6: Endpoints de Integración (2 horas)**

**Tarea 6.1: Agregar validation endpoints al backend principal**

```python
# app/api/v1/endpoints/validations.py - AGREGAR AL BACKEND PRINCIPAL
from fastapi import APIRouter, Depends, BackgroundTasks
import httpx

router = APIRouter()

@router.post("/validate-contact/{contact_id}")
async def validate_contact_platforms(
    contact_id: int,
    platforms: List[str] = ["whatsapp", "instagram"],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Trigger validation for specific contact"""

    # Get contact
    contact = await db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(404, detail="Contact not found")

    # Start validation in background
    background_tasks.add_task(
        process_contact_validation,
        contact.phone_e164,
        platforms,
        contact_id
    )

    return {
        "message": f"Validation started for contact {contact_id}",
        "phone": contact.phone_e164,
        "platforms": platforms,
        "status": "processing"
    }

async def process_contact_validation(phone_e164: str, platforms: List[str], contact_id: int):
    """Background task to process contact validation"""

    # Call validation orchestrator
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://validation-orchestrator:8020/validate/contact",
            json={
                "phone_e164": phone_e164,
                "platforms": platforms
            }
        )

        if response.status_code == 200:
            results = response.json()

            # Store results in database
            await store_validation_results(contact_id, results["results"])

            # Update contact summary fields
            await update_contact_validation_summary(contact_id)

            # Calculate lead score
            scoring_service = LeadScoringService(db)
            await scoring_service.calculate_contact_score(contact_id)

async def store_validation_results(contact_id: int, results: Dict):
    """Store validation results in database"""
    async for db in get_db():
        for platform, result in results.items():
            validation = PlatformValidation(
                contact_id=contact_id,
                phone_e164=result["phone_e164"],
                platform=platform,
                is_valid=result["is_valid"],
                is_business=result.get("is_business", False),
                confidence_score=result["confidence_score"],
                platform_details=result.get("platform_details", {}),
                validation_method=result.get("validation_method"),
                response_time_ms=result.get("response_time_ms")
            )

            db.add(validation)

        await db.commit()
```

### 🌆 **DÍA 6-7 TARDE: Testing e Integración Dashboard**

#### ✅ **BLOQUE 7: Actualizar Dashboard para Validaciones (3 horas)**

**Tarea 7.1: Expandir tipos TypeScript**

```typescript
// WebDashboard/src/types/Validation.ts - EXPANDIR
export interface PlatformValidation {
  id: string;
  contactId: string;
  phoneE164: string;
  platform: "whatsapp" | "instagram" | "facebook" | "google" | "apple";
  isValid: boolean;
  isBusiness: boolean;
  isPremium: boolean;
  confidenceScore: number;
  platformDetails: Record<string, any>;
  validationMethod: string;
  responseTimeMs: number;
  validatedAt: string;
  expiresAt: string;
}

export interface LeadScore {
  id: string;
  contactId: string;
  phoneE164: string;
  whatsappScore: number;
  instagramScore: number;
  facebookScore: number;
  googleScore: number;
  appleScore: number;
  totalScore: number;
  qualityTier: "PREMIUM" | "HIGH" | "MEDIUM" | "LOW" | "POOR" | "UNKNOWN";
  confidenceLevel: number;
  platformCount: number;
  businessAccountCount: number;
  lastCalculatedAt: string;
}

export interface ContactWithValidations extends Contact {
  whatsappValidated?: boolean;
  instagramValidated?: boolean;
  facebookValidated?: boolean;
  googleValidated?: boolean;
  appleValidated?: boolean;
  leadScore?: number;
  leadTier?: string;
  platformValidations?: PlatformValidation[];
  leadScoreRecord?: LeadScore;
}
```

**Tarea 7.2: Componente de validación en ContactCard**

```typescript
// WebDashboard/src/components/contacts/ValidationStatus.tsx - NUEVO
import React from "react";
import {
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
} from "@heroicons/react/24/outline";

interface ValidationStatusProps {
  contact: ContactWithValidations;
}

export const ValidationStatus: React.FC<ValidationStatusProps> = ({
  contact,
}) => {
  const platforms = [
    { name: "WhatsApp", key: "whatsappValidated", color: "green" },
    { name: "Instagram", key: "instagramValidated", color: "purple" },
    { name: "Facebook", key: "facebookValidated", color: "blue" },
    { name: "Google", key: "googleValidated", color: "red" },
    { name: "Apple", key: "appleValidated", color: "gray" },
  ];

  const getStatusIcon = (validated?: boolean) => {
    if (validated === true) {
      return <CheckCircleIcon className="h-4 w-4 text-green-500" />;
    } else if (validated === false) {
      return <XCircleIcon className="h-4 w-4 text-red-500" />;
    } else {
      return <ClockIcon className="h-4 w-4 text-gray-400" />;
    }
  };

  const getScoreColor = (score?: number) => {
    if (!score) return "text-gray-500";
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    if (score >= 40) return "text-orange-600";
    return "text-red-600";
  };

  return (
    <div className="space-y-3">
      {/* Lead Score */}
      {contact.leadScore && (
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Lead Score</span>
          <div className="flex items-center">
            <span
              className={`text-lg font-bold ${getScoreColor(
                contact.leadScore
              )}`}
            >
              {contact.leadScore}
            </span>
            <span className="text-sm text-gray-500 ml-1">/100</span>
            {contact.leadTier && (
              <span
                className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${
                  contact.leadTier === "PREMIUM"
                    ? "bg-purple-100 text-purple-800"
                    : contact.leadTier === "HIGH"
                    ? "bg-green-100 text-green-800"
                    : contact.leadTier === "MEDIUM"
                    ? "bg-yellow-100 text-yellow-800"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                {contact.leadTier}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Platform Validations */}
      <div>
        <span className="text-sm font-medium text-gray-700 block mb-2">
          Platform Status
        </span>
        <div className="grid grid-cols-2 gap-2">
          {platforms.slice(0, 4).map((platform) => (
            <div key={platform.key} className="flex items-center text-sm">
              {getStatusIcon(
                contact[platform.key as keyof ContactWithValidations] as boolean
              )}
              <span className="ml-2 text-gray-600">{platform.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
```

---

## 🎯 CRITERIOS DE ACEPTACIÓN

### **✅ Al Final del Día 5:**

- [ ] WhatsApp Validator funcionando con 3 métodos
- [ ] Proxy management operativo
- [ ] Rate limiting implementado
- [ ] Cache de resultados funcionando
- [ ] Health checks y métricas

### **✅ Al Final del Día 6:**

- [ ] Instagram Validator operativo
- [ ] Validation Orchestrator funcionando
- [ ] Integración con backend principal
- [ ] Background tasks para validación
- [ ] API endpoints expandidos

### **✅ Al Final del Día 7:**

- [ ] Dashboard mostrando validaciones
- [ ] Componentes de validación en UI
- [ ] Testing de integración completo
- [ ] Performance optimizada
- [ ] Sistema híbrido funcionando

---

## 🚨 TROUBLESHOOTING

### **Problema: Rate limiting de plataformas**

- **Solución:** Implementar backoff exponencial y proxy rotation
- **Monitor:** Métricas de success rate por método
- **Fallback:** Múltiples métodos de validación

### **Problema: Validadores no responden**

- **Solución:** Health checks y circuit breakers
- **Timeout:** Configurar timeouts apropiados
- **Retry:** Logic de retry con límites

### **Problema: Performance con gran volumen**

- **Solución:** Batch processing y queue management
- **Scale:** Múltiples instancias de validadores
- **Cache:** Aggressive caching de resultados

---

## 📊 MÉTRICAS DE PROGRESO

- **WhatsApp Validator:** 35% del total
- **Instagram Validator:** 30% del total
- **Validation Orchestrator:** 20% del total
- **Dashboard Integration:** 15% del total

**Total Fase 3:** 100% → **Preparado para Fase 4**

---

## 🚀 RESULTADO ESPERADO

### **Al Completar Fase 3:**

- ✅ **Validadores core funcionando** (WhatsApp + Instagram)
- ✅ **Orquestación inteligente** de validaciones
- ✅ **Integración con 31.8M contactos** existentes
- ✅ **Dashboard expandido** con validaciones
- ✅ **Performance escalable** para gran volumen

### **🎉 Capacidades Nuevas:**

- **Validación automática** de números WhatsApp
- **Detección de cuentas** Instagram asociadas
- **Enriquecimiento de datos** en tiempo real
- **Base preparada** para lead scoring

**→ Continuar con [Fase 4: Lead Scoring](./fase4-lead-scoring.md)**

---

_Fase 3: Validadores Core_
_SMS Marketing Platform v2.0 - Migración Sistema Actual_
_Implementación Detallada_
