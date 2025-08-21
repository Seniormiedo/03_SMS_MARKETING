-- ANÁLISIS COMPLETO DE 31M CONTACTOS CON LÓGICA IFT CORRECTA
-- CPP = MÓVILES (VERIFIED)
-- MPP/FPP = FIJOS (NOT_MOBILE)

-- 1. ESTADÍSTICAS GENERALES DE LA BD
SELECT '=== ESTADÍSTICAS GENERALES BD ===' as titulo;
SELECT 
    status,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje
FROM contacts
WHERE phone_national IS NOT NULL 
  AND phone_national ~ '^[0-9]+$'
  AND length(phone_national::text) = 10
GROUP BY status
ORDER BY cantidad DESC;

-- 2. ESTADÍSTICAS DE RANGOS IFT CARGADOS
SELECT '=== RANGOS IFT DISPONIBLES ===' as titulo;
SELECT 
    tipo_servicio,
    COUNT(*) as rangos,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje,
    MIN(numero_inicial) as primer_numero,
    MAX(numero_final) as ultimo_numero
FROM ift_rangos
GROUP BY tipo_servicio
ORDER BY rangos DESC;

-- 3. CREAR MUESTRA ESTRATIFICADA MÁS GRANDE (50K contactos)
CREATE TEMP TABLE temp_sample_full AS
SELECT id, phone_national, status, operator
FROM (
    -- Tomar muestra proporcional por status
    SELECT *, ROW_NUMBER() OVER (PARTITION BY status ORDER BY RANDOM()) as rn
    FROM contacts 
    WHERE phone_national IS NOT NULL 
      AND phone_national ~ '^[0-9]+$'
      AND length(phone_national::text) = 10
) t
WHERE rn <= 25000  -- 25K por cada status principal
LIMIT 50000;

SELECT '=== MUESTRA CREADA ===' as titulo;
SELECT 
    status,
    COUNT(*) as cantidad
FROM temp_sample_full
GROUP BY status
ORDER BY cantidad DESC;

-- 4. EJECUTAR VALIDACIÓN IFT EN MUESTRA GRANDE
CREATE TEMP TABLE temp_validation_full AS
SELECT 
    ts.id,
    ts.phone_national,
    ts.status as status_actual,
    ts.operator as operador_actual,
    ift.es_movil,
    ift.operador as operador_ift,
    ift.tipo_servicio,
    ift.encontrado,
    CASE 
        WHEN ift.es_movil = TRUE THEN 'VERIFIED'
        WHEN ift.es_movil = FALSE AND ift.encontrado = TRUE THEN 'NOT_MOBILE'
        ELSE 'UNKNOWN'
    END as nuevo_status
FROM temp_sample_full ts
CROSS JOIN LATERAL verificar_numero_ift(ts.phone_national::BIGINT) ift;

-- 5. RESULTADOS PRINCIPALES DE VALIDACIÓN
SELECT '=== RESULTADOS VALIDACIÓN 50K MUESTRA ===' as titulo;
SELECT 
    status_actual,
    nuevo_status,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje
FROM temp_validation_full
GROUP BY status_actual, nuevo_status
ORDER BY cantidad DESC;

-- 6. COBERTURA IFT EN MUESTRA
SELECT '=== COBERTURA IFT ===' as titulo;
SELECT 
    encontrado,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje
FROM temp_validation_full
GROUP BY encontrado;

-- 7. DISTRIBUCIÓN POR TIPO DE SERVICIO EN MUESTRA
SELECT '=== DISTRIBUCIÓN TIPO SERVICIO ===' as titulo;
SELECT 
    tipo_servicio,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje
FROM temp_validation_full
WHERE encontrado = TRUE
GROUP BY tipo_servicio
ORDER BY cantidad DESC;

-- 8. ANÁLISIS DE NÚMEROS NO ENCONTRADOS EN IFT
SELECT '=== NÚMEROS NO ENCONTRADOS ===' as titulo;
SELECT 
    status_actual,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje,
    MIN(phone_national) as ejemplo_min,
    MAX(phone_national) as ejemplo_max
FROM temp_validation_full
WHERE encontrado = FALSE
GROUP BY status_actual;

-- 9. TOP OPERADORES IDENTIFICADOS
SELECT '=== TOP 15 OPERADORES REALES ===' as titulo;
SELECT 
    operador_ift,
    tipo_servicio,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje
FROM temp_validation_full
WHERE encontrado = TRUE
GROUP BY operador_ift, tipo_servicio
ORDER BY cantidad DESC
LIMIT 15;

-- 10. PROYECCIÓN A BASE COMPLETA
SELECT '=== PROYECCIÓN A BD COMPLETA ===' as titulo;

-- Calcular totales actuales
WITH totales_actuales AS (
    SELECT 
        status,
        COUNT(*) as total
    FROM contacts
    WHERE phone_national IS NOT NULL 
      AND phone_national ~ '^[0-9]+$'
      AND length(phone_national::text) = 10
    GROUP BY status
),
-- Calcular porcentajes de cambio de la muestra
cambios_muestra AS (
    SELECT 
        status_actual,
        nuevo_status,
        COUNT(*) as cantidad_muestra,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY status_actual), 2) as porcentaje_cambio
    FROM temp_validation_full
    GROUP BY status_actual, nuevo_status
)
SELECT 
    ta.status as status_actual,
    ta.total as contactos_actuales,
    cm.nuevo_status,
    cm.porcentaje_cambio,
    ROUND(ta.total * cm.porcentaje_cambio / 100) as contactos_proyectados
FROM totales_actuales ta
JOIN cambios_muestra cm ON ta.status = cm.status_actual
WHERE cm.porcentaje_cambio > 0.1  -- Solo mostrar cambios significativos
ORDER BY contactos_proyectados DESC;