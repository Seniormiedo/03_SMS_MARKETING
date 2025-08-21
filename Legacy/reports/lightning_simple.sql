-- LIGHTNING FAST SIMPLIFICADO - SIN CAMBIOS DE CONFIGURACIÓN
-- Actualización masiva directa de todos los contactos

-- Estadísticas antes
SELECT '=== ESTADÍSTICAS ANTES DE ACTUALIZACIÓN ===' as titulo;
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

-- Función Lightning simplificada
CREATE OR REPLACE FUNCTION lightning_simple_update()
RETURNS TABLE(
    total_processed BIGINT,
    total_updated BIGINT,
    execution_time_seconds NUMERIC
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    processed_count BIGINT := 0;
    updated_count BIGINT := 0;
BEGIN
    start_time := clock_timestamp();
    
    -- Log inicio
    RAISE NOTICE 'INICIANDO ACTUALIZACIÓN LIGHTNING FAST...';
    
    -- Contar contactos a procesar
    SELECT COUNT(*) INTO processed_count
    FROM contacts 
    WHERE phone_national IS NOT NULL 
      AND phone_national ~ '^[0-9]+$'
      AND length(phone_national::text) = 10;
    
    RAISE NOTICE 'Contactos a procesar: %', processed_count;
    
    -- ACTUALIZACIÓN MASIVA DIRECTA
    UPDATE contacts 
    SET 
        status = CASE 
            WHEN ift.tipo_servicio = 'CPP' THEN 'VERIFIED'::contactstatus
            WHEN ift.tipo_servicio IN ('MPP', 'FIJO') THEN 'NOT_MOBILE'::contactstatus
            ELSE status
        END,
        operator = COALESCE(ift.operador, operator),
        updated_at = NOW()
    FROM ift_rangos ift
    WHERE contacts.phone_national::BIGINT >= ift.numero_inicial 
      AND contacts.phone_national::BIGINT <= ift.numero_final
      AND contacts.phone_national IS NOT NULL 
      AND contacts.phone_national ~ '^[0-9]+$'
      AND length(contacts.phone_national::text) = 10;
    
    -- Obtener número de filas actualizadas
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    
    end_time := clock_timestamp();
    
    RAISE NOTICE 'ACTUALIZACIÓN COMPLETADA: % procesados, % actualizados', processed_count, updated_count;
    
    RETURN QUERY SELECT 
        processed_count,
        updated_count,
        EXTRACT(EPOCH FROM (end_time - start_time))::NUMERIC;
END;
$$ LANGUAGE plpgsql;

-- EJECUTAR ACTUALIZACIÓN LIGHTNING
SELECT '=== EJECUTANDO LIGHTNING FAST ===' as mensaje;
SELECT * FROM lightning_simple_update();

-- Estadísticas después
SELECT '=== ESTADÍSTICAS DESPUÉS DE ACTUALIZACIÓN ===' as titulo;
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

SELECT '=== LIGHTNING FAST COMPLETADO ===' as resultado;