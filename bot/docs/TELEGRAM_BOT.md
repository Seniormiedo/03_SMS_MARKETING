# 🤖 Bot de Telegram

Esta guía cubre los modos del bot de Telegram: demo, general y producción.

## Archivos relevantes

- General: `core/telegram_bot.py` (clase `TelegramContactBot`) + `telegram_main.py`
- Demo: `telegram_demo.py` (clase `TelegramBotDemo`)
- Producción: `telegram_production.py` (clase `TelegramProductionBot`)

## Comandos soportados

- `/start`, `/help`, `/get`, `/stats`, `/states`, `/cities`, `/available`
- Menús y botones inline para acciones rápidas

## Diferencias por modo

- **Demo**
  - Sin conexión a BD (datos simulados)
  - Genera archivos de muestra (contenido mock)
  - Ideal para validación funcional
- **General**
  - Carga ubicaciones desde BD
  - Valida y ejecuta flujo de extracción usando servicios
  - Requiere configuración y BD operativa
- **Producción**
  - Conexión real a BD, extracción real
  - Límites reforzados (rate limit ~3s, cuotas diarias)
  - Marca contactos como `OPTED_OUT`
  - Subida de archivo con validación de tamaño

## Límites y confirmaciones

- Rango por extracción: `100` a `10,000`
- Límite diario recomendado: `50,000` contactos
- Confirmación requerida para extracciones grandes según `config.should_require_confirmation(amount)`
- Tamaño máximo de archivo a subir a Telegram: `BOT_TELEGRAM_MAX_FILE_SIZE_MB` (default 50MB)

## Ejecución

- Demo: `python telegram_demo.py`
- General: `python telegram_main.py`
- Producción: `python telegram_production.py`

Asegúrese de configurar `.env` con `BOT_TELEGRAM_BOT_TOKEN` y credenciales de base de datos.

## Errores y manejo

- Errores se notifican al usuario y se registran en logs
- Eventos de auditoría: inicio de usuario, éxito/fallo de extracción, exportación de archivo
