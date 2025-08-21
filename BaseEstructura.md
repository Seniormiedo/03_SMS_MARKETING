# Base de Datos SMS Marketing - Estructura Completa

## 📊 Resumen Ejecutivo

**Base de Datos:** `sms_marketing`  
**Motor:** PostgreSQL 16  
**Usuario:** `sms_user`  
**Total de Tablas:** 20  
**Registros Principales:** 31.8M contactos, 177K rangos IFT, 25 números de validación  

---

## 🏗️ Arquitectura General

### Tablas Principales (Core Business)
- **`contacts`** - 31.8M registros - Contactos principales del sistema
- **`campaigns`** - Campañas SMS con configuración y métricas
- **`messages`** - Mensajes individuales enviados
- **`ift_rangos`** - 177K rangos oficiales IFT para clasificación
- **`validation_numbers`** - 25 números hardcodeados para validación

### Tablas de Referencia
- **`ladas_reference`** - Mapeo LADA → Estado/Municipio
- **`mejores_ladas`** - LADAs optimizadas para campañas

### Tablas de Respaldo y Auditoría
- **`contacts_backup_*`** - Múltiples respaldos de contactos
- **`contacts_changes_*`** - Registro de cambios masivos
- **`contacts_ift_changes`** - Cambios específicos por IFT
- **`update_checkpoints`** - Puntos de control para actualizaciones

### Tablas de Migración/Staging
- **`csv_raw`** / **`csv_staging`** - Datos en proceso de migración
- **`raw_telcel_data`** / **`telcel_data`** - Datos originales Telcel
- **`alembic_version`** - Control de versiones de esquema

---

## 📋 Estructura Detallada por Tabla

### 1. CONTACTS (Tabla Principal)
**Registros:** 31,833,272  
**Verificados:** 31,800,377  
**No Móviles:** 3,192  
**Disponibles:** 31,803,569  

#### Campos Principales
```sql
-- Identificación
id                  INTEGER PRIMARY KEY
phone_e164          VARCHAR(15) UNIQUE NOT NULL  -- +52xxxxxxxxxx
phone_national      VARCHAR(12) NOT NULL         -- xxxxxxxxxx
phone_original      VARCHAR(20)

-- Información Personal
full_name           VARCHAR(255)
address             TEXT
neighborhood        VARCHAR(100)

-- Información Geográfica
lada                VARCHAR(3)           -- Código de área
state_code          VARCHAR(5)           -- CDMX, JAL, etc.
state_name          VARCHAR(50)          -- Nombre completo del estado
municipality        VARCHAR(100)         -- Municipio/Delegación
city                VARCHAR(100)         -- Ciudad

-- Información Técnica
is_mobile           BOOLEAN DEFAULT TRUE
operator            VARCHAR(50)          -- Telcel, Telmex, etc.

-- Estado y Gestión
status              CONTACTSTATUS DEFAULT 'UNKNOWN'
status_updated_at   TIMESTAMP WITH TIME ZONE
status_source       VARCHAR(50)

-- Seguimiento de Uso
send_count          INTEGER DEFAULT 0
last_sent_at        TIMESTAMP WITH TIME ZONE
opt_out_at          TIMESTAMP WITH TIME ZONE
opt_out_method      VARCHAR(20)

-- Validación
last_validated_at   TIMESTAMP WITH TIME ZONE
validation_attempts INTEGER DEFAULT 0

-- Metadatos
source              VARCHAR(50) DEFAULT 'TELCEL2022'
import_batch_id     VARCHAR(50)
created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
```

#### Índices Críticos
- **`contacts_phone_e164_key`** - UNIQUE para evitar duplicados
- **`idx_contacts_premium_extraction`** - Optimizado para extracciones premium
- **`idx_contacts_location_extraction`** - Optimizado para extracciones por ubicación
- **`idx_contacts_active_mobile`** - Contactos activos y móviles

#### Restricciones
- **`check_phone_e164_format`** - Formato +52[0-9]{10}
- **`check_phone_national_format`** - Formato [0-9]{10}
- **`check_send_count_positive`** - send_count >= 0
- **`check_validation_attempts_positive`** - validation_attempts >= 0

---

### 2. IFT_RANGOS (Clasificación Oficial)
**Registros:** 177,422  
**CPP (Móviles):** 103,493  
**MPP (Fijos):** 11,351  
**FIJO:** 62,578  

#### Estructura
```sql
id               INTEGER PRIMARY KEY
numero_inicial   BIGINT NOT NULL      -- Inicio del rango
numero_final     BIGINT NOT NULL      -- Fin del rango
cantidad_numeros INTEGER NOT NULL     -- Cantidad en el rango
tipo_servicio    VARCHAR(10) NOT NULL -- CPP, MPP, FIJO
operador         TEXT NOT NULL        -- Operador asignado
fecha_asignacion DATE                 -- Fecha de asignación IFT
created_at       TIMESTAMP DEFAULT NOW()
```

#### Función Asociada
```sql
verificar_numero_ift(numero_telefono BIGINT)
RETURNS TABLE (
    es_movil BOOLEAN,
    operador_ift VARCHAR,
    tipo_servicio VARCHAR,
    fecha_asignacion DATE,
    encontrado BOOLEAN
)
```

**Lógica de Clasificación:**
- **CPP** → `es_movil = TRUE` (Móviles)
- **MPP/FIJO** → `es_movil = FALSE` (Fijos)

---

### 3. VALIDATION_NUMBERS (Sistema de Validación)
**Registros:** 25  
**Activos:** 25  
**Uso Promedio:** 0  
**Uso Máximo:** 1  

#### Estructura
```sql
id                      INTEGER PRIMARY KEY
phone_number            VARCHAR(15) UNIQUE NOT NULL
description             VARCHAR(100) DEFAULT 'Número de validación de campañas SMS'
is_active               BOOLEAN DEFAULT TRUE
created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
last_used               TIMESTAMP
usage_count             INTEGER DEFAULT 0

-- Campos Calculados Automáticamente
lada                    VARCHAR(3) GENERATED ALWAYS AS (substring(phone_number, 1, 3)) STORED
state_validation        VARCHAR(20) DEFAULT 'VALIDACION'
municipality_validation VARCHAR(20) DEFAULT 'VALIDACION'
```

#### Propósito
- **1 número por cada 1000 contactos** extraídos
- **Posición aleatoria** dentro de cada bloque de 1000
- **Identificación:** `state_name = 'VALIDACION'`
- **Monitoreo** de recepción de campañas SMS

---

### 4. CAMPAIGNS (Gestión de Campañas)

#### Estructura Principal
```sql
id                      INTEGER PRIMARY KEY
name                    VARCHAR(255) NOT NULL
description             TEXT
message_template        TEXT NOT NULL

-- Segmentación
target_states           VARCHAR(5)[]     -- Estados objetivo
target_ladas            VARCHAR(3)[]     -- LADAs objetivo  
target_cities           VARCHAR(100)[]   -- Ciudades objetivo
target_operators        VARCHAR(50)[]    -- Operadores objetivo

-- Configuración
min_last_contact_days   INTEGER          -- Días mínimos desde último contacto
max_send_count          INTEGER          -- Máximo envíos por contacto
exclude_recent_contacts INTEGER DEFAULT 30
max_recipients          INTEGER          -- Máximo destinatarios
send_rate_per_minute    INTEGER DEFAULT 100
priority                INTEGER DEFAULT 5 -- 1-10

-- Estado y Programación
status                  CAMPAIGNSTATUS DEFAULT 'DRAFT'
scheduled_at            TIMESTAMP WITH TIME ZONE
started_at              TIMESTAMP WITH TIME ZONE
completed_at            TIMESTAMP WITH TIME ZONE

-- Métricas
estimated_recipients    INTEGER DEFAULT 0
sent_count              INTEGER DEFAULT 0
delivered_count         INTEGER DEFAULT 0
failed_count            INTEGER DEFAULT 0

-- Costos
estimated_cost_usd      INTEGER
actual_cost_usd         INTEGER DEFAULT 0

-- Aprobación y Cumplimiento
approved_by             VARCHAR(100)
approved_at             TIMESTAMP WITH TIME ZONE
compliance_checked      VARCHAR(50)

-- Control de Errores
error_message           TEXT
retry_count             INTEGER DEFAULT 0
```

---

### 5. MESSAGES (Mensajes Individuales)

#### Estructura Principal
```sql
id                INTEGER PRIMARY KEY
campaign_id       INTEGER REFERENCES campaigns(id)
contact_id        INTEGER REFERENCES contacts(id)
phone_e164        VARCHAR(15) NOT NULL

-- Contenido
message_content   TEXT NOT NULL
message_length    INTEGER DEFAULT 0
sms_parts         INTEGER DEFAULT 1

-- Proveedor
provider          VARCHAR(50)
external_id       VARCHAR(100)
provider_response TEXT

-- Estado
status            MESSAGESTATUS DEFAULT 'QUEUED'
delivery_status   DELIVERYSTATUS DEFAULT 'PENDING'
error_code        VARCHAR(20)
error_message     TEXT
retry_count       INTEGER DEFAULT 0

-- Timestamps
queued_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW()
sent_at           TIMESTAMP WITH TIME ZONE
delivered_at      TIMESTAMP WITH TIME ZONE
failed_at         TIMESTAMP WITH TIME ZONE

-- Costos y Routing
cost_usd          NUMERIC(10,6)
cost_currency     VARCHAR(3) DEFAULT 'USD'
priority          INTEGER DEFAULT 5
route_id          VARCHAR(50)

-- Análisis
opt_out_detected  VARCHAR(20)
spam_score        NUMERIC(3,2)
```

---

### 6. LADAS_REFERENCE (Referencia Geográfica)

#### Estructura
```sql
lada       VARCHAR(3) PRIMARY KEY
estado     VARCHAR(50) NOT NULL
municipio  VARCHAR(100) NOT NULL
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### Propósito
- **Mapeo oficial** LADA → Estado/Municipio
- **Normalización** de datos geográficos
- **Actualización masiva** de contactos sin ubicación

---

## 🔧 Tipos de Datos Personalizados (ENUMs)

### CONTACTSTATUS
```sql
'ACTIVE', 'VERIFIED', 'INACTIVE', 'DISCONNECTED', 'SUSPENDED', 
'UNKNOWN', 'PENDING_VALIDATION', 'OPTED_OUT', 'BLOCKED', 
'BLACKLISTED', 'INVALID_FORMAT', 'NOT_MOBILE', 'CARRIER_ERROR'
```

### CAMPAIGNSTATUS
```sql
'DRAFT', 'SCHEDULED', 'RUNNING', 'PAUSED', 'COMPLETED', 'CANCELLED', 'FAILED'
```

### MESSAGESTATUS
```sql
'QUEUED', 'SENDING', 'SENT', 'DELIVERED', 'FAILED', 'REJECTED', 'EXPIRED', 'CANCELLED'
```

### DELIVERYSTATUS
```sql
'PENDING', 'DELIVERED', 'FAILED', 'UNDELIVERED', 'REJECTED', 'UNKNOWN'
```

---

## 📈 Estadísticas de Rendimiento

### Distribución de Contactos por Estado
- **VERIFIED:** 31,800,377 (99.9%)
- **NOT_MOBILE:** 3,192 (0.01%)
- **Disponibles (sin opt-out):** 31,803,569

### Distribución IFT por Tipo de Servicio
- **CPP (Móviles):** 103,493 (58.3%)
- **FIJO:** 62,578 (35.3%)
- **MPP:** 11,351 (6.4%)

### Índices Críticos para Rendimiento
1. **Extracciones Premium:** `idx_contacts_premium_extraction`
2. **Extracciones por Ubicación:** `idx_contacts_location_extraction`
3. **Contactos Activos:** `idx_contacts_active_mobile`
4. **Búsqueda por Teléfono:** `idx_contacts_phone_e164`
5. **Rangos IFT:** `idx_ift_rangos_rango`

---

## 🔒 Integridad y Restricciones

### Claves Foráneas
- **messages.campaign_id** → campaigns.id (ON DELETE SET NULL)
- **messages.contact_id** → contacts.id (ON DELETE CASCADE)

### Triggers Automáticos
- **update_contacts_updated_at** - Actualiza `updated_at` en contactos
- **update_campaigns_updated_at** - Actualiza `updated_at` en campañas
- **update_messages_updated_at** - Actualiza `updated_at` en mensajes

### Validaciones de Negocio
- **Formatos de teléfono** validados por regex
- **Rangos IFT** con validación numero_final >= numero_inicial
- **Contadores positivos** en todas las métricas
- **Prioridades** en rango 1-10

---

## 🚀 Funcionalidades Avanzadas

### Sistema de Validación Automática
- **25 números hardcodeados** para monitoreo
- **Inyección automática** 1 por cada 1000 contactos
- **Posicionamiento aleatorio** dentro de bloques
- **Tracking de uso** con estadísticas

### Clasificación IFT Automática
- **Función verificar_numero_ift()** para clasificación en tiempo real
- **177K rangos oficiales** actualizados
- **Lógica CPP/MPP/FIJO** implementada

### Optimizaciones de Consulta
- **Índices especializados** para cada tipo de extracción
- **Índices compuestos** para filtros complejos
- **Índices condicionales** para casos específicos

---

## 📊 Métricas de Capacidad

### Volumen de Datos
- **Contactos:** 31.8M registros (~8GB)
- **Rangos IFT:** 177K registros (~50MB)
- **Espacio total estimado:** ~10GB

### Rendimiento Esperado
- **Extracciones simples:** < 2 segundos
- **Extracciones complejas:** < 10 segundos
- **Actualizaciones masivas:** 1M registros/minuto

### Límites Operacionales
- **Extracción máxima:** 10,000 contactos/solicitud
- **Extracciones diarias:** 50,000 contactos/día
- **Extracciones por hora:** 20 solicitudes/hora

---

## 🔧 Mantenimiento y Monitoreo

### Tablas de Respaldo Activas
- `contacts_backup_monitored`
- `contacts_backup_pre_ift`
- `contacts_backup_simple_safe`
- `contacts_backup_ultra_safe`

### Registro de Cambios
- `contacts_changes_simple`
- `contacts_changes_ultra_safe`
- `contacts_ift_changes`

### Puntos de Control
- `update_checkpoints` - Para actualizaciones masivas seguras

---

## 📝 Notas Técnicas

### Configuración PostgreSQL
- **listen_addresses = '*'** - Para conexiones Docker
- **Extensiones:** pg_trgm para búsquedas de texto

### Consideraciones de Seguridad
- **Validación de grupo Telegram** implementada
- **Logging de accesos no autorizados**
- **Restricciones de extracción** por usuario/hora/día

### Próximas Mejoras
- [ ] Particionado de tabla `messages` por fecha
- [ ] Índices adicionales para analytics
- [ ] Compresión de datos históricos
- [ ] Réplicas de solo lectura para reportes

---

*Documento generado automáticamente el 2025-01-13*  
*Base de datos: sms_marketing v2.1*  
*Contactos activos: 31.8M*
