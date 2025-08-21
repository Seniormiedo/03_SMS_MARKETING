# 📤 Extracción y Exportaciones

## Tipos de extracción

- `premium`: Mejores LADAs (consulta balanceada por top LADAs)
- `state`: Por estado (coincidencia ILIKE)
- `city`: Por ciudad (coincidencia ILIKE)
- `municipality`: Por municipio (coincidencia ILIKE)
- `lada`: Por LADA exacta

Orígenes: `core/database.py` (métodos `get_premium_contacts`, `get_contacts_by_state`, etc.)

## Validaciones y disponibilidad

- `core/validators.py` valida: formato `/get`, cantidad, formato de exportación, ubicación conocida
- `services/contact_service.py` verifica disponibilidad previa a extraer
- Si no hay contactos disponibles, se retorna error claro al usuario

## Límites

- Cantidad: `100` a `10,000` por extracción
- Diarias: recomendado `≤ 50,000`
- Rate limit: configurable; producción típicamente 3s entre comandos por usuario

## Marcado `OPTED_OUT`

Tras extraer, los contactos utilizados se marcan `OPTED_OUT` vía `core/database.py` para evitar reutilización.

## Exportaciones

- Formatos: `XLSX` y `TXT` (ver `services/export_service.py`)
- Ruta: `BOT_EXPORT_PATH` (default `./exports/`)

### XLSX
- Hoja `Contactos` con columnas: `Number`, `Content`
- `Number`: teléfono a 12 dígitos `52xxxxxxxxxx`
- `Content`: ubicación en mayúsculas (ciudad/estado) **truncada a máximo 11 caracteres**
- Hoja `Metadata` con: fecha, total, formato, versión del bot

### TXT
- Un número por línea, formateado a 12 dígitos `52xxxxxxxxxx`

## Nombres de archivo

Regla: `<tipo>_<cantidad>[_<ubicacion>]_<YYYYMMDD_HHMMSS>.<ext>`

Ejemplos:
- `premium_1000_20250101_120000.xlsx`
- `state_500_Sinaloa_20250101_120000.txt`

Generación: `utils/formatters.py` (`FileNameGenerator.generate_extraction_filename`)
