# 🏗️ Arquitectura del Sistema

Este documento describe los componentes, capas y flujos del Contact Extractor Bot, con referencias directas a los archivos del repositorio.

## Visión general

- **Interfaces de usuario**:
  - CLI/Servicio (`main.py`)
  - Telegram general (`core/telegram_bot.py` vía `telegram_main.py`)
  - Telegram demo (`telegram_demo.py`)
  - Telegram producción (`telegram_production.py`)
- **Núcleo (core)**: validaciones y acceso a datos
  - `core/validators.py`: parseo de comandos y reglas de negocio
  - `core/database.py`: conexión a PostgreSQL (pool sync/async) y consultas optimizadas
- **Servicios (dominio)**:
  - `services/contact_service.py`: extracción real, validación de disponibilidad, marcado `OPTED_OUT`
  - `services/export_service.py`: generación de archivos XLSX/TXT y limpieza
- **Utilidades**:
  - `utils/logger.py`: logging estructurado (structlog + rich) y auditoría
  - `utils/formatters.py`: formateo de teléfonos, nombres de archivo, utilidades
- **Modelos**:
  - `models/contact.py`: entidad de contacto
  - `models/extraction.py`: solicitud y resultado de extracción, estadísticas
- **Configuración**:
  - `config.py`: `BotConfig` con validación (Pydantic Settings), lectura `.env`

## Flujo alto nivel

1. Usuario envía comando (CLI/Telegram)
2. `core/validators.py` parsea y valida
3. `services/contact_service.py` valida disponibilidad y consulta datos mediante `core/database.py`
4. Marca contactos como `OPTED_OUT` para evitar reuso
5. `services/export_service.py` exporta resultados a XLSX/TXT
6. `utils/logger.py` registra eventos y auditoría
7. Respuesta/archivo se entrega al usuario (CLI o Telegram)

## Módulos y responsabilidades

- `config.py`
  - Variables: host, puerto, base, usuario, password; límites; paths; Telegram; logging; caching
  - Prefijo env: `BOT_`, archivo env: `.env`
- `core/database.py`
  - Pools sync/async (psycopg2/asyncpg)
  - Consultas especializadas (premium, estado, ciudad, municipio, LADA)
  - Validación de disponibilidad y listado de ubicaciones
  - Marcado `OPTED_OUT`
- `core/validators.py`
  - Comandos soportados: `/get`, `/help`, `/stats`, `/states`, `/cities`, `/available`
  - Construcción de `ExtractionRequest` y reglas de formato/límites
- `services/contact_service.py`
  - Orquesta extracción real y mide performance
  - Auditoría de extracciones (éxito/error)
- `services/export_service.py`
  - Exporta XLSX (openpyxl) y TXT, nombres de archivo, hoja Metadata, limpieza
- `utils/logger.py`
  - Log de sistema + audit trail (STARTUP, EXTRACTION_REQUEST, EXTRACTION_SUCCESS, FILE_EXPORT, VALIDATION_ERROR, RATE_LIMIT_EXCEEDED)
- `utils/formatters.py`
  - `PhoneFormatter`, `FileNameGenerator`, `DataFormatter`, `ProgressFormatter`

## Integraciones externas

- PostgreSQL 16 (psycopg2/asyncpg)
- Telegram (python-telegram-bot)

## Datos y escalabilidad

- `docs/db/` detalla esquema y 21 índices optimizados
- Volumen referencial: 31.8M+ contactos; consultas sub-milisegundo para patrones frecuentes

## Consideraciones de seguridad

- Validación estricta de input; sanitización de nombres de archivo
- Rate limiting configurable
- Auditoría de acciones

## Estado por fases

- Fase 1 (infraestructura): completa
- Fase 2 (extracción real): implementada en servicios y bot de producción
