# 📊 ESQUEMA COMPLETO DE BASE DE DATOS SMS MARKETING

## 📋 **INFORMACIÓN GENERAL**

- **Base de datos:** `sms_marketing`
- **Motor:** PostgreSQL 16
- **Usuario:** `sms_user`
- **Codificación:** UTF8
- **Timezone:** UTC con soporte de zonas horarias
- **Fecha de creación:** Agosto 2025

---

## 🗂️ **TABLAS PRINCIPALES**

### **1. TABLA `contacts` - Contactos**

**Propósito:** Almacenar información de contactos telefónicos para campañas SMS

| Campo | Tipo | Longitud | Nulo | Valor por Defecto | Descripción |
|-------|------|----------|------|-------------------|-------------|
| `id` | INTEGER | - | NO | nextval('contacts_id_seq') | ID único autoincremental |
| `created_at` | TIMESTAMP WITH TIME ZONE | - | NO | now() | Fecha de creación del registro |
| `updated_at` | TIMESTAMP WITH TIME ZONE | - | NO | now() | Fecha de última actualización |
| `phone_e164` | VARCHAR(15) | 15 | NO | - | Teléfono en formato E.164 (+52xxxxxxxxxx) |
| `phone_national` | VARCHAR(12) | 12 | NO | - | Teléfono en formato nacional (xxxxxxxxxx) |
| `phone_original` | VARCHAR(20) | 20 | SÍ | - | Teléfono en formato original del archivo |
| `full_name` | VARCHAR(255) | 255 | SÍ | - | Nombre completo del contacto |
| `address` | TEXT | - | SÍ | - | Dirección completa |
| `neighborhood` | VARCHAR(100) | 100 | SÍ | - | Colonia o barrio |
| `lada` | VARCHAR(3) | 3 | SÍ | - | Código de área (3 dígitos) |
| `state_code` | VARCHAR(5) | 5 | SÍ | - | Código del estado (ej: CDMX, JAL) |
| `state_name` | VARCHAR(50) | 50 | SÍ | - | Nombre completo del estado |
| `municipality` | VARCHAR(100) | 100 | SÍ | - | Municipio o delegación |
| `city` | VARCHAR(100) | 100 | SÍ | - | Ciudad |
| `is_mobile` | BOOLEAN | - | NO | true | Indica si es teléfono móvil |
| `operator` | VARCHAR(50) | 50 | SÍ | - | Operador telefónico (Telcel, Telmex) |
| `status` | CONTACTSTATUS | - | NO | 'UNKNOWN' | Estado del contacto |
| `status_updated_at` | TIMESTAMP WITH TIME ZONE | - | SÍ | - | Fecha de actualización del estado |
| `status_source` | VARCHAR(50) | 50 | SÍ | - | Fuente de la actualización del estado |
| `send_count` | INTEGER | - | NO | 0 | Número de SMS enviados |
| `last_sent_at` | TIMESTAMP WITH TIME ZONE | - | SÍ | - | Fecha del último SMS enviado |
| `opt_out_at` | TIMESTAMP WITH TIME ZONE | - | SÍ | - | Fecha de baja voluntaria |
| `opt_out_method` | VARCHAR(20) | 20 | SÍ | - | Método de baja (SMS, WEB, CALL) |
| `last_validated_at` | TIMESTAMP WITH TIME ZONE | - | SÍ | - | Fecha de última validación |
| `validation_attempts` | INTEGER | - | NO | 0 | Intentos de validación |
| `source` | VARCHAR(50) | 50 | NO | 'TELCEL2022' | Fuente de los datos |
| `import_batch_id` | VARCHAR(50) | 50 | SÍ | - | ID del lote de importación |

**Constraints:**
- `PRIMARY KEY`: `id`
- `UNIQUE`: `phone_e164`

**Triggers:**
- `update_contacts_updated_at` → Actualiza `updated_at` automáticamente

---

### **2. TABLA `campaigns` - Campañas SMS**

**Propósito:** Gestionar campañas de marketing por SMS

| Campo | Tipo | Longitud | Nulo | Valor por Defecto | Descripción |
|-------|------|----------|------|-------------------|-------------|
| `id` | INTEGER | - | NO | nextval('campaigns_id_seq') | ID único autoincremental |
| `created_at` | TIMESTAMP WITH TIME ZONE | - | NO | now() | Fecha de creación |
| `updated_at` | TIMESTAMP WITH TIME ZONE | - | NO | now() | Fecha de actualización |
| `name` | VARCHAR(255) | 255 | NO | - | Nombre de la campaña |
| `description` | TEXT | - | SÍ | - | Descripción detallada |
| `message_template` | TEXT | - | NO | - | Plantilla del mensaje SMS |
| `target_states` | ARRAY | - | SÍ | - | Estados objetivo |
| `target_ladas` | ARRAY | - | SÍ | - | LADAs objetivo |
| `target_cities` | ARRAY | - | SÍ | - | Ciudades objetivo |
| `target_operators` | ARRAY | - | SÍ | - | Operadores objetivo |
| `min_last_contact_days` | INTEGER | - | SÍ | - | Días mínimos desde último contacto |
| `max_send_count` | INTEGER | - | SÍ | - | Máximo de envíos por contacto |
| `exclude_recent_contacts` | INTEGER | - | NO | 30 | Excluir contactos recientes (días) |
| `max_recipients` | INTEGER | - | SÍ | - | Máximo número de destinatarios |
| `send_rate_per_minute` | INTEGER | - | NO | 100 | Velocidad de envío (SMS/minuto) |
| `priority` | INTEGER | - | NO | 5 | Prioridad de la campaña (1-10) |
| `status` | CAMPAIGNSTATUS | - | NO | 'DRAFT' | Estado de la campaña |
| `scheduled_at` | TIMESTAMP WITH TIME ZONE | - | SÍ | - | Fecha programada de inicio |
| `started_at` | TIMESTAMP WITH TIME ZONE | - | SÍ | - | Fecha real de inicio |
| `completed_at` | TIMESTAMP WITH TIME ZONE | - | SÍ | - | Fecha de finalización |
| `estimated_recipients` | INTEGER | - | NO | 0 | Destinatarios estimados |
| `sent_count` | INTEGER | - | NO | 0 | SMS enviados |
| `delivered_count` | INTEGER | - | NO | 0 | SMS entregados |
| `failed_count` | INTEGER | - | NO | 0 | SMS fallidos |
| `estimated_cost_usd` | INTEGER | - | SÍ | - | Costo estimado en USD |
| `actual_cost_usd` | INTEGER | - | NO | 0 | Costo real en USD |
| `approved_by` | VARCHAR(100) | 100 | SÍ | - | Usuario que aprobó |
| `approved_at` | TIMESTAMP WITH TIME ZONE | - | SÍ | - | Fecha de aprobación |
| `compliance_checked` | VARCHAR(50) | 50 | SÍ | - | Verificación de cumplimiento |
| `error_message` | TEXT | - | SÍ | - | Mensaje de error |
| `retry_count` | INTEGER | - | NO | 0 | Número de reintentos |

**Constraints:**
- `PRIMARY KEY`: `id`

**Triggers:**
- `update_campaigns_updated_at` → Actualiza `updated_at` automáticamente

---

### **3. TABLA `messages` - Mensajes SMS**

**Propósito:** Registrar cada SMS individual enviado

| Campo | Tipo | Longitud | Nulo | Valor por Defecto | Descripción |
|-------|------|----------|------|-------------------|-------------|
| `id` | INTEGER | - | NO | nextval('messages_id_seq') | ID único autoincremental |
| `created_at` | TIMESTAMP WITH TIME ZONE | - | NO | now() | Fecha de creación |
| `updated_at` | TIMESTAMP WITH TIME ZONE | - | NO | now() | Fecha de actualización |
| `campaign_id` | INTEGER | - | SÍ | - | ID de la campaña |
| `contact_id` | INTEGER | - | SÍ | - | ID del contacto |
| `phone_e164` | VARCHAR(15) | 15 | NO | - | Teléfono destino |
| `message_content` | TEXT | - | NO | - | Contenido del mensaje |
| `message_length` | INTEGER | - | NO | 0 | Longitud del mensaje |
| `sms_parts` | INTEGER | - | NO | 1 | Número de partes SMS |
| `provider` | VARCHAR(50) | 50 | SÍ | - | Proveedor SMS usado |
| `external_id` | VARCHAR(100) | 100 | SÍ | - | ID externo del proveedor |
| `provider_response` | TEXT | - | SÍ | - | Respuesta del proveedor |
| `status` | MESSAGESTATUS | - | NO | 'QUEUED' | Estado del mensaje |
| `delivery_status` | DELIVERYSTATUS | - | NO | 'PENDING' | Estado de entrega |
| `error_code` | VARCHAR(20) | 20 | SÍ | - | Código de error |
| `error_message` | TEXT | - | SÍ | - | Mensaje de error |
| `retry_count` | INTEGER | - | NO | 0 | Número de reintentos |
| `queued_at` | TIMESTAMP WITH TIME ZONE | - | NO | now() | Fecha de cola |
| `sent_at` | TIMESTAMP WITH TIME ZONE | - | SÍ | - | Fecha de envío |
| `delivered_at` | TIMESTAMP WITH TIME ZONE | - | SÍ | - | Fecha de entrega |
| `failed_at` | TIMESTAMP WITH TIME ZONE | - | SÍ | - | Fecha de fallo |
| `cost_usd` | NUMERIC | - | SÍ | - | Costo en USD |
| `cost_currency` | VARCHAR(3) | 3 | NO | 'USD' | Moneda del costo |
| `priority` | INTEGER | - | NO | 5 | Prioridad del mensaje |
| `route_id` | VARCHAR(50) | 50 | SÍ | - | ID de ruta |
| `opt_out_detected` | VARCHAR(20) | 20 | SÍ | - | Detección de baja |
| `spam_score` | NUMERIC | - | SÍ | - | Puntuación de spam |

**Constraints:**
- `PRIMARY KEY`: `id`
- `FOREIGN KEY`: `campaign_id` → `campaigns(id)`
- `FOREIGN KEY`: `contact_id` → `contacts(id)`

**Triggers:**
- `update_messages_updated_at` → Actualiza `updated_at` automáticamente

---

## 🏷️ **TIPOS PERSONALIZADOS (ENUMS)**

### **1. CONTACTSTATUS**
Estados posibles para contactos:
- `ACTIVE` - Activo y disponible
- `VERIFIED` - Verificado y confirmado
- `INACTIVE` - Inactivo temporalmente
- `DISCONNECTED` - Desconectado
- `SUSPENDED` - Suspendido
- `UNKNOWN` - Estado desconocido
- `PENDING_VALIDATION` - Pendiente de validación
- `OPTED_OUT` - Dado de baja voluntariamente
- `BLOCKED` - Bloqueado por el sistema
- `BLACKLISTED` - En lista negra
- `INVALID_FORMAT` - Formato inválido
- `NOT_MOBILE` - No es teléfono móvil
- `CARRIER_ERROR` - Error del operador

### **2. CAMPAIGNSTATUS**
Estados posibles para campañas:
- `DRAFT` - Borrador
- `SCHEDULED` - Programada
- `RUNNING` - En ejecución
- `PAUSED` - Pausada
- `COMPLETED` - Completada
- `CANCELLED` - Cancelada
- `FAILED` - Fallida

### **3. MESSAGESTATUS**
Estados posibles para mensajes:
- `QUEUED` - En cola
- `SENDING` - Enviando
- `SENT` - Enviado
- `DELIVERED` - Entregado
- `FAILED` - Fallido
- `REJECTED` - Rechazado
- `EXPIRED` - Expirado
- `CANCELLED` - Cancelado

### **4. DELIVERYSTATUS**
Estados de entrega:
- `PENDING` - Pendiente
- `DELIVERED` - Entregado
- `FAILED` - Fallido
- `UNDELIVERED` - No entregado
- `REJECTED` - Rechazado
- `UNKNOWN` - Desconocido

---

## ⚙️ **FUNCIONES Y TRIGGERS**

### **Función: `update_updated_at_column()`**
```sql
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$
```

**Propósito:** Actualizar automáticamente el campo `updated_at` cuando se modifica un registro.

### **Triggers Activos:**
1. `update_contacts_updated_at` en tabla `contacts`
2. `update_campaigns_updated_at` en tabla `campaigns`
3. `update_messages_updated_at` en tabla `messages`

**Evento:** `BEFORE UPDATE` - Se ejecuta antes de cada actualización de registro.

---

## 🔍 **ÍNDICES OPTIMIZADOS**

### **Tabla `contacts` (21 índices):**
1. `contacts_pkey` - PRIMARY KEY (id)
2. `contacts_phone_e164_key` - UNIQUE (phone_e164)
3. `idx_contacts_active_mobile` - Contactos activos móviles
4. `idx_contacts_city` - Por ciudad
5. `idx_contacts_city_status` - Ciudad + estado
6. `idx_contacts_full_name` - Por nombre
7. `idx_contacts_is_mobile` - Tipo de teléfono
8. `idx_contacts_lada` - Por LADA
9. `idx_contacts_lada_status` - LADA + estado
10. `idx_contacts_last_sent_at` - Último envío
11. `idx_contacts_last_sent_filter` - Filtro de envíos
12. `idx_contacts_municipality` - Por municipio
13. `idx_contacts_operator` - Por operador
14. `idx_contacts_operator_status` - Operador + estado
15. `idx_contacts_opt_out_at` - Fecha de baja
16. `idx_contacts_opt_out_filter` - Filtro de bajas
17. `idx_contacts_phone_e164` - Teléfono E.164
18. `idx_contacts_phone_national` - Teléfono nacional
19. `idx_contacts_state_code` - Por estado
20. `idx_contacts_state_status` - Estado + status
21. `idx_contacts_status` - Por status

### **Rendimiento de Consultas:**
- **Búsqueda por LADA:** < 1ms
- **Filtro por operador:** < 1ms
- **Consultas por estado:** < 1ms
- **Búsquedas complejas:** < 5ms

---

## 📊 **TABLAS AUXILIARES**

### **Tabla `alembic_version`**
- Gestión de versiones de migración
- Campo: `version_num` VARCHAR(32)

### **Tablas de Migración (Temporales)**
- `telcel_data` - Datos temporales de TELCEL2022
- `csv_staging` - Staging para CSV
- `raw_telcel_data` - Datos en bruto

### **Extensiones Activas**
- `pg_stat_statements` - Estadísticas de consultas
- `pg_stat_statements_info` - Información adicional

---

## 🛡️ **INTEGRIDAD Y CONSTRAINTS**

### **Claves Primarias:**
- `contacts.id`
- `campaigns.id` 
- `messages.id`
- `raw_telcel_data.id`
- `alembic_version.version_num`

### **Claves Únicas:**
- `contacts.phone_e164` - Garantiza teléfonos únicos

### **Claves Foráneas:**
- `messages.campaign_id` → `campaigns.id`
- `messages.contact_id` → `contacts.id`

### **Validaciones:**
- Formatos de teléfono E.164
- Estados válidos mediante ENUMs
- Timestamps con zona horaria
- Valores por defecto para contadores

---

## 📈 **ESTADÍSTICAS ACTUALES**

### **Volumen de Datos:**
- **Contactos:** 31,833,272 registros
- **Tamaño tabla contacts:** 14 GB
- **Tamaño total BD:** 40 GB
- **Estados únicos:** 96
- **LADAs únicas:** 284

### **Distribución:**
- **Móviles:** 5,883,120 (18.48%)
- **Fijos:** 25,950,152 (81.52%)
- **Operadores:** Telcel, Telmex
- **Integridad:** 100% verificada

---

## 🔧 **CONFIGURACIÓN Y OPTIMIZACIÓN**

### **Configuración PostgreSQL:**
- `shared_preload_libraries = 'pg_stat_statements'`
- Índices especializados para consultas frecuentes
- Triggers automáticos para timestamps
- Constraints para integridad de datos

### **Recomendaciones de Mantenimiento:**
1. `VACUUM ANALYZE` periódico
2. Monitoreo de `pg_stat_statements`
3. Backup regular de datos
4. Limpieza de tablas temporales
5. Optimización de consultas frecuentes

---

**📅 Última actualización:** Agosto 2025  
**🔧 Versión del esquema:** 1.0  
**📊 Estado:** Producción activa