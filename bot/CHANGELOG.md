# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project adheres to Semantic Versioning.

## [Unreleased]

## [1.0.3] - 2025-08-08

### Fixed
- **CRITICAL**: Fixed `'str' object has no attribute 'value'` error in production bot.
- Corrected enum handling in Pydantic models with `use_enum_values = True`.
- Fixed Markdown parsing errors in Telegram messages (switched to MarkdownV2).
- Updated all `.value` references to use `str()` conversion for enum fields.
- Resolved event loop management issues in `telegram_production.py`.

### Changed
- Bot now connects to external existing database instead of creating new PostgreSQL instance.
- Updated `docker-compose.stack.yml` to use `network_mode: host` for external DB connection.
- Moved legacy files (`main.py`, `tests/`, `docker_smoke_test.py`) to `LEGACY/` folder.
- Improved error messages with proper Markdown escaping.

## [1.0.2] - 2025-08-08

### Added
- Pruebas de integración mínimas en `tests/test_integration_bot.py` (modo lectura con `BOT_TEST_MODE`).
- Variable `BOT_TEST_MODE` para ejecutar extracciones contra BD real sin marcar `OPTED_OUT`.

## [1.0.1] - 2025-08-08

### Added
- Documentación integral en `docs/`: `README.md`, `ARCHITECTURE.md`, `CONFIGURATION.md`, `TELEGRAM_BOT.md`, `EXTRACTION_AND_EXPORTS.md`, `LOGGING_AND_AUDIT.md`, `OPERATIONS.md`, `SECURITY_AND_COMPLIANCE.md`.

### Changed
- Estandarización de la cifra de volumen de datos a “31.8M+” en documentación, anotando que puede crecer.

### Security
- Documentadas prácticas de sanitización de entrada, rate limiting y auditoría.

[Unreleased]: https://example.com/compare/1.0.1...HEAD
[1.0.1]: https://example.com/releases/1.0.1
