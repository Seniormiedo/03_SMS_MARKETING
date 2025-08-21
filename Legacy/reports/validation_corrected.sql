-- VALIDACIÓN CORREGIDA CON LÓGICA IFT CORRECTA
-- CPP = MÓVILES (VERIFIED)  
-- MPP/FPP = FIJOS (NOT_MOBILE)

-- Crear muestra de 15,000 contactos para validación más robusta
CREATE TEMP TABLE temp_sample_corrected AS
SELECT id, phone_national, status, operator
FROM contacts 
WHERE phone_national IS NOT NULL 
  AND phone_national ~ '^[0-9]+$'
  AND length(phone_national::text) = 10
ORDER BY RANDOM()
LIMIT 15000;

-- Ejecutar validación con función corregida
CREATE TEMP TABLE temp_validation_corrected AS
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
FROM temp_sample_corrected ts
CROSS JOIN LATERAL verificar_numero_ift(ts.phone_national::BIGINT) ift;

-- RESULTADOS PRINCIPALES
SELECT '=== RESULTADOS DE VALIDACIÓN CORREGIDA ===' as titulo;

-- Resumen por cambio de status
SELECT 
    status_actual,
    nuevo_status,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje
FROM temp_validation_corrected
GROUP BY status_actual, nuevo_status
ORDER BY cantidad DESC;

-- Estadísticas de números encontrados vs no encontrados
SELECT '=== COBERTURA IFT ===' as titulo;
SELECT 
    encontrado,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje
FROM temp_validation_corrected
GROUP BY encontrado;

-- Distribución por tipo de servicio encontrado
SELECT '=== DISTRIBUCIÓN POR TIPO DE SERVICIO ===' as titulo;
SELECT 
    tipo_servicio,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje
FROM temp_validation_corrected
WHERE encontrado = TRUE
GROUP BY tipo_servicio
ORDER BY cantidad DESC;

-- Top operadores reales identificados
SELECT '=== TOP 10 OPERADORES REALES ===' as titulo;
SELECT 
    operador_ift,
    tipo_servicio,
    COUNT(*) as cantidad
FROM temp_validation_corrected
WHERE encontrado = TRUE
GROUP BY operador_ift, tipo_servicio
ORDER BY cantidad DESC
LIMIT 10;