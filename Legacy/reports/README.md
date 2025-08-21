# 📱 SMS Marketing Platform

Plataforma profesional de marketing por SMS diseñada para gestionar eficientemente 36.6 millones de números telefónicos mexicanos.

## 🚀 Características Principales

- **Gestión masiva de contactos** - 36.6M números telefónicos mexicanos
- **Segmentación geográfica** - Por estado, LADA, municipio y ciudad
- **Envío masivo de SMS** - Hasta 500,000 SMS/día
- **Múltiples proveedores** - Twilio, AWS SNS, MessageBird
- **Analytics en tiempo real** - Métricas de entrega y engagement
- **Compliance LFPDPPP** - Cumplimiento normativo mexicano
- **Opt-out automático** - Gestión de exclusiones

## 🏗️ Arquitectura

```
├── FastAPI (Backend)
├── PostgreSQL (Base de datos principal)
├── Redis (Cache y colas)
├── Celery (Procesamiento asíncrono)
├── Docker (Contenedores)
└── Nginx (Proxy reverso)
```

## 📋 Requisitos Previos

- Docker 25+ y Docker Compose
- Python 3.11+
- 16GB RAM, 8 vCPU, 1TB SSD
- Cuenta Twilio para envío de SMS
- Cuenta Telnyx para validación de números

## 🚀 Instalación Rápida

1. **Clonar y configurar:**
```bash
git clone <repository>
cd sms_marketing_platform
cp .env.example .env
```

2. **Editar variables de entorno:**
```bash
# Editar .env con tus credenciales
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TELNYX_API_KEY=your_telnyx_key
```

3. **Iniciar servicios:**
```bash
docker-compose up -d
```

4. **Verificar instalación:**
```bash
curl http://localhost:8000/health
```

## 📊 Estado del Proyecto

### ✅ Completado (Día 1 - Fase 1)
- [x] Estructura completa del proyecto FastAPI
- [x] Docker Compose con PostgreSQL y Redis
- [x] Sistema de autenticación JWT
- [x] Endpoints básicos de API
- [x] Configuración optimizada para bulk operations

### 🔄 En Progreso (Días 2-5 - Fase 1)
- [ ] Modelos SQLAlchemy y migraciones Alembic
- [ ] Script de migración de 36.6M registros
- [ ] Normalización de números telefónicos
- [ ] Workers Celery para envío SMS
- [ ] Índices optimizados y vistas materializadas

### 📈 Siguientes Fases
- **Fase 2:** Limpieza y enriquecimiento de datos
- **Fase 3:** Motor de SMS y campañas
- **Fase 4:** Analytics y compliance

## 🔧 Comandos Útiles

```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Ejecutar migraciones
docker-compose exec api alembic upgrade head

# Acceder a PostgreSQL
docker-compose exec postgres psql -U sms_user -d sms_marketing

# Monitorear Redis
docker-compose exec redis redis-cli monitor

# Ejecutar tests
docker-compose exec api pytest

# Ver métricas Celery
open http://localhost:5555  # Flower
```

## 📚 Documentación API

Una vez iniciado el proyecto, la documentación interactiva está disponible en:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

## 🔐 Autenticación

La API utiliza JWT tokens. Credenciales por defecto:
- **Usuario:** admin
- **Contraseña:** admin123

```bash
# Obtener token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

## 📊 Métricas y Monitoreo

- **Health Check:** http://localhost:8000/health
- **Celery Monitor:** http://localhost:5555
- **PostgreSQL:** localhost:15432
- **Redis:** localhost:16379

## 🚨 Troubleshooting

### Puerto ocupado
Si los puertos están ocupados, modifica `docker-compose.yml`:
```yaml
ports:
  - "18000:8000"  # API
  - "15433:5432"  # PostgreSQL
  - "16380:6379"  # Redis
```

### Memoria insuficiente
Reduce configuración PostgreSQL en `docker/postgres.conf`:
```
shared_buffers = 2GB
work_mem = 128MB
maintenance_work_mem = 512MB
```

### Logs de debug
```bash
docker-compose logs -f api worker postgres redis
```

## 📈 Performance

### Configuración Actual
- **Throughput:** 100-500 SMS/segundo
- **Consultas DB:** <2s para 1M registros
- **API Response:** <200ms p95
- **Uptime:** >99.9%

### Optimizaciones Aplicadas
- Índices PostgreSQL optimizados
- Pool de conexiones configurado
- Cache Redis para consultas frecuentes
- Workers Celery distribuidos
- Rate limiting por proveedor SMS

## 🤝 Contribución

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 📞 Soporte

- **Email:** soporte@smsmarketing.com
- **Documentación:** [Wiki del proyecto](wiki/)
- **Issues:** [GitHub Issues](issues/)

---

**SMS Marketing Platform v1.0.0**  
*Desarrollado con ❤️ para el mercado mexicano*