# 📝 Logging y Auditoría

El sistema usa `structlog` + `rich` para logging estructurado y un logger separado de auditoría.

- Archivo: `utils/logger.py`
- Clase: `BotLogger`
- Directorio de logs: `BOT_LOG_PATH` (default `./logs/`)
- Archivos generados:
  - `bot_YYYYMMDD.log` (evento general)
  - `audit_YYYYMMDD.log` (auditoría; habilitado si `BOT_ENABLE_AUDIT_LOG=true`)

## Eventos de auditoría

- `BOT_STARTUP` (info del sistema)
- `EXTRACTION_REQUEST` (parámetros solicitados)
- `EXTRACTION_SUCCESS` / `REAL_EXTRACTION_SUCCESS` (resumen y sample IDs)
- `EXTRACTION_ERROR` / `REAL_EXTRACTION_FAILED` (errores)
- `FILE_EXPORT` (ruta, tamaño, formato)
- `VALIDATION_ERROR` (tipo y entrada)
- `RATE_LIMIT_EXCEEDED`

## Buenas prácticas

- Nivel por entorno: `INFO` en producción; `DEBUG` en desarrollo
- Auditoría activa en producción
- No loggear secretos (`DB_PASSWORD`, tokens)
