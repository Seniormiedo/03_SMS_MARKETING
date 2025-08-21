# 🚀 SMS Marketing Platform v2.0

**Enterprise SMS Marketing Platform with Multi-Platform Lead Validation and AI-Powered Optimization**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 Descripción

Plataforma enterprise de marketing SMS con capacidades avanzadas de validación multi-plataforma, scoring inteligente de leads y automatización completa de campañas. Integra validación en tiempo real para WhatsApp, Instagram, Facebook, Google y Apple.

### 🎯 Características Principales

- **🤖 Validación Multi-Plataforma:** WhatsApp, Instagram, Facebook, Google, Apple
- **🧠 Scoring Inteligente:** Sistema de puntuación 0-100 con Machine Learning
- **📊 Dashboard Web:** Interfaz moderna con React + TypeScript
- **🔄 Automatización:** Campañas auto-optimizadas con A/B testing
- **📈 Analytics Predictivos:** Forecasting y ROI prediction
- **🌐 Escalabilidad Enterprise:** Kubernetes, multi-tenancy, global load balancing

---

## 🏗️ Arquitectura

### **Estructura del Proyecto:**

```
SmsMarketingPlatform/
├── 📁 Core/                           # Núcleo del sistema (Clean Architecture)
│   ├── 📁 Domain/                     # Entidades y reglas de negocio
│   ├── 📁 Application/                # Casos de uso y servicios
│   ├── 📁 Infrastructure/             # Implementaciones concretas
│   └── 📁 Shared/                     # Utilidades compartidas
├── 📁 Services/                       # Microservicios
│   ├── 📁 ApiGateway/                # Gateway principal (FastAPI)
│   ├── 📁 ContactManagement/         # Gestión de contactos
│   ├── 📁 LeadScoring/               # Sistema de scoring con ML
│   ├── 📁 ValidationOrchestrator/    # Orquestador de validaciones
│   └── 📁 PlatformValidators/        # Validadores por plataforma
├── 📁 WebDashboard/                   # Frontend React + TypeScript
├── 📁 Infrastructure/                 # DevOps y configuraciones
├── 📁 Tests/                          # Tests organizados por tipo
└── 📁 Documentation/                  # Documentación técnica
```

### **Microservicios:**

- **API Gateway** (Puerto 8080) - Punto de entrada único
- **Contact Management** (Puerto 8001) - Gestión de 31.8M contactos
- **Lead Scoring** (Puerto 8002) - IA para scoring de leads
- **WhatsApp Validator** (Puerto 8011) - Validación WhatsApp
- **Instagram Validator** (Puerto 8012) - Validación Instagram
- **Facebook Validator** (Puerto 8013) - Validación Facebook
- **Google Validator** (Puerto 8014) - Validación Google
- **Apple Validator** (Puerto 8015) - Validación Apple

---

## 🚀 Instalación Rápida

### **Prerrequisitos:**

- Python 3.11+
- Docker & Docker Compose
- Node.js 18+ (para el dashboard)
- PostgreSQL 16+
- Redis 7+

### **1. Clonar y Configurar:**

```bash
git clone <repository-url>
cd SmsMarketingPlatform

# Copiar configuración de ejemplo
cp .env.example .env

# Editar variables de entorno
nano .env
```

### **2. Instalación con Docker (Recomendado):**

```bash
# Levantar toda la infraestructura
docker-compose up -d

# Verificar servicios
docker-compose ps

# Ver logs
docker-compose logs -f api-gateway
```

### **3. Instalación Manual:**

```bash
# Instalar dependencias Python
pip install -e ".[dev]"

# Instalar dependencias del dashboard
cd WebDashboard
npm install
npm run build

# Configurar base de datos
alembic upgrade head

# Ejecutar servicios
uvicorn Services.ApiGateway.main:app --host 0.0.0.0 --port 8080
```

---

## 📊 Base de Datos

### **Estadísticas Actuales:**

- **31.8M contactos** verificados y listos
- **177K rangos IFT** para clasificación móvil/fijo
- **25 números de validación** hardcodeados
- **20 tablas** optimizadas con índices especializados

### **Tablas Principales:**

- `contacts` - Contactos principales (31.8M registros)
- `campaigns` - Campañas SMS con métricas
- `messages` - Mensajes individuales enviados
- `lead_scores` - Puntuaciones de calidad por lead
- `platform_validations` - Resultados de validación por plataforma
- `validation_jobs` - Jobs de validación en lote

---

## 🔧 Configuración

### **Variables de Entorno (.env):**

```env
# Base de Datos
DATABASE_URL=postgresql://sms_user:password@localhost:5432/sms_marketing
REDIS_URL=redis://localhost:6379/0
MONGODB_URL=mongodb://localhost:27017/validations

# API Keys
TELEGRAM_BOT_TOKEN=your_bot_token
WHATSAPP_API_KEY=your_whatsapp_key
INSTAGRAM_API_KEY=your_instagram_key

# Configuración de Servicios
ENVIRONMENT=production
LOG_LEVEL=INFO
MAX_WORKERS=4
RATE_LIMIT_PER_MINUTE=1000

# Scoring Configuration
WHATSAPP_WEIGHT=25
FACEBOOK_WEIGHT=20
INSTAGRAM_WEIGHT=20
GOOGLE_WEIGHT=20
APPLE_WEIGHT=15
```

---

## 🎮 Uso

### **Dashboard Web:**

```bash
# Acceder al dashboard
http://localhost:3000

# Login con credenciales configuradas
# Navegar por contactos, campañas y analytics
```

### **API REST:**

```bash
# Documentación interactiva
http://localhost:8080/docs

# Ejemplo: Extraer contactos
curl -X POST "http://localhost:8080/api/v1/contacts/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1000,
    "location": "CDMX",
    "export_format": "xlsx"
  }'

# Ejemplo: Validar leads
curl -X POST "http://localhost:8080/api/v1/validation/validate-batch" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_numbers": ["+525551234567", "+525559876543"],
    "platforms": ["whatsapp", "instagram", "facebook"]
  }'
```

### **Bot de Telegram:**

```
/start - Iniciar bot
/extract 1000 CDMX xlsx - Extraer contactos
/validate +525551234567 - Validar número
/stats - Ver estadísticas
/help - Ayuda completa
```

---

## 🧪 Testing

### **Ejecutar Tests:**

```bash
# Tests unitarios
pytest Tests/Unit/ -v

# Tests de integración
pytest Tests/Integration/ -v

# Tests E2E
pytest Tests/E2E/ -v

# Cobertura completa
pytest --cov=Core --cov=Services --cov-report=html

# Tests específicos
pytest Tests/Unit/test_contact_service.py -v
```

### **Linting y Formateo:**

```bash
# Formatear código
black Core/ Services/

# Linting
ruff check Core/ Services/

# Type checking
mypy Core/ Services/

# Security check
bandit -r Core/ Services/
```

---

## 📈 Monitoreo

### **Métricas Disponibles:**

- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3001
- **Flower (Celery):** http://localhost:5555
- **Health Checks:** http://localhost:8080/health

### **Logs Estructurados:**

```bash
# Ver logs en tiempo real
docker-compose logs -f api-gateway

# Logs específicos por servicio
docker-compose logs contact-management
docker-compose logs lead-scoring

# Logs de validadores
docker-compose logs whatsapp-validator
```

---

## 🚀 Deployment

### **Desarrollo:**

```bash
docker-compose -f docker-compose.dev.yml up -d
```

### **Producción:**

```bash
# Con Kubernetes
kubectl apply -f Infrastructure/Kubernetes/

# Con Docker Swarm
docker stack deploy -c docker-compose.prod.yml sms-platform
```

### **Escalamiento:**

```bash
# Escalar validadores
docker-compose up -d --scale whatsapp-validator=3
docker-compose up -d --scale instagram-validator=2

# Auto-scaling con Kubernetes
kubectl autoscale deployment whatsapp-validator --cpu-percent=70 --min=2 --max=10
```

---

## 📚 Documentación

### **Enlaces Útiles:**

- [Arquitectura Detallada](Documentation/Architecture/README.md)
- [API Reference](Documentation/API/README.md)
- [Guía de Deployment](Documentation/Deployment/README.md)
- [Troubleshooting](Documentation/Troubleshooting.md)

### **Ejemplos de Código:**

- [Crear Validador Personalizado](Documentation/Examples/custom-validator.md)
- [Integrar Nueva Plataforma](Documentation/Examples/new-platform.md)
- [Configurar ML Models](Documentation/Examples/ml-setup.md)

---

## 🤝 Contribución

### **Flujo de Desarrollo:**

1. Fork del repositorio
2. Crear branch: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -am 'Add nueva funcionalidad'`
4. Push branch: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

### **Estándares de Código:**

- **Python:** PEP 8, type hints obligatorios
- **TypeScript:** Strict mode, ESLint + Prettier
- **Tests:** Cobertura mínima 90%
- **Documentación:** Docstrings en formato Google

---

## 📊 Roadmap

### **Fase 1 (Completada):** Fundación y Arquitectura

- ✅ Reestructuración profesional del proyecto
- ✅ Clean Architecture implementada
- ✅ Base de datos optimizada (31.8M contactos)
- ✅ Sistema de scoring básico

### **Fase 2 (En Desarrollo):** Microservicios y Validación

- 🔄 Implementación de 5 validadores de plataforma
- 🔄 Dashboard web con React + TypeScript
- 🔄 Sistema de scoring avanzado con ML
- 🔄 API Gateway con rate limiting

### **Fase 3 (Planeada):** IA y Enterprise

- 📋 Machine Learning avanzado
- 📋 Automatización completa de campañas
- 📋 Kubernetes deployment
- 📋 Multi-tenancy y escalabilidad global

---

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

---

## 👥 Equipo

- **Arquitecto Principal:** Sistema de validación multi-plataforma
- **DevOps Engineer:** Infraestructura y deployment
- **ML Engineer:** Modelos de scoring y predicción
- **Frontend Developer:** Dashboard React + TypeScript
- **QA Engineer:** Testing y calidad de código

---

## 📞 Soporte

- **Issues:** [GitHub Issues](https://github.com/your-repo/issues)
- **Documentación:** [Wiki](https://github.com/your-repo/wiki)
- **Email:** dev@smsmarketing.com

---

_SMS Marketing Platform v2.0 - Transformando el marketing SMS con IA y validación multi-plataforma_
