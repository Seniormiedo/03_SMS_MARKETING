# ⚙️ Configuración y Variables de Entorno

El sistema utiliza `Pydantic Settings` con prefijo `BOT_` y archivo `.env` opcional. Las rutas de exportación y logs se crean automáticamente si no existen.

- Archivo: `config.py`
- Clase: `BotConfig`
- Prefijo: `BOT_`
- Archivo de entorno: `.env`

## Variables por categoría

### Base de Datos
- `BOT_DB_HOST` (str, default: `localhost`)
- `BOT_DB_PORT` (int, default: `5432`)
- `BOT_DB_NAME` (str, default: `sms_marketing`)
- `BOT_DB_USER` (str, default: `sms_user`)
- `BOT_DB_PASSWORD` (str, requerido)

### Bot
- `BOT_BOT_NAME` (str, default: `ContactExtractorBot`)
- `BOT_BOT_VERSION` (str, default: `1.0.0`)
- `BOT_BOT_LOG_LEVEL` (DEBUG|INFO|WARNING|ERROR|CRITICAL, default: `INFO`)
- `BOT_BOT_ENVIRONMENT` (development|staging|production, default: `development`)

### Telegram
- `BOT_TELEGRAM_BOT_TOKEN` (str, requerido)
- `BOT_TELEGRAM_BOT_USERNAME` (str, default: `RNumbeRs_bot`)
- `BOT_TELEGRAM_WEBHOOK_URL` (str, opcional)
- `BOT_TELEGRAM_WEBHOOK_SECRET` (str, opcional)
- `BOT_TELEGRAM_MAX_FILE_SIZE_MB` (int, default: `50`)

### Límites de Extracción
- `BOT_MIN_EXTRACTION_AMOUNT` (int, default: `100`)
- `BOT_MAX_EXTRACTION_AMOUNT` (int, default: `10000`)
- `BOT_MAX_DAILY_EXTRACTIONS` (int, default: `50000`)
- `BOT_MAX_HOURLY_EXTRACTIONS` (int, default: `10`)

### Archivos
- `BOT_EXPORT_PATH` (str, default: `./exports/`)
- `BOT_LOG_PATH` (str, default: `./logs/`)
- `BOT_FILE_RETENTION_DAYS` (int, default: `7`)
- `BOT_MAX_FILE_SIZE_MB` (int, default: `100`)

### Seguridad
- `BOT_REQUIRE_CONFIRMATION` (bool, default: `True`)
- `BOT_ENABLE_AUDIT_LOG` (bool, default: `True`)
- `BOT_ENABLE_RATE_LIMITING` (bool, default: `True`)

### Performance
- `BOT_DB_POOL_SIZE` (int, default: `20`)
- `BOT_DB_MAX_OVERFLOW` (int, default: `30`)
- `BOT_DB_POOL_TIMEOUT` (int, default: `30`)
- `BOT_DB_POOL_RECYCLE` (int, default: `3600`)
- `BOT_QUERY_TIMEOUT` (int, default: `60`)
- `BOT_EXTRACTION_TIMEOUT` (int, default: `300`)
- `BOT_EXPORT_BATCH_SIZE` (int, default: `5000`)

### Optimización de extracción
- `BOT_MAX_CONCURRENT_EXTRACTIONS` (int, default: `5`)
- `BOT_LARGE_EXTRACTION_THRESHOLD` (int, default: `5000`)
- `BOT_PROGRESS_UPDATE_INTERVAL` (int, default: `30`)

### Cache
- `BOT_CACHE_LOCATIONS_TTL` (int, default: `3600`)
- `BOT_CACHE_AVAILABILITY_TTL` (int, default: `300`)
- `BOT_CACHE_PREMIUM_LADAS_TTL` (int, default: `86400`)

### Formato y exportación
- `BOT_PHONE_FORMAT_DIGITS` (int, default: `12`)
- `BOT_XLSX_SHEET_NAME` (str, default: `Contactos`)
- `BOT_TXT_ENCODING` (str, default: `utf-8`)

### Limpieza
- `BOT_AUTO_CLEANUP_ENABLED` (bool, default: `True`)
- `BOT_CLEANUP_SCHEDULE_HOURS` (int, default: `24`)
- `BOT_TEMP_FILE_TTL_MINUTES` (int, default: `60`)

## Ejemplo de `.env`

```env
BOT_DB_HOST=localhost
BOT_DB_PORT=5432
BOT_DB_NAME=sms_marketing
BOT_DB_USER=sms_user
BOT_DB_PASSWORD=changeme

BOT_BOT_ENVIRONMENT=development
BOT_BOT_LOG_LEVEL=INFO

BOT_TELEGRAM_BOT_TOKEN=123456789:ABCDEF
BOT_TELEGRAM_BOT_USERNAME=RNumbeRs_bot

BOT_EXPORT_PATH=./exports/
BOT_LOG_PATH=./logs/
```

## Reglas de validación relevantes

- `bot_log_level` valida contra niveles conocidos y se guarda en mayúsculas
- `bot_environment` valida contra `development|staging|production` (en minúsculas)
- `min_extraction_amount <= max_extraction_amount`
- `export_path` y `log_path` se crean si no existen

## URLs de conexión

- Sincrónica: `postgresql://{user}:{password}@{host}:{port}/{db}`
- Asíncrona: `postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}`
