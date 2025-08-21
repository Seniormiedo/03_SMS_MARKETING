# 🛠️ Operaciones

## Arranque rápido

1. Crear y completar `.env` (ver `CONFIGURATION.md`)
2. Instalar dependencias: `pip install -r requirements.txt`
3. Ejecutar según modo:
   - CLI/Servicio: `python main.py` (o `python main.py --interactive`)
   - Telegram general: `python telegram_main.py`
   - Telegram demo: `python telegram_demo.py`
   - Telegram producción: `python telegram_production.py`

## Verificación de conectividad BD

- El sistema prueba conexión al inicializar (`DatabaseManager.test_connection()`)
- Revisar `BOT_DB_HOST`, `BOT_DB_PORT`, `BOT_DB_NAME`, `BOT_DB_USER`, `BOT_DB_PASSWORD`

## Limpieza de exportaciones

- `ExportService.cleanup_old_files(days_old)` borra archivos en `BOT_EXPORT_PATH` más antiguos que `days_old` (default: `BOT_FILE_RETENTION_DAYS`)

## Cuotas y límites

- Extracción: 100–10,000 contactos
- Diario recomendado: ≤ 50,000
- Rate limit: producción ~ 1 comando cada 3s por usuario

## Troubleshooting

- Error conexión BD: validar credenciales, reachability y privilegios
- Archivo demasiado grande para Telegram: reducir cantidad o usar TXT
- Validación de comando: usar `/help` para formato correcto
- Permisos de escritura: verificar rutas de `BOT_EXPORT_PATH` y `BOT_LOG_PATH`
