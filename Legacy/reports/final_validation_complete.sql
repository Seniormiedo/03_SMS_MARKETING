-- VALIDACIÓN FINAL COMPLETA CON TODOS LOS RANGOS IFT
-- CPP = MÓVILES (VERIFIED)
-- MPP + FIJO = FIJOS (NOT_MOBILE)

-- 1. ESTADÍSTICAS ACTUALES DE LA BD
SELECT '=== ESTADÍSTICAS BD ACTUAL ===' as titulo;
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

-- 2. ESTADÍSTICAS RANGOS IFT COMPLETOS
SELECT '=== RANGOS IFT COMPLETOS ===' as titulo;
SELECT 
    tipo_servicio,
    COUNT(*) as rangos,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje,
    CASE 
        WHEN tipo_servicio = 'CPP' THEN 'MÓVILES (VERIFIED)'
        WHEN tipo_servicio IN ('MPP', 'FIJO') THEN 'FIJOS (NOT_MOBILE)'
    END as clasificacion
FROM ift_rangos
GROUP BY tipo_servicio
ORDER BY rangos DESC;

-- 3. CREAR MUESTRA GRANDE Y ESTRATIFICADA (75K contactos)
CREATE TEMP TABLE temp_sample_final AS
SELECT id, phone_national, status, operator
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY status ORDER BY RANDOM()) as rn
    FROM contacts 
    WHERE phone_national IS NOT NULL 
      AND phone_national ~ '^[0-9]+$'
      AND length(phone_national::text) = 10
) t
WHERE rn <= 37500  -- 37.5K por cada status
LIMIT 75000;

SELECT '=== MUESTRA FINAL CREADA ===' as titulo;
SELECT 
    status,
    COUNT(*) as cantidad
FROM temp_sample_final
GROUP BY status
ORDER BY cantidad DESC;

-- 4. EJECUTAR VALIDACIÓN COMPLETA
CREATE TEMP TABLE temp_validation_final AS
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
FROM temp_sample_final ts
CROSS JOIN LATERAL verificar_numero_ift(ts.phone_national::BIGINT) ift;

-- 5. RESULTADOS PRINCIPALES
SELECT '=== RESULTADOS VALIDACIÓN FINAL 75K ===' as titulo;
SELECT 
    status_actual,
    nuevo_status,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje
FROM temp_validation_final
GROUP BY status_actual, nuevo_status
ORDER BY cantidad DESC;

-- 6. COBERTURA IFT COMPLETA
SELECT '=== COBERTURA IFT COMPLETA ===' as titulo;
SELECT 
    encontrado,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje
FROM temp_validation_final
GROUP BY encontrado
ORDER BY encontrado DESC;

-- 7. DISTRIBUCIÓN POR TIPO DE SERVICIO
SELECT '=== DISTRIBUCIÓN POR TIPO SERVICIO ===' as titulo;
SELECT 
    tipo_servicio,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje,
    CASE 
        WHEN tipo_servicio = 'CPP' THEN 'MÓVILES'
        WHEN tipo_servicio IN ('MPP', 'FIJO') THEN 'FIJOS'
        ELSE 'DESCONOCIDO'
    END as clasificacion
FROM temp_validation_final
WHERE encontrado = TRUE
GROUP BY tipo_servicio
ORDER BY cantidad DESC;

-- 8. ANÁLISIS DETALLADO DE CAMBIOS
SELECT '=== ANÁLISIS DETALLADO DE CAMBIOS ===' as titulo;

-- Números VERIFIED que seguirán siendo VERIFIED (CPP)
SELECT 'VERIFIED que mantienen status (CPP)' as cambio,
       COUNT(*) as cantidad,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM temp_validation_final WHERE status_actual = 'VERIFIED'), 2) as porcentaje_del_total_verified
FROM temp_validation_final 
WHERE status_actual = 'VERIFIED' AND nuevo_status = 'VERIFIED';

-- Números VERIFIED que se convertirán a NOT_MOBILE (MPP/FIJO)
SELECT 'VERIFIED que cambian a NOT_MOBILE (MPP/FIJO)' as cambio,
       COUNT(*) as cantidad,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM temp_validation_final WHERE status_actual = 'VERIFIED'), 2) as porcentaje_del_total_verified
FROM temp_validation_final 
WHERE status_actual = 'VERIFIED' AND nuevo_status = 'NOT_MOBILE';

-- Números NOT_MOBILE que se convertirán a VERIFIED (CPP)
SELECT 'NOT_MOBILE que cambian a VERIFIED (CPP)' as cambio,
       COUNT(*) as cantidad,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM temp_validation_final WHERE status_actual = 'NOT_MOBILE'), 2) as porcentaje_del_total_not_mobile
FROM temp_validation_final 
WHERE status_actual = 'NOT_MOBILE' AND nuevo_status = 'VERIFIED';

-- 9. TOP OPERADORES POR TIPO
SELECT '=== TOP 10 OPERADORES MÓVILES (CPP) ===' as titulo;
SELECT 
    operador_ift,
    COUNT(*) as cantidad
FROM temp_validation_final
WHERE tipo_servicio = 'CPP' AND encontrado = TRUE
GROUP BY operador_ift
ORDER BY cantidad DESC
LIMIT 10;

SELECT '=== TOP 10 OPERADORES FIJOS (MPP+FIJO) ===' as titulo;
SELECT 
    operador_ift,
    tipo_servicio,
    COUNT(*) as cantidad
FROM temp_validation_final
WHERE tipo_servicio IN ('MPP', 'FIJO') AND encontrado = TRUE
GROUP BY operador_ift, tipo_servicio
ORDER BY cantidad DESC
LIMIT 10;

-- 10. PROYECCIÓN FINAL A BD COMPLETA
SELECT '=== PROYECCIÓN A BD COMPLETA (31.8M) ===' as titulo;

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
cambios_muestra AS (
    SELECT 
        status_actual,
        nuevo_status,
        COUNT(*) as cantidad_muestra,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY status_actual), 2) as porcentaje_cambio
    FROM temp_validation_final
    GROUP BY status_actual, nuevo_status
)
SELECT 
    ta.status as status_actual,
    FORMAT('%s', ta.total) as contactos_actuales,
    cm.nuevo_status,
    cm.porcentaje_cambio || '%' as porcentaje,
    FORMAT('%s', ROUND(ta.total * cm.porcentaje_cambio / 100)) as contactos_proyectados
FROM totales_actuales ta
JOIN cambios_muestra cm ON ta.status = cm.status_actual
WHERE cm.porcentaje_cambio > 0.1
ORDER BY (ta.total * cm.porcentaje_cambio / 100) DESC;