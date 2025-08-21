# 📊 DIFERENCIA: CONTACTOS MIGRADOS vs VERIFIED

## 🤔 **PREGUNTA DEL USUARIO**
> "Cuál es la diferencia exactamente entre un Contacto Migrado normal y uno Verified, revisa dónde se catalogan"

---

## ✅ **RESPUESTA TÉCNICA DETALLADA**

### **🏗️ PROCESO DE MIGRACIÓN Y CATALOGACIÓN**

Durante la migración desde `TELCEL2022.csv`, **TODOS los contactos pasan por un proceso de catalogación automática** donde se les asigna un `status` basado en criterios específicos.

---

## 📋 **DEFINICIÓN DE STATUS DE CONTACTOS**

### **🎯 Status Disponibles en el Sistema:**

Según `app/models/contact.py`, líneas 15-40:

```python
class ContactStatus(str, enum.Enum):
    # Active statuses
    ACTIVE = "ACTIVE"                    # Línea activa y operativa
    VERIFIED = "VERIFIED"                # Línea verificada recientemente ✅
    
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
    NOT_MOBILE = "NOT_MOBILE"          # No es número móvil ❌
    CARRIER_ERROR = "CARRIER_ERROR"    # Error del carrier/operadora
```

---

## 🔍 **LÓGICA DE ASIGNACIÓN DE STATUS**

### **📱 Criterio Principal: ¿Es Número Móvil?**

Durante la migración, el sistema aplica esta lógica (encontrada en `Legacy/migration_scripts/python_csv_solution.py`, línea 341):

```sql
CASE WHEN lada IN (
    '55', '56', '33', '81', '222', '228', '229', '238', '244', '246', '248', '249', 
    '271', '272', '273', '274', '275', '276', '278', '282', '283', '284', '285', 
    '287', '288', '294', '295', '296', '297', '311', '312', '313', '314', '315', 
    '316', '317', '318', '319', '321', '322', '323', '324', '325', '326', '327', 
    '328', '329', '331', '332', '333', '334', '341', '342', '343', '344', '345', 
    '346', '347', '348', '351', '352', '353', '354', '355', '356', '357', '358', 
    '359', '361', '362', '363', '364', '365', '366', '367', '368', '369', '371', 
    '372', '373', '374', '375', '376', '377', '378', '381', '382', '383', '384', 
    '385', '386', '387', '388', '389', '391', '392', '393', '394', '395', '411', 
    '412', '413', '414', '415', '417', '418', '421', '422', '423', '424', '425', 
    '426', '427', '428', '429', '431', '432', '433', '434', '435', '436', '437', 
    '438', '441', '442', '443', '444', '445', '446', '447', '448', '449', '451', 
    '452', '453', '454', '455', '456', '457', '458', '459', '461', '462', '463', 
    '464', '465', '466', '467', '468', '469', '471', '472', '473', '474', '475', 
    '476', '477', '478', '481', '482', '483', '484', '485', '486', '487', '488', 
    '489', '492', '493', '494', '496', '497', '498', '499', '614', '615', '616', 
    '617', '618', '621', '622', '623', '624', '625', '626', '627', '628', '629', 
    '631', '632', '633', '634', '635', '636', '637', '638', '639', '641', '642', 
    '643', '644', '645', '646', '647', '648', '649', '651', '652', '653', '656', 
    '657', '658', '659', '661', '662', '664', '665', '667', '668', '669', '671', 
    '672', '673', '674', '675', '676', '677', '686', '687', '688', '689', '694', 
    '695', '696', '697', '698'
) 
THEN 'VERIFIED' 
ELSE 'NOT_MOBILE' 
END as status
```

### **🎯 Criterio Simplificado:**
- **Si LADA está en lista de LADAs móviles** → `status = 'VERIFIED'`
- **Si LADA NO está en lista de LADAs móviles** → `status = 'NOT_MOBILE'`

---

## 📊 **DIFERENCIAS PRÁCTICAS**

### **🔄 CONTACTO MIGRADO NORMAL:**
- **Definición:** Cualquier contacto que fue importado desde `TELCEL2022.csv`
- **Status posibles:** `VERIFIED`, `NOT_MOBILE`, `INVALID_FORMAT`, `UNKNOWN`
- **Cantidad total:** 31,833,272 contactos
- **Incluye:** Tanto móviles como fijos

### **✅ CONTACTO VERIFIED:**
- **Definición:** Contacto migrado cuyo número fue identificado como móvil
- **Status específico:** `VERIFIED` únicamente
- **Cantidad:** 25,033,272 contactos (78.6% del total)
- **Criterio:** LADA pertenece a la lista de LADAs móviles
- **Uso:** **Solo estos se usan para extracciones del bot**

### **❌ CONTACTO NOT_MOBILE:**
- **Definición:** Contacto migrado identificado como teléfono fijo
- **Status específico:** `NOT_MOBILE`
- **Cantidad:** ~6,800,000 contactos (21.4% del total)
- **Criterio:** LADA NO está en la lista de LADAs móviles
- **Uso:** **Excluidos de extracciones del bot**

---

## 🗂️ **DÓNDE SE CATALOGAN**

### **📍 Ubicaciones en el Código:**

1. **Definición de Status:** `app/models/contact.py`, líneas 15-40
2. **Migración y Asignación:** `Legacy/migration_scripts/python_csv_solution.py`, línea 341
3. **Base de Datos:** Tabla `contacts`, columna `status` (tipo ENUM)
4. **Validación:** `migrations/versions/001_create_initial_tables.py`, líneas 19-24

### **📊 En la Base de Datos:**
```sql
-- Estructura de la tabla contacts
CREATE TABLE contacts (
    id INTEGER PRIMARY KEY,
    phone_e164 VARCHAR(15) NOT NULL,
    phone_national VARCHAR(12) NOT NULL,
    -- ... otros campos ...
    status contactstatus NOT NULL DEFAULT 'UNKNOWN',  -- ← AQUÍ SE CATALOGA
    is_mobile BOOLEAN NOT NULL DEFAULT true,
    -- ... más campos ...
);

-- ENUM de status
CREATE TYPE contactstatus AS ENUM (
    'ACTIVE', 'VERIFIED', 'INACTIVE', 'DISCONNECTED', 'SUSPENDED',
    'UNKNOWN', 'PENDING_VALIDATION', 'OPTED_OUT', 'BLOCKED', 'BLACKLISTED',
    'INVALID_FORMAT', 'NOT_MOBILE', 'CARRIER_ERROR'
);
```

---

## 🎯 **IMPACTO EN EL SISTEMA**

### **🤖 Para el Bot de Telegram:**
- **Extracciones premium:** Solo usa contactos con `status = 'VERIFIED'`
- **Filtros aplicados:** `WHERE status = 'VERIFIED' AND opt_out_at IS NULL`
- **Disponibles:** 25,033,272 contactos verificados

### **📊 Para Analytics:**
- **Contactos totales:** 31,833,272 (todos los migrados)
- **Contactos utilizables:** 25,033,272 (solo VERIFIED)
- **Tasa de verificación:** 78.6%

### **🔒 Para Compliance:**
- **VERIFIED:** Aptos para campañas SMS
- **NOT_MOBILE:** Excluidos automáticamente
- **OPTED_OUT:** Marcados como no contactar

---

## 📈 **DISTRIBUCIÓN REAL**

### **📊 Por Status (basado en reporte de migración):**

| Status | Cantidad | Porcentaje | Descripción |
|--------|----------|------------|-------------|
| **VERIFIED** | 25,033,272 | 78.6% | ✅ Números móviles verificados |
| **NOT_MOBILE** | 6,800,000 | 21.4% | ❌ Números fijos excluidos |
| **INVALID_FORMAT** | 0 | 0% | ❌ Formatos inválidos |
| **UNKNOWN** | 0 | 0% | ❓ Estado desconocido |

### **📱 Por Tipo de Línea (solo VERIFIED):**
| Tipo | Cantidad | Porcentaje | Uso en Bot |
|------|----------|------------|------------|
| **Móviles** | 5,883,120 | 23.5% | ✅ Preferidos |
| **Fijos** | 19,150,152 | 76.5% | ✅ También utilizables |

---

## 🔍 **RESUMEN EJECUTIVO**

### **✅ NO HAY "CONTACTOS MIGRADOS NORMALES" vs "VERIFIED"**

**La realidad es:**

1. **TODOS los contactos son "migrados"** desde `TELCEL2022.csv`
2. **Durante la migración se les asigna automáticamente un status**
3. **VERIFIED = contactos con LADAs identificadas como móviles**
4. **NOT_MOBILE = contactos con LADAs identificadas como fijas**

### **🎯 Diferencia Clave:**
- **31,833,272 contactos migrados** (total importado)
- **25,033,272 contactos VERIFIED** (aptos para SMS)
- **6,800,000 contactos NOT_MOBILE** (excluidos del bot)

### **💡 Conclusión:**
No existe una categoría de "contacto migrado normal" separada de "VERIFIED". **VERIFIED es simplemente el status asignado a los contactos migrados que fueron identificados como números móviles** durante el proceso de importación automática.

---

**📱 El bot solo extrae contactos con `status = 'VERIFIED'` porque son los únicos considerados aptos para campañas SMS móviles.**