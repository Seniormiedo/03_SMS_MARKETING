# 📚 Documentación del Sistema - Contact Extractor Bot

Este directorio contiene la documentación técnica y operativa del sistema de extracción de contactos (Contact Extractor Bot). Toda la documentación está alineada con el código actual del repositorio y sirve como referencia para desarrollo, operaciones y cumplimiento.

Nota sobre volumen de datos: La documentación de base de datos referencia 31.8M+ contactos. La cifra puede crecer con nuevas cargas; las guías operativas y de rendimiento consideran este incremento.

## Índice

- Arquitectura general del sistema: consulte `ARCHITECTURE.md`
- Configuración y variables de entorno: consulte `CONFIGURATION.md`
- Bot de Telegram (demo, general y producción): consulte `TELEGRAM_BOT.md`
- Extracciones y exportaciones (XLSX/TXT): consulte `EXTRACTION_AND_EXPORTS.md`
- Logging y auditoría (estructurado + eventos): consulte `LOGGING_AND_AUDIT.md`
- Operaciones (arranque, limpieza, troubleshooting): consulte `OPERATIONS.md`
- Seguridad y cumplimiento (validación, opt-out, límites): consulte `SECURITY_AND_COMPLIANCE.md`
- Documentación de Base de Datos: consulte `db/README.md`

## Puntos de entrada del sistema

- CLI/Servicio: `main.py`
- Telegram (general): `telegram_main.py`
- Telegram (demo, sin BD): `telegram_demo.py`
- Telegram (producción, con BD real): `telegram_production.py`

## Componentes principales (referencia rápida)

- Configuración: `config.py` (Pydantic Settings, prefijo `BOT_`, `.env`)
- Núcleo: `core/database.py`, `core/validators.py`, `core/telegram_bot.py`
- Servicios: `services/contact_service.py`, `services/export_service.py`
- Modelos: `models/contact.py`, `models/extraction.py`
- Utilidades: `utils/logger.py`, `utils/formatters.py`

## Diagramas

Guarde los diagramas SVG provistos en la conversación en `./Diagramas de flujo/` con los nombres:

- `arquitectura-sistema.svg`
- `flujo-telegram.svg`

## Convenciones

- Idioma: Español
- SemVer: cambios documentados en `CHANGELOG.md`
- Estándar de documentación: Keep a Changelog para cambios; este `docs/` para guías técnicas


