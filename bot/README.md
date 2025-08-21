# 🤖 Contact Extractor Bot

**Bot profesional para extracción de contactos SMS con arquitectura escalable**

## 📋 Descripción

Bot desarrollado para extraer contactos de una base de datos PostgreSQL con 36M+ registros, con funcionalidades de segmentación geográfica, control de uso y exportación en múltiples formatos.

## 🏗️ Arquitectura

### **Estructura del Proyecto:**
```
bot/
├── 📄 .env                     # Configuración específica
├── 📄 requirements.txt         # Dependencias
├── 📄 main.py                  # Punto de entrada
├── 📄 config.py               # Gestión de configuración
├── 📁 core/                   # Componentes principales
│   ├── database.py            # Conexión PostgreSQL
│   ├── bot_handler.py         # Lógica del bot
│   └── validators.py          # Validaciones
├── 📁 services/               # Servicios de negocio
│   ├── contact_service.py     # Extracción de contactos
│   ├── export_service.py      # Exportación XLSX/TXT
│   └── location_service.py    # Validación geográfica
├── 📁 models/                 # Modelos de datos
│   ├── contact.py             # Modelo de contacto
│   └── extraction.py          # Modelo de extracción
├── 📁 utils/                  # Utilidades
│   ├── formatters.py          # Formateo de datos
│   └── logger.py              # Sistema de logging
├── 📁 exports/                # Archivos generados
└── 📁 logs/                   # Logs del sistema
```

## 🚀 Instalación

### **1. Requisitos del Sistema:**
- Python 3.11+
- PostgreSQL 16+
- Base de datos `sms_marketing` configurada

### **2. Instalación de Dependencias:**
```bash
cd bot/
pip install -r requirements.txt
```

### **3. Configuración:**
Edita el archivo `.env` con tus credenciales:
```env
BOT_DB_HOST=localhost
BOT_DB_PORT=5432
BOT_DB_NAME=sms_marketing
BOT_DB_USER=tu_usuario
BOT_DB_PASSWORD=tu_password
```

## 💻 Uso

### **Modo Interactivo (Pruebas):**
```bash
python main.py --interactive
```

### **Modo Servicio:**
```bash
python main.py
```

## 🤖 Comandos Disponibles

### **📤 Extracción de Contactos:**
- `/get [100-10000] premium [xlsx|txt]` - Mejores LADAs
- `/get [100-10000] [estado] [xlsx|txt]` - Por estado específico  
- `/get [100-10000] [ciudad] [xlsx|txt]` - Por ciudad específica

### **📊 Información del Sistema:**
- `/stats` - Estadísticas del sistema
- `/states` - Lista de estados disponibles
- `/cities [estado]` - Ciudades disponibles
- `/available [premium|ubicación]` - Contactos disponibles
- `/help` - Ayuda completa

### **💡 Ejemplos:**
```
/get 1000 premium xlsx          # 1000 contactos premium en Excel
/get 500 Sinaloa txt           # 500 contactos de Sinaloa en texto
/get 2000 Guadalajara xlsx     # 2000 contactos de Guadalajara
```

## 📊 Formatos de Exportación

### **📋 Archivo XLSX:**
| Column A: Number | Column B: Content |
|------------------|-------------------|
| 526674355781     | GUADALAJARA       |
| 526679827455     | CUAUHTEMOC        |

### **📄 Archivo TXT:**
```
526674355781
526679827455
526672382990
```

## ⚙️ Configuración Avanzada

### **Límites del Sistema:**
- **Mínimo:** 100 contactos por extracción
- **Máximo:** 10,000 contactos por extracción  
- **Límite diario:** 50,000 contactos
- **Límite por hora:** 10 extracciones

### **Formatos Soportados:**
- **XLSX:** Excel con columnas Number/Content
- **TXT:** Lista simple de números (12 dígitos)

### **Control de Uso:**
- Los contactos extraídos se marcan como `OPTED_OUT`
- Prevención automática de duplicados
- Auditoría completa de todas las operaciones

## 🔧 Desarrollo

### **Estado Actual: Fase 1 - Infraestructura Base ✅**

**Componentes Completados:**
- ✅ Sistema de configuración con Pydantic
- ✅ Conexión a PostgreSQL con pooling
- ✅ Sistema de logging estructurado con auditoría
- ✅ Validaciones completas de entrada
- ✅ Modelos de datos profesionales
- ✅ Formateo y utilidades
- ✅ Punto de entrada principal

### **Próximas Fases:**
- **Fase 2:** Funcionalidad Core (extracción real)
- **Fase 3:** Sistema de Exportación (XLSX/TXT)
- **Fase 4:** Bot Handler (procesamiento completo)
- **Fase 5:** Testing y Optimización

## 📝 Logging y Auditoría

### **Logs Generados:**
- `bot_YYYYMMDD.log` - Log principal del bot
- `audit_YYYYMMDD.log` - Log de auditoría (si habilitado)

### **Eventos Tracked:**
- Solicitudes de extracción
- Extracciones completadas
- Actualizaciones de estado
- Errores y validaciones
- Métricas de performance

## 🔐 Seguridad

### **Características de Seguridad:**
- Validación exhaustiva de entrada
- Rate limiting configurable
- Auditoría completa de operaciones
- Sanitización de nombres de archivo
- Control de acceso a base de datos

### **Validaciones Implementadas:**
- Rangos de cantidad (100-10,000)
- Formatos válidos (xlsx/txt)
- Existencia de ubicaciones
- Disponibilidad de contactos
- Formato de comandos

## 🚧 Estado del Proyecto

**✅ FASE 1 COMPLETADA - Infraestructura Base**

El bot cuenta con una arquitectura profesional completa y está listo para la implementación de la funcionalidad core en la Fase 2.

**Componentes Listos:**
- Sistema de configuración profesional
- Conexión robusta a PostgreSQL  
- Logging estructurado con auditoría
- Validaciones completas
- Modelos de datos optimizados
- Utilidades de formateo
- Punto de entrada funcional

**Próximo Paso:** Implementación de extracción real de contactos y generación de archivos.

---

**📧 Contacto:** SMS Marketing Team  
**📅 Última Actualización:** Agosto 2025  
**🔖 Versión:** 1.0.0 (Fase 1)