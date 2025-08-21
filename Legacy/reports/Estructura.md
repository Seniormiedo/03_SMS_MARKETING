# 📊 Análisis de Estructura - SMS Marketing Database

**Fecha de análisis:** 2025-08-05T11:15:31.922487

## 📁 Información General del Archivo

- **Nombre:** `numeros.db`
- **Tamaño:** 10.26 GB (10502.28 MB)
- **Última modificación:** 2025-08-04T18:00:18.316981
- **Fecha de creación:** 2025-08-04T17:24:44.331970

## 📋 Estructura de Tablas

### 🗂️ Tabla: `estadisticas_migracion`

**Registros totales:** 1

#### Columnas

| Nombre | Tipo | Nulo | Clave Primaria | Valor Defecto |
|--------|------|------|----------------|---------------|
| `id` | INTEGER | ✅ | 🔑 | ➖ |
| `total_procesados` | INTEGER | ✅ | ➖ | ➖ |
| `total_validos` | INTEGER | ✅ | ➖ | ➖ |
| `total_duplicados` | INTEGER | ✅ | ➖ | ➖ |
| `total_con_ciudad` | INTEGER | ✅ | ➖ | ➖ |
| `ladas_encontradas` | INTEGER | ✅ | ➖ | ➖ |
| `ladas_faltantes` | INTEGER | ✅ | ➖ | ➖ |
| `tiempo_procesamiento_segundos` | REAL | ✅ | ➖ | ➖ |
| `archivo_origen` | TEXT | ✅ | ➖ | ➖ |
| `fecha_migracion` | TIMESTAMP | ✅ | ➖ | CURRENT_TIMESTAMP |

#### Muestra de Datos (primeros 5 registros)

```json
[
  {
    "id": 1,
    "total_procesados": 36653021,
    "total_validos": 36645692,
    "total_duplicados": 0,
    "total_con_ciudad": "b'\\xd97\\x13\\x01\\x00\\x00\\x00\\x00'",
    "ladas_encontradas": 171,
    "ladas_faltantes": 186,
    "tiempo_procesamiento_segundos": 2155.215403,
    "archivo_origen": "TELCEL2022.csv",
    "fecha_migracion": "2025-08-05 01:00:18"
  }
]
```

#### SQL de Creación

```sql
CREATE TABLE estadisticas_migracion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    total_procesados INTEGER,
    total_validos INTEGER,
    total_duplicados INTEGER,
    total_con_ciudad INTEGER,
    ladas_encontradas INTEGER,
    ladas_faltantes INTEGER,
    tiempo_procesamiento_segundos REAL,
    archivo_origen TEXT,
    fecha_migracion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

---

### 🗂️ Tabla: `ladas_faltantes`

**Registros totales:** 186

#### Columnas

| Nombre | Tipo | Nulo | Clave Primaria | Valor Defecto |
|--------|------|------|----------------|---------------|
| `lada` | TEXT | ✅ | 🔑 | ➖ |
| `cantidad_registros` | INTEGER | ✅ | ➖ | ➖ |
| `ejemplos_numeros` | TEXT | ✅ | ➖ | ➖ |
| `fecha_detectado` | TIMESTAMP | ✅ | ➖ | CURRENT_TIMESTAMP |

#### Índices

- **sqlite_autoindex_ladas_faltantes_1**: lada (ÚNICO)

#### Muestra de Datos (primeros 5 registros)

```json
[
  {
    "lada": "845",
    "cantidad_registros": 18301,
    "ejemplos_numeros": "8451002316, 8451002359, 8451002384",
    "fecha_detectado": "2025-08-05 01:00:18"
  },
  {
    "lada": "846",
    "cantidad_registros": 51167,
    "ejemplos_numeros": "8461000043, 8461000056, 8461000072",
    "fecha_detectado": "2025-08-05 01:00:18"
  },
  {
    "lada": "864",
    "cantidad_registros": 26512,
    "ejemplos_numeros": "8641000122, 8641001374, 8641002051",
    "fecha_detectado": "2025-08-05 01:00:18"
  },
  {
    "lada": "869",
    "cantidad_registros": 8700,
    "ejemplos_numeros": "8691000002, 8691000003, 8691000004",
    "fecha_detectado": "2025-08-05 01:00:18"
  },
  {
    "lada": "873",
    "cantidad_registros": 14832,
    "ejemplos_numeros": "8731000023, 8731000028, 8731000046",
    "fecha_detectado": "2025-08-05 01:00:18"
  }
]
```

#### SQL de Creación

```sql
CREATE TABLE ladas_faltantes (
    lada TEXT PRIMARY KEY,
    cantidad_registros INTEGER,
    ejemplos_numeros TEXT,
    fecha_detectado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

---

### 🗂️ Tabla: `numeros`

**Registros totales:** 36,645,692

#### Columnas

| Nombre | Tipo | Nulo | Clave Primaria | Valor Defecto |
|--------|------|------|----------------|---------------|
| `id` | INTEGER | ✅ | 🔑 | ➖ |
| `numero` | TEXT | ❌ | ➖ | ➖ |
| `campo1_original` | TEXT | ✅ | ➖ | ➖ |
| `nombre` | TEXT | ✅ | ➖ | ➖ |
| `campo3` | TEXT | ✅ | ➖ | ➖ |
| `direccion` | TEXT | ✅ | ➖ | ➖ |
| `colonia` | TEXT | ✅ | ➖ | ➖ |
| `municipio_csv` | TEXT | ✅ | ➖ | ➖ |
| `estado_sep` | TEXT | ✅ | ➖ | ➖ |
| `municipio_sep` | TEXT | ✅ | ➖ | ➖ |
| `estado_cof` | TEXT | ✅ | ➖ | ➖ |
| `municipio_cof` | TEXT | ✅ | ➖ | ➖ |
| `lada` | TEXT | ✅ | ➖ | ➖ |
| `ciudad_por_lada` | TEXT | ✅ | ➖ | ➖ |
| `es_valido` | BOOLEAN | ✅ | ➖ | 1 |
| `fecha_migracion` | TIMESTAMP | ✅ | ➖ | CURRENT_TIMESTAMP |

#### Índices

- **idx_fecha**: fecha_migracion 
- **idx_municipio**: municipio_cof 
- **idx_ciudad**: ciudad_por_lada 
- **idx_lada**: lada 
- **idx_numero**: numero 
- **sqlite_autoindex_numeros_1**: numero (ÚNICO)

#### Muestra de Datos (primeros 5 registros)

```json
[
  {
    "id": 1,
    "numero": "6121004768",
    "campo1_original": "6121004768",
    "nombre": "CATALINO RODRIGUEZ ALVARADO",
    "campo3": null,
    "direccion": "ENCINAS Y EMILIANO ZAPATA #2695",
    "colonia": "LOS OLIVOS LA RINCONADA",
    "municipio_csv": "MEXICO",
    "estado_sep": null,
    "municipio_sep": null,
    "estado_cof": "BCS",
    "municipio_cof": "LA PAZ",
    "lada": "612",
    "ciudad_por_lada": "La Paz",
    "es_valido": 1,
    "fecha_migracion": "2025-08-05 00:24:44"
  },
  {
    "id": 2,
    "numero": "6121005000",
    "campo1_original": "6121005000",
    "nombre": "NORMA RRFUGIO AVILEZ RODRIGUEZ",
    "campo3": null,
    "direccion": "VILLA CAMILA / VILLA NATALIA Y NAOMI 361",
    "colonia": "VILLA DEL ENCANTO",
    "municipio_csv": "LA PAZ",
    "estado_sep": "BAJA CALIFORNIA SUR",
    "municipio_sep": "LA PAZ",
    "estado_cof": "BCS",
    "municipio_cof": "LA PAZ",
    "lada": "612",
    "ciudad_por_lada": "La Paz",
    "es_valido": 1,
    "fecha_migracion": "2025-08-05 00:24:44"
  },
  {
    "id": 3,
    "numero": "6121005002",
    "campo1_original": "6121005002",
    "nombre": "RAMON ANDRES ESPINOZA GOMEZ",
    "campo3": "SIN",
    "direccion": "RIO PANUCO Y RIO BALZA SIN Int.SIN",
    "colonia": "LAGUNA AZUL",
    "municipio_csv": "TIJUANA",
    "estado_sep": null,
    "municipio_sep": null,
    "estado_cof": "BCS",
    "municipio_cof": "LA PAZ",
    "lada": "612",
    "ciudad_por_lada": "La Paz",
    "es_valido": 1,
    "fecha_migracion": "2025-08-05 00:24:44"
  },
  {
    "id": 4,
    "numero": "6121005003",
    "campo1_original": "6121005003",
    "nombre": "NANCY CAMACHO OSORIO",
    "campo3": "SN",
    "direccion": "NEVADA DE COLIMA ENTRE SAN MARTIN Y SANTA A 145",
    "colonia": "SANTA FE",
    "municipio_csv": "LA PAZ",
    "estado_sep": null,
    "municipio_sep": null,
    "estado_cof": "BCS",
    "municipio_cof": "LA PAZ",
    "lada": "612",
    "ciudad_por_lada": "La Paz",
    "es_valido": 1,
    "fecha_migracion": "2025-08-05 00:24:44"
  },
  {
    "id": 5,
    "numero": "6121005004",
    "campo1_original": "6121005004",
    "nombre": "ROSA LILIA HERNANDEZ PENUELAS",
    "campo3": "HEPR730426",
    "direccion": "FISIMAR 161 Int.00000",
    "colonia": "INDECO",
    "municipio_csv": "LA PAZ",
    "estado_sep": null,
    "municipio_sep": null,
    "estado_cof": "BCS",
    "municipio_cof": "LA PAZ",
    "lada": "612",
    "ciudad_por_lada": "La Paz",
    "es_valido": 1,
    "fecha_migracion": "2025-08-05 00:24:44"
  }
]
```

#### SQL de Creación

```sql
CREATE TABLE numeros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT NOT NULL UNIQUE,
    campo1_original TEXT,
    nombre TEXT,
    campo3 TEXT,
    direccion TEXT,
    colonia TEXT,
    municipio_csv TEXT,
    estado_sep TEXT,
    municipio_sep TEXT,
    estado_cof TEXT,
    municipio_cof TEXT,
    lada TEXT,
    ciudad_por_lada TEXT,
    es_valido BOOLEAN DEFAULT 1,
    fecha_migracion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

---

## 📱 Análisis de Patrones de Datos

### 🔍 Columna: `ladas_faltantes.ejemplos_numeros`

- **Total valores:** 186
- **Valores únicos:** 186
- **Longitud promedio:** 33.9 caracteres
- **Tipos detectados:** str

#### Muestra de Valores

```
8451002316, 8451002359, 8451002384
8461000043, 8461000056, 8461000072
8641000122, 8641001374, 8641002051
8691000002, 8691000003, 8691000004
8731000023, 8731000028, 8731000046
8911010154, 8911010404, 8911011662
8921000004, 8921000009, 8921000012
8941000010, 8941000013, 8941000014
8971000000, 8971000031, 8971000673
3151000002, 3151000003, 3151000005
```

---

### 🔍 Columna: `numeros.numero`

- **Total valores:** 1,000
- **Valores únicos:** 1,000
- **Longitud promedio:** 10.0 caracteres
- **Tipos detectados:** str

#### 📞 Análisis de Números Telefónicos

**Formatos detectados:**
- `nacional_10_digitos`: 1,000 (100.0%)

**Distribución por longitud:**
- 10 dígitos: 1,000 (100.0%)

**Prefijos más comunes (top 10):**
- `222`: 1,000 (100.0%)

**Validez:** 1,000 válidos (100.0%), 0 inválidos

#### Muestra de Valores

```
2221000014
2221000052
2221000100
2221000110
2221000160
2221000302
2221000339
2221000342
2221000366
2221000674
```

---

## 💡 Recomendaciones para Migración

### 🔄 Estrategia de Migración

1. **Limpieza de datos:**
   - Normalizar formatos de números telefónicos
   - Eliminar duplicados
   - Validar números según estándares internacionales

2. **Optimización:**
   - Crear índices en columnas de búsqueda frecuente
   - Particionar tablas grandes por fecha o región
   - Implementar compresión para reducir espacio

3. **Seguridad:**
   - Cifrar números telefónicos sensibles
   - Implementar auditoría de accesos
   - Configurar backups automáticos

### 🏗️ Arquitectura Recomendada

```
PostgreSQL (Principal)
├── contacts (números normalizados)
├── campaigns (campañas de marketing)
├── messages (historial de mensajes)
├── opt_outs (lista de exclusión)
└── analytics (métricas y reportes)

Redis (Cache/Queue)
├── session_cache
├── message_queue
└── rate_limiting
```

---

*Reporte generado automáticamente por SMS Marketing Platform Analyzer*
