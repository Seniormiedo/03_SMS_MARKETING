# 🤖 PLAN DE IMPLEMENTACIÓN - BOT EXTRACTOR DE CONTACTOS SMS

## 📋 **ANÁLISIS DE REQUERIMIENTOS**

### **🎯 Funcionalidades Principales:**
1. **Extracción por cantidad y calidad:**
   - `/get [100-10000] premium [xlsx|txt]` - Mejores LADAs
   - `/get [100-10000] [estado] [xlsx|txt]` - Por estado específico  
   - `/get [100-10000] [ciudad] [xlsx|txt]` - Por ciudad específica

2. **Formatos de exportación:**
   - **XLSX:** Columnas "Number" (12 dígitos) y "Content" (ciudad)
   - **TXT:** Lista simple de números (12 dígitos), uno por línea

3. **Control de uso:**
   - Marcar contactos como `OPTED_OUT` después de extracción
   - Prevenir duplicados en extracciones futuras

4. **Rangos soportados:**
   - Mínimo: 100 contactos
   - Máximo: 10,000 contactos

---

## 🏗️ **ARQUITECTURA PROFESIONAL**

### **📁 Estructura del Proyecto:**
```
📁 bot/
├── 📄 .env                     # Configuración específica del bot
├── 📄 requirements.txt         # Dependencias del bot
├── 📄 main.py                  # Punto de entrada principal
├── 📄 config.py               # Configuración y variables
├── 📁 core/
│   ├── 📄 __init__.py
│   ├── 📄 database.py         # Conexión y queries a PostgreSQL
│   ├── 📄 bot_handler.py      # Lógica principal del bot
│   └── 📄 validators.py       # Validaciones de comandos
├── 📁 services/
│   ├── 📄 __init__.py
│   ├── 📄 contact_service.py  # Servicio de extracción de contactos
│   ├── 📄 export_service.py   # Servicio de exportación XLSX/TXT
│   └── 📄 location_service.py # Servicio de validación geográfica
├── 📁 models/
│   ├── 📄 __init__.py
│   ├── 📄 contact.py          # Modelo de contacto
│   └── 📄 extraction.py       # Modelo de extracción
├── 📁 utils/
│   ├── 📄 __init__.py
│   ├── 📄 formatters.py       # Formateo de números y datos
│   └── 📄 logger.py           # Sistema de logging
├── 📁 exports/                # Carpeta para archivos generados
└── 📁 logs/                   # Carpeta para logs del bot
```

---

## 🔧 **COMPONENTES TÉCNICOS DETALLADOS**

### **1. 🗂️ Base de Datos (database.py)**
```python
class DatabaseManager:
    """Gestor de conexión a PostgreSQL optimizado"""
    
    # Métodos principales:
    - get_premium_contacts(limit: int) -> List[Contact]
    - get_contacts_by_state(state: str, limit: int) -> List[Contact]  
    - get_contacts_by_city(city: str, limit: int) -> List[Contact]
    - mark_contacts_as_opted_out(contact_ids: List[int]) -> bool
    - get_available_states() -> List[str]
    - get_available_cities() -> List[str]
    - validate_premium_availability(limit: int) -> bool
```

### **2. 🤖 Bot Handler (bot_handler.py)**
```python
class ContactBotHandler:
    """Manejador principal de comandos del bot"""
    
    # Comandos soportados:
    - handle_get_premium(amount: int, format: str) -> str
    - handle_get_by_state(amount: int, state: str, format: str) -> str
    - handle_get_by_city(amount: int, city: str, format: str) -> str
    - handle_help() -> str
    - handle_stats() -> str
```

### **3. 📊 Servicio de Contactos (contact_service.py)**
```python
class ContactService:
    """Lógica de negocio para extracción de contactos"""
    
    # Funcionalidades:
    - extract_premium_contacts(limit: int) -> ExtractionResult
    - extract_by_location(location: str, limit: int) -> ExtractionResult
    - validate_extraction_request(params: dict) -> ValidationResult
    - process_extraction(extraction: ExtractionRequest) -> ExtractionResult
```

### **4. 📤 Servicio de Exportación (export_service.py)**
```python
class ExportService:
    """Generación de archivos XLSX y TXT"""
    
    # Métodos:
    - export_to_xlsx(contacts: List[Contact], filename: str) -> str
    - export_to_txt(contacts: List[Contact], filename: str) -> str
    - format_phone_number(phone: str) -> str  # A 12 dígitos
    - generate_unique_filename(prefix: str, extension: str) -> str
```

### **5. 🌍 Servicio de Ubicación (location_service.py)**
```python
class LocationService:
    """Validación y normalización geográfica"""
    
    # Funcionalidades:
    - validate_state_name(state: str) -> str
    - validate_city_name(city: str) -> str
    - get_premium_states() -> List[str]  # Top 10 estados
    - normalize_location_input(input: str) -> str
```

---

## 📝 **ESPECIFICACIÓN DE COMANDOS**

### **🎯 Comando Premium:**
```
/get [cantidad] premium [formato]

Ejemplos:
- /get 1000 premium xlsx
- /get 500 premium txt
- /get 2500 premium xlsx

Lógica:
1. Validar cantidad (100-10000)
2. Consultar mejores_ladas para obtener top estados
3. Extraer contactos VERIFIED de esos estados
4. Marcar como OPTED_OUT
5. Generar archivo en formato solicitado
```

### **🏛️ Comando por Estado:**
```
/get [cantidad] [estado] [formato]

Ejemplos:
- /get 1000 Sinaloa xlsx
- /get 500 "Nuevo León" txt
- /get 100 Coahuila xlsx

Lógica:
1. Validar estado existe en BD
2. Normalizar nombre (ej: "nuevo leon" → "Nuevo León")
3. Extraer contactos VERIFIED del estado
4. Marcar como OPTED_OUT
5. Generar archivo
```

### **🏙️ Comando por Ciudad:**
```
/get [cantidad] [ciudad] [formato]

Ejemplos:
- /get 100 Culiacán txt
- /get 1000 Monterrey xlsx
- /get 500 Guadalajara txt

Lógica:
1. Validar ciudad existe en BD
2. Normalizar nombre de ciudad
3. Extraer contactos VERIFIED de la ciudad
4. Marcar como OPTED_OUT
5. Generar archivo
```

---

## 🗄️ **QUERIES SQL OPTIMIZADAS**

### **1. 📊 Extracción Premium:**
```sql
-- Contactos de mejores estados (basado en mejores_ladas)
WITH premium_states AS (
    SELECT DISTINCT estado 
    FROM mejores_ladas 
    ORDER BY icpth_2022 DESC 
    LIMIT 10
),
available_contacts AS (
    SELECT c.id, c.phone_national, c.city, c.state_name
    FROM contacts c
    JOIN premium_states ps ON c.state_name = ps.estado
    WHERE c.status = 'VERIFIED' 
      AND c.opt_out_at IS NULL
    ORDER BY RANDOM()
    LIMIT ?
)
SELECT * FROM available_contacts;
```

### **2. 🏛️ Extracción por Estado:**
```sql
-- Contactos por estado específico
SELECT id, phone_national, city, state_name
FROM contacts 
WHERE state_name ILIKE ? 
  AND status = 'VERIFIED'
  AND opt_out_at IS NULL
ORDER BY RANDOM()
LIMIT ?;
```

### **3. 🏙️ Extracción por Ciudad:**
```sql
-- Contactos por ciudad específica
SELECT id, phone_national, city, state_name
FROM contacts 
WHERE city ILIKE ? 
  AND status = 'VERIFIED'
  AND opt_out_at IS NULL
ORDER BY RANDOM()
LIMIT ?;
```

### **4. ✅ Marcado como OPTED_OUT:**
```sql
-- Actualizar estado de contactos extraídos
UPDATE contacts 
SET status = 'OPTED_OUT',
    opt_out_at = NOW(),
    opt_out_method = 'BOT_EXTRACTION',
    updated_at = NOW()
WHERE id = ANY(?);
```

---

## 📊 **FORMATO DE ARCHIVOS**

### **📋 Archivo XLSX:**
```
| Column A: Number    | Column B: Content  |
|--------------------|--------------------|
| 526674355781       | GUADALAJARA        |
| 526679827455       | CUAUHTEMOC         |
| 526672382990       | CUAUHTEMOC         |
| 526671305264       | MONTERREY          |
| 526678474107       | CUAUHTEMOC         |
```

### **📄 Archivo TXT:**
```
526674355781
526679827455
526672382990
526671305264
526678474107
```

---

## ⚙️ **CONFIGURACIÓN (.env)**

### **🔧 Variables del Bot:**
```env
# Configuración de Base de Datos
BOT_DB_HOST=localhost
BOT_DB_PORT=5432
BOT_DB_NAME=sms_marketing
BOT_DB_USER=sms_user
BOT_DB_PASSWORD=sms_password

# Configuración del Bot
BOT_NAME=ContactExtractorBot
BOT_VERSION=1.0.0
BOT_LOG_LEVEL=INFO

# Límites de Extracción
MIN_EXTRACTION_AMOUNT=100
MAX_EXTRACTION_AMOUNT=10000
MAX_DAILY_EXTRACTIONS=50000

# Configuración de Archivos
EXPORT_PATH=./exports/
LOG_PATH=./logs/
FILE_RETENTION_DAYS=7

# Configuración de Seguridad
REQUIRE_CONFIRMATION=true
ENABLE_AUDIT_LOG=true
```

---

## 🔐 **VALIDACIONES Y SEGURIDAD**

### **✅ Validaciones de Entrada:**
1. **Cantidad:** Entre 100 y 10,000
2. **Formato:** Solo 'xlsx' o 'txt'
3. **Estado/Ciudad:** Existe en base de datos
4. **Disponibilidad:** Suficientes contactos VERIFIED

### **🛡️ Controles de Seguridad:**
1. **Rate Limiting:** Máximo 10 extracciones por hora
2. **Audit Log:** Registro de todas las extracciones
3. **Confirmación:** Requiere confirmación para extracciones >5000
4. **Cleanup:** Eliminación automática de archivos después de 7 días

### **📊 Validación de Disponibilidad:**
```python
def validate_availability(location: str, amount: int) -> ValidationResult:
    """Valida si hay suficientes contactos disponibles"""
    available = count_available_contacts(location)
    if available < amount:
        return ValidationResult(
            valid=False,
            message=f"Solo hay {available} contactos disponibles en {location}"
        )
    return ValidationResult(valid=True)
```

---

## 📈 **SISTEMA DE LOGGING Y MÉTRICAS**

### **📋 Logs de Auditoría:**
```
[2025-08-06 10:30:15] INFO: Extraction requested - Amount: 1000, Type: premium, Format: xlsx
[2025-08-06 10:30:16] INFO: Contacts extracted - IDs: [1,2,3...], Location: Premium States
[2025-08-06 10:30:17] INFO: File generated - Path: exports/premium_1000_20250806_103017.xlsx
[2025-08-06 10:30:18] INFO: Contacts marked as OPTED_OUT - Count: 1000
```

### **📊 Métricas Tracked:**
- Total extracciones por día/semana/mes
- Distribución por tipo (premium/estado/ciudad)
- Formatos más utilizados (xlsx vs txt)
- Estados/ciudades más solicitados
- Contactos totales extraídos

---

## 🚀 **COMANDOS ADICIONALES ÚTILES**

### **📊 Comando de Estadísticas:**
```
/stats
- Contactos disponibles totales: 25,050,145
- Contactos premium disponibles: 5,986,228
- Estados disponibles: 32
- Ciudades disponibles: 2,847
- Extracciones hoy: 12 (8,500 contactos)
```

### **📍 Comando de Ayuda:**
```
/help
Comandos disponibles:
- /get [100-10000] premium [xlsx|txt] - Mejores LADAs
- /get [100-10000] [estado] [xlsx|txt] - Por estado
- /get [100-10000] [ciudad] [xlsx|txt] - Por ciudad
- /stats - Estadísticas del sistema
- /states - Lista de estados disponibles
- /cities [estado] - Ciudades de un estado
```

### **🗺️ Comandos de Información:**
```
/states - Lista todos los estados disponibles
/cities Sinaloa - Lista ciudades de Sinaloa
/available premium - Contactos premium disponibles
/available Sinaloa - Contactos disponibles en Sinaloa
```

---

## 🔄 **FLUJO DE PROCESAMIENTO**

### **1. 📥 Recepción de Comando:**
```
Usuario: /get 1000 premium xlsx
↓
Validador: Parsea comando y valida parámetros
↓
Handler: Identifica tipo de extracción (premium)
```

### **2. 🔍 Validación y Consulta:**
```
LocationService: Valida disponibilidad
↓
ContactService: Ejecuta query optimizada
↓
Database: Retorna contactos VERIFIED disponibles
```

### **3. 📤 Procesamiento y Exportación:**
```
ExportService: Formatea números a 12 dígitos
↓
ExportService: Genera archivo XLSX/TXT
↓
ContactService: Marca contactos como OPTED_OUT
```

### **4. ✅ Entrega y Logging:**
```
BotHandler: Entrega archivo al usuario
↓
Logger: Registra extracción en audit log
↓
Cleanup: Programa eliminación del archivo
```

---

## 🧪 **ESTRATEGIA DE TESTING**

### **✅ Tests Unitarios:**
- Validación de comandos
- Formateo de números telefónicos
- Generación de archivos XLSX/TXT
- Queries de base de datos

### **🔗 Tests de Integración:**
- Flujo completo de extracción
- Conexión a base de datos
- Generación y cleanup de archivos

### **⚡ Tests de Performance:**
- Extracción de 10,000 contactos
- Generación de archivos grandes
- Consultas concurrentes

---

## 📋 **PLAN DE IMPLEMENTACIÓN POR FASES**

### **🏗️ Fase 1: Infraestructura Base (Día 1)**
- ✅ Estructura de carpetas y archivos
- ✅ Configuración de base de datos
- ✅ Sistema de logging básico
- ✅ Validaciones de entrada

### **🔧 Fase 2: Funcionalidad Core (Día 2)**
- ✅ Servicio de extracción de contactos
- ✅ Queries SQL optimizadas
- ✅ Marcado de OPTED_OUT
- ✅ Tests unitarios básicos

### **📤 Fase 3: Sistema de Exportación (Día 3)**
- ✅ Generación de archivos XLSX
- ✅ Generación de archivos TXT
- ✅ Formateo de números telefónicos
- ✅ Sistema de cleanup automático

### **🤖 Fase 4: Bot Handler (Día 4)**
- ✅ Procesamiento de comandos
- ✅ Integración de todos los servicios
- ✅ Manejo de errores robusto
- ✅ Comandos de ayuda y estadísticas

### **🚀 Fase 5: Testing y Optimización (Día 5)**
- ✅ Tests de integración completos
- ✅ Optimización de performance
- ✅ Documentación final
- ✅ Deploy y monitoreo

---

## 💡 **CONSIDERACIONES TÉCNICAS ADICIONALES**

### **⚡ Optimizaciones de Performance:**
- Uso de índices específicos para consultas geográficas
- Paginación para extracciones grandes
- Cache de validaciones de ubicación
- Conexiones de BD con pooling

### **🔄 Manejo de Errores:**
- Rollback automático si falla la exportación
- Retry logic para conexiones de BD
- Validación de integridad de archivos
- Notificación de errores críticos

### **📊 Monitoreo y Alertas:**
- Dashboard de métricas en tiempo real
- Alertas por uso excesivo
- Monitoreo de salud de BD
- Reportes automáticos diarios

---

**🎯 RESULTADO ESPERADO:**
Un bot robusto, escalable y profesional capaz de extraer contactos de manera eficiente, con controles de seguridad, auditoría completa y formatos de exportación optimizados para campañas SMS masivas.

**⏱️ TIEMPO ESTIMADO DE IMPLEMENTACIÓN:** 5 días  
**🔧 TECNOLOGÍAS:** Python 3.11+, PostgreSQL, openpyxl, asyncio  
**📊 CAPACIDAD:** Hasta 10,000 contactos por extracción, 50,000 por día**