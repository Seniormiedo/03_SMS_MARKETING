# 🚀 FASE 1 DETALLADA - Infraestructura Base
## SMS Marketing Platform - Semana 1 (5 días)

**Objetivo:** Establecer base tecnológica completa y migrar 36.6M números de SQLite a PostgreSQL  
**Duración:** 5 días laborales  
**Prerequisitos:** Servidor con 16GB RAM, 8 vCPU, 1TB SSD

---

## 📅 DÍA 1: Setup Inicial del Proyecto

### 🎯 Objetivo del Día
Crear la estructura base del proyecto FastAPI con Docker y configuración inicial.

### ⏰ Cronograma Detallado

#### **09:00 - 10:30 | Tarea 1.1: Estructura del Proyecto**
**Duración:** 1.5 horas  
**Responsable:** Desarrollador principal

**Subtareas:**
- [ ] **1.1.1** Crear estructura de directorios completa
- [ ] **1.1.2** Inicializar repositorio Git con .gitignore
- [ ] **1.1.3** Crear archivos base de configuración
- [ ] **1.1.4** Setup inicial de requirements.txt

**Entregables:**
```
sms_marketing_platform/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py
│   │           ├── contacts.py
│   │           ├── campaigns.py
│   │           └── health.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── deps.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── contact.py
│   │   ├── campaign.py
│   │   └── message.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── contact.py
│   │   ├── campaign.py
│   │   └── message.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── contact_service.py
│   │   ├── sms_service.py
│   │   └── campaign_service.py
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   └── sms_worker.py
│   └── utils/
│       ├── __init__.py
│       ├── phone_utils.py
│       └── geo_utils.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   ├── test_services/
│   └── test_workers/
├── scripts/
│   ├── migrate_data.py
│   ├── clean_numbers.py
│   └── setup_db.py
├── docker/
│   ├── Dockerfile
│   ├── Dockerfile.worker
│   └── nginx.conf
├── migrations/
│   └── versions/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
├── alembic.ini
└── README.md
```

#### **10:30 - 12:00 | Tarea 1.2: Configuración Docker**
**Duración:** 1.5 horas

**Subtareas:**
- [ ] **1.2.1** Crear Dockerfile principal para FastAPI
- [ ] **1.2.2** Crear Dockerfile para workers Celery
- [ ] **1.2.3** Configurar docker-compose.yml completo
- [ ] **1.2.4** Setup de variables de entorno

**Entregables:**
- `Dockerfile` optimizado para producción
- `docker-compose.yml` con todos los servicios
- `.env.example` con todas las variables necesarias

#### **13:00 - 15:00 | Tarea 1.3: FastAPI Base**
**Duración:** 2 horas

**Subtareas:**
- [ ] **1.3.1** Configurar aplicación FastAPI principal
- [ ] **1.3.2** Setup de middleware (CORS, logging, security)
- [ ] **1.3.3** Configurar rutas base y health check
- [ ] **1.3.4** Setup de documentación automática

**Entregables:**
- Aplicación FastAPI funcional
- Endpoint `/health` operativo
- Documentación Swagger en `/docs`

#### **15:00 - 17:00 | Tarea 1.4: Configuración de Seguridad**
**Duración:** 2 horas

**Subtareas:**
- [ ] **1.4.1** Implementar autenticación JWT
- [ ] **1.4.2** Configurar hash de passwords
- [ ] **1.4.3** Setup de roles y permisos básicos
- [ ] **1.4.4** Configurar variables de entorno seguras

**Entregables:**
- Sistema de autenticación JWT funcional
- Endpoint `/auth/login` operativo
- Middleware de autenticación configurado

---

## 📅 DÍA 2: Configuración de Base de Datos

### 🎯 Objetivo del Día
Configurar PostgreSQL, Redis y sistema de migraciones Alembic.

### ⏰ Cronograma Detallado

#### **09:00 - 10:30 | Tarea 2.1: Setup PostgreSQL**
**Duración:** 1.5 horas

**Subtareas:**
- [ ] **2.1.1** Configurar PostgreSQL en docker-compose
- [ ] **2.1.2** Crear configuración de conexión en FastAPI
- [ ] **2.1.3** Setup de SQLAlchemy con async support
- [ ] **2.1.4** Configurar pool de conexiones optimizado

**Configuración PostgreSQL:**
```yaml
# docker-compose.yml
postgres:
  image: postgres:16-alpine
  environment:
    POSTGRES_DB: sms_marketing
    POSTGRES_USER: sms_user
    POSTGRES_PASSWORD: ${DB_PASSWORD}
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./docker/postgres.conf:/etc/postgresql/postgresql.conf
  ports:
    - "5432:5432"
  command: postgres -c config_file=/etc/postgresql/postgresql.conf
```

#### **10:30 - 12:00 | Tarea 2.2: Setup Redis**
**Duración:** 1.5 horas

**Subtareas:**
- [ ] **2.2.1** Configurar Redis en docker-compose
- [ ] **2.2.2** Setup de conexión Redis en FastAPI
- [ ] **2.2.3** Configurar Redis para cache y sesiones
- [ ] **2.2.4** Setup Redis para colas Celery

**Configuración Redis:**
```yaml
# docker-compose.yml
redis:
  image: redis:7-alpine
  volumes:
    - redis_data:/data
    - ./docker/redis.conf:/usr/local/etc/redis/redis.conf
  ports:
    - "6379:6379"
  command: redis-server /usr/local/etc/redis/redis.conf
```

#### **13:00 - 15:30 | Tarea 2.3: Configuración Alembic**
**Duración:** 2.5 horas

**Subtareas:**
- [ ] **2.3.1** Inicializar Alembic en el proyecto
- [ ] **2.3.2** Configurar alembic.ini con variables de entorno
- [ ] **2.3.3** Crear script de inicialización de DB
- [ ] **2.3.4** Setup de modelos base SQLAlchemy

**Entregables:**
- Alembic configurado y funcional
- Script `setup_db.py` para inicialización
- Modelos base creados

#### **15:30 - 17:00 | Tarea 2.4: Modelos de Datos Iniciales**
**Duración:** 1.5 horas

**Subtareas:**
- [ ] **2.4.1** Crear modelo Contact (tabla contacts)
- [ ] **2.4.2** Crear modelo Campaign (tabla campaigns)
- [ ] **2.4.3** Crear modelo Message (tabla messages)
- [ ] **2.4.4** Definir relaciones entre modelos

**Entregables:**
- Modelos SQLAlchemy completos
- Primera migración generada
- Base de datos inicializada

---

## 📅 DÍA 3: Script de Migración de Datos

### 🎯 Objetivo del Día
Crear y probar script de migración desde SQLite a PostgreSQL.

### ⏰ Cronograma Detallado

#### **09:00 - 11:00 | Tarea 3.1: Análisis de Datos Origen**
**Duración:** 2 horas

**Subtareas:**
- [ ] **3.1.1** Analizar estructura detallada de numeros.db
- [ ] **3.1.2** Mapear campos SQLite → PostgreSQL
- [ ] **3.1.3** Identificar transformaciones necesarias
- [ ] **3.1.4** Definir estrategia de migración por lotes

**Mapeo de Campos:**
```python
# SQLite → PostgreSQL mapping
FIELD_MAPPING = {
    'numero': 'phone_national',
    'campo1_original': 'phone_original',
    'nombre': 'full_name',
    'direccion': 'address',
    'colonia': 'neighborhood',
    'municipio_cof': 'municipality',
    'estado_cof': 'state_code',
    'lada': 'lada',
    'ciudad_por_lada': 'city',
    'es_valido': 'is_valid',
    'fecha_migracion': 'migrated_at'
}
```

#### **11:00 - 13:00 | Tarea 3.2: Script de Migración Base**
**Duración:** 2 horas

**Subtareas:**
- [ ] **3.2.1** Crear clase MigrationManager
- [ ] **3.2.2** Implementar lectura por lotes de SQLite
- [ ] **3.2.3** Implementar escritura por lotes a PostgreSQL
- [ ] **3.2.4** Agregar logging y progress tracking

**Estructura del Script:**
```python
class MigrationManager:
    def __init__(self, sqlite_path, postgres_url, batch_size=10000):
        self.sqlite_path = sqlite_path
        self.postgres_url = postgres_url
        self.batch_size = batch_size
        
    async def migrate_contacts(self):
        """Migra tabla numeros → contacts"""
        
    async def migrate_statistics(self):
        """Migra estadísticas de migración"""
        
    async def migrate_missing_ladas(self):
        """Migra LADAs faltantes"""
```

#### **14:00 - 16:00 | Tarea 3.3: Normalización de Números**
**Duración:** 2 horas

**Subtareas:**
- [ ] **3.3.1** Integrar librería phonenumbers
- [ ] **3.3.2** Implementar normalización a E.164
- [ ] **3.3.3** Validación de números mexicanos
- [ ] **3.3.4** Detección automática móvil vs fijo

**Función de Normalización:**
```python
import phonenumbers
from phonenumbers import carrier, geocoder

def normalize_mexican_number(number_str: str) -> dict:
    """
    Normaliza número mexicano y extrae metadatos
    """
    try:
        # Parse con región México
        parsed = phonenumbers.parse(number_str, "MX")
        
        return {
            'phone_e164': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
            'phone_national': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
            'is_valid': phonenumbers.is_valid_number(parsed),
            'is_mobile': phonenumbers.number_type(parsed) == phonenumbers.PhoneNumberType.MOBILE,
            'carrier': carrier.name_for_number(parsed, "es"),
            'location': geocoder.description_for_number(parsed, "es")
        }
    except Exception as e:
        return {'error': str(e)}
```

#### **16:00 - 17:00 | Tarea 3.4: Testing de Migración**
**Duración:** 1 hora

**Subtareas:**
- [ ] **3.4.1** Crear tests unitarios para normalización
- [ ] **3.4.2** Test de migración con muestra pequeña (1000 registros)
- [ ] **3.4.3** Validar integridad de datos migrados
- [ ] **3.4.4** Benchmark de performance

---

## 📅 DÍA 4: Ejecución de Migración Masiva

### 🎯 Objetivo del Día
Ejecutar migración completa de 36.6M registros con monitoreo.

### ⏰ Cronograma Detallado

#### **09:00 - 10:00 | Tarea 4.1: Preparación Pre-Migración**
**Duración:** 1 hora

**Subtareas:**
- [ ] **4.1.1** Backup completo de numeros.db original
- [ ] **4.1.2** Optimizar configuración PostgreSQL para bulk insert
- [ ] **4.1.3** Preparar scripts de monitoreo
- [ ] **4.1.4** Configurar logging detallado

**Optimizaciones PostgreSQL:**
```sql
-- Configuraciones para bulk insert masivo
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET work_mem = '256MB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET checkpoint_segments = 64;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET synchronous_commit = off;
SELECT pg_reload_conf();
```

#### **10:00 - 12:00 | Tarea 4.2: Migración Fase 1 - Datos Base**
**Duración:** 2 horas

**Subtareas:**
- [ ] **4.2.1** Migrar primeros 10M registros (lote de prueba)
- [ ] **4.2.2** Validar calidad de datos migrados
- [ ] **4.2.3** Ajustar parámetros según performance
- [ ] **4.2.4** Documentar métricas de migración

**Script de Monitoreo:**
```python
async def monitor_migration_progress():
    """Monitorea progreso de migración en tiempo real"""
    while migration_active:
        stats = await get_migration_stats()
        print(f"""
        Progreso: {stats.processed:,}/{stats.total:,} ({stats.percentage:.1f}%)
        Velocidad: {stats.records_per_second:,} registros/seg
        Tiempo restante: {stats.eta}
        Errores: {stats.errors}
        """)
        await asyncio.sleep(30)
```

#### **13:00 - 15:00 | Tarea 4.3: Migración Fase 2 - Datos Completos**
**Duración:** 2 horas (inicio del proceso completo)

**Subtareas:**
- [ ] **4.3.1** Lanzar migración completa (36.6M registros)
- [ ] **4.3.2** Monitoreo continuo de progreso
- [ ] **4.3.3** Manejo de errores y reintentos
- [ ] **4.3.4** Backup incremental cada 5M registros

**Tiempo Estimado Total:** 6-8 horas para migración completa

#### **15:00 - 17:00 | Tarea 4.4: Validación Post-Migración**
**Duración:** 2 horas

**Subtareas:**
- [ ] **4.4.1** Validar count total de registros
- [ ] **4.4.2** Verificar integridad referencial
- [ ] **4.4.3** Validar muestreo aleatorio de datos
- [ ] **4.4.4** Generar reporte de calidad de migración

**Queries de Validación:**
```sql
-- Validaciones post-migración
SELECT COUNT(*) as total_contacts FROM contacts;
SELECT COUNT(*) as valid_phones FROM contacts WHERE is_valid = true;
SELECT state_code, COUNT(*) FROM contacts GROUP BY state_code ORDER BY COUNT(*) DESC;
SELECT lada, COUNT(*) FROM contacts GROUP BY lada ORDER BY COUNT(*) DESC LIMIT 20;
```

---

## 📅 DÍA 5: Optimización e Indexación

### 🎯 Objetivo del Día
Optimizar base de datos migrada y crear índices para consultas masivas.

### ⏰ Cronograma Detallado

#### **09:00 - 10:30 | Tarea 5.1: Creación de Índices**
**Duración:** 1.5 horas

**Subtareas:**
- [ ] **5.1.1** Crear índices primarios (phone_e164, id)
- [ ] **5.1.2** Crear índices de segmentación (state, lada, city)
- [ ] **5.1.3** Crear índices de campaña (last_sent, opt_out)
- [ ] **5.1.4** Crear índices compuestos optimizados

**Índices Críticos:**
```sql
-- Índices para consultas de segmentación masiva
CREATE INDEX CONCURRENTLY idx_contacts_state_active ON contacts(state_code, status) WHERE opt_out_at IS NULL;
CREATE INDEX CONCURRENTLY idx_contacts_lada_active ON contacts(lada, status) WHERE opt_out_at IS NULL;
CREATE INDEX CONCURRENTLY idx_contacts_city_active ON contacts(city, status) WHERE opt_out_at IS NULL;
CREATE INDEX CONCURRENTLY idx_contacts_last_sent ON contacts(last_sent_at) WHERE last_sent_at IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_contacts_send_count ON contacts(send_count);

-- Índices para búsquedas de texto
CREATE INDEX CONCURRENTLY idx_contacts_name_gin ON contacts USING gin(to_tsvector('spanish', full_name));
CREATE INDEX CONCURRENTLY idx_contacts_address_gin ON contacts USING gin(to_tsvector('spanish', address));
```

#### **10:30 - 12:00 | Tarea 5.2: Optimización de Consultas**
**Duración:** 1.5 horas

**Subtareas:**
- [ ] **5.2.1** Crear vistas materializadas para segmentación
- [ ] **5.2.2** Optimizar queries de campañas masivas
- [ ] **5.2.3** Implementar particionado por estado (opcional)
- [ ] **5.2.4** Configurar estadísticas automáticas

**Vistas Materializadas:**
```sql
-- Vista para números activos por estado
CREATE MATERIALIZED VIEW contacts_by_state AS
SELECT 
    state_code,
    state_name,
    COUNT(*) as total_contacts,
    COUNT(*) FILTER (WHERE status = 'ACTIVE') as active_contacts,
    COUNT(*) FILTER (WHERE is_mobile = true) as mobile_contacts,
    COUNT(*) FILTER (WHERE last_sent_at > NOW() - INTERVAL '30 days') as recently_contacted
FROM contacts 
WHERE opt_out_at IS NULL 
GROUP BY state_code, state_name;

CREATE UNIQUE INDEX ON contacts_by_state(state_code);
```

#### **13:00 - 14:30 | Tarea 5.3: Testing de Performance**
**Duración:** 1.5 horas

**Subtareas:**
- [ ] **5.3.1** Benchmark queries de segmentación
- [ ] **5.3.2** Test de consultas de campaña (100K, 500K, 1M registros)
- [ ] **5.3.3** Validar performance de inserción de mensajes
- [ ] **5.3.4** Optimizar configuración PostgreSQL final

**Benchmarks Objetivo:**
```python
# Performance targets
BENCHMARK_TARGETS = {
    'segmentation_100k': '< 500ms',      # Segmentar 100K números
    'segmentation_1m': '< 2s',           # Segmentar 1M números  
    'campaign_insert_10k': '< 1s',       # Insertar 10K mensajes
    'delivery_update_1k': '< 100ms',     # Actualizar 1K delivery status
    'contact_search': '< 200ms',         # Búsqueda por nombre/teléfono
}
```

#### **14:30 - 16:00 | Tarea 5.4: Setup de Celery Workers**
**Duración:** 1.5 horas

**Subtareas:**
- [ ] **5.4.1** Configurar Celery con Redis backend
- [ ] **5.4.2** Crear workers para envío de SMS
- [ ] **5.4.3** Setup de colas prioritarias
- [ ] **5.4.4** Configurar monitoreo Flower

**Configuración Celery:**
```python
# celery_config.py
from celery import Celery

celery_app = Celery(
    "sms_marketing",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=["app.workers.sms_worker"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Mexico_City",
    enable_utc=True,
    task_routes={
        "app.workers.sms_worker.send_sms": {"queue": "sms_queue"},
        "app.workers.sms_worker.send_bulk_sms": {"queue": "bulk_queue"},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
```

#### **16:00 - 17:00 | Tarea 5.5: Validación Final de Fase 1**
**Duración:** 1 hora

**Subtareas:**
- [ ] **5.5.1** Ejecutar suite completa de tests
- [ ] **5.5.2** Validar todos los endpoints API
- [ ] **5.5.3** Verificar funcionalidad de workers
- [ ] **5.5.4** Generar reporte de Fase 1 completada

---

## 📊 Métricas de Éxito - Fase 1

### 🎯 KPIs Técnicos
- [ ] **Migración completa:** 36,645,692 registros migrados
- [ ] **Calidad de datos:** >99% números válidos mantenidos
- [ ] **Performance DB:** Consultas <2s para 1M registros
- [ ] **API Response:** <200ms p95 para endpoints básicos
- [ ] **Uptime:** 100% durante migración

### 📈 Métricas de Calidad
- [ ] **Números E.164:** 100% normalizados correctamente
- [ ] **Deduplicación:** 0 duplicados en base final
- [ ] **Índices:** Todos los índices críticos creados
- [ ] **Backups:** Backup completo post-migración

### 🔧 Entregables Técnicos
- [ ] **Infraestructura:** Docker Compose funcional
- [ ] **Base de datos:** PostgreSQL optimizada con 36.6M registros
- [ ] **API:** FastAPI con autenticación JWT
- [ ] **Workers:** Celery configurado y operativo
- [ ] **Monitoreo:** Logs y métricas básicas

---

## ⚠️ Riesgos y Contingencias

### 🚨 Riesgos Críticos
| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Falla en migración masiva | Media | Alto | Backup + migración por lotes de 1M |
| Memoria insuficiente | Alta | Medio | Optimizar batch_size + swap |
| Corrupción de datos | Baja | Crítico | Validación continua + rollback |

### 🔄 Plan de Rollback
1. **Parar todos los servicios** (API + Workers + DB)
2. **Restaurar backup** de numeros.db original
3. **Revertir configuración** a estado inicial
4. **Reiniciar análisis** de causa raíz

**Tiempo de rollback:** 30 minutos máximo

---

## 📋 Checklist Final - Fase 1

### ✅ Día 1 - Setup Inicial
- [ ] Estructura de proyecto creada
- [ ] Docker Compose configurado
- [ ] FastAPI base funcionando
- [ ] Autenticación JWT implementada

### ✅ Día 2 - Base de Datos
- [ ] PostgreSQL configurado y optimizado
- [ ] Redis funcionando para cache y colas
- [ ] Alembic configurado con migraciones
- [ ] Modelos SQLAlchemy creados

### ✅ Día 3 - Script de Migración
- [ ] Script de migración desarrollado
- [ ] Normalización de números implementada
- [ ] Tests de migración pasando
- [ ] Benchmark de performance validado

### ✅ Día 4 - Migración Masiva
- [ ] 36.6M registros migrados exitosamente
- [ ] Validación de integridad completada
- [ ] Backup post-migración realizado
- [ ] Reporte de calidad generado

### ✅ Día 5 - Optimización
- [ ] Índices críticos creados
- [ ] Vistas materializadas implementadas
- [ ] Performance benchmarks aprobados
- [ ] Celery workers operativos

---

## 🚀 Preparación para Fase 2

### 📝 Entregables para Fase 2
- [ ] **Base de datos optimizada** con 36.6M contactos
- [ ] **API endpoints básicos** funcionando
- [ ] **Sistema de workers** preparado para SMS
- [ ] **Documentación técnica** actualizada

### 🎯 Siguientes Pasos
1. **Fase 2:** Limpieza y enriquecimiento de datos
2. **Integración Telnyx** para validación de números activos
3. **Segmentación geográfica** avanzada
4. **Preparación para envío** masivo de SMS

---

*Fase 1 Detallada - SMS Marketing Platform*  
*Versión: 1.0 | Fecha: 2025-01-27*