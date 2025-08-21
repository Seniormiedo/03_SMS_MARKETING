# 🔐 Seguridad y Cumplimiento

## Validación y sanitización

- Validación estricta de comandos en `core/validators.py`
- Sanitización de nombres de archivo en `utils/formatters.py` (`FileNameGenerator.sanitize_filename`)
- Validación de teléfonos con `phonenumbers` y normalización a 12/13 dígitos

## Rate limiting y control de uso

- Rate limit configurable (`BOT_ENABLE_RATE_LIMITING`)
- Límites por cantidad y diarios (ver `CONFIGURATION.md`)

## Opt-out y no-reutilización

- Marcado `OPTED_OUT` posterior a extracción (`core/database.py`)
- Previene reuso accidental de contactos

## Auditoría y trazabilidad

- Eventos de auditoría detallados (ver `LOGGING_AND_AUDIT.md`)
- Útil para cumplimiento y post-mortem

## Manejo de secretos

- Variables sensibles en `.env` (`BOT_DB_PASSWORD`, `BOT_TELEGRAM_BOT_TOKEN`)
- No exponer en logs ni en repositorio

## Privacidad y datos

- Campos exportados mínimos (teléfono + ubicación)
- Retención limitada de archivos (`BOT_FILE_RETENTION_DAYS`)
- Considerar cifrado de backups de BD y control de acceso
