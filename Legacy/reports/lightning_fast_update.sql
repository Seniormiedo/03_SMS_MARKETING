-- =====================================================
-- ACTUALIZACIÓN LIGHTNING FAST - MÁXIMA VELOCIDAD
-- =====================================================
-- Actualización directa masiva con monitoreo intermedio
-- Tiempo estimado: 30-60 minutos (vs 15-20 horas original)

-- =====================================================
-- PASO 1: PREPARACIÓN Y OPTIMIZACIÓN
-- =====================================================

-- Configurar sesión para máxima performance
SET work_mem = '1GB';
SET maintenance_work_mem = '2GB';
SET checkpoint_completion_target = 0.9;
SET wal_buffers = '64MB';
SET shared_buffers = '512MB';

-- Crear índices temporales si no existen
CREATE INDEX IF NOT EXISTS idx_contacts_phone_bigint ON contacts ((phone_national::BIGINT)) 
WHERE phone_national IS NOT NULL AND phone_national ~ '^[0-9]+$';

-- =====================================================
-- PASO 2: ANÁLISIS PRE-ACTUALIZACIÓN
-- =====================================================

SELECT '=== ANÁLISIS PRE-ACTUALIZACIÓN ===' as titulo;

-- Estado actual
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

-- Muestra de números que cambiarán
SELECT '=== MUESTRA DE CAMBIOS ESPERADOS ===' as titulo;

WITH sample_changes AS (
    SELECT 
        c.status as status_actual,
        CASE 
            WHEN ift.tipo_servicio = 'CPP' THEN 'VERIFIED'
            WHEN ift.tipo_servicio IN ('MPP', 'FIJO') THEN 'NOT_MOBILE'
            ELSE c.status::TEXT
        END as nuevo_status,
        COUNT(*) as cantidad
    FROM contacts c
    JOIN ift_rangos ift ON (
        c.phone_national::BIGINT >= ift.numero_inicial 
        AND c.phone_national::BIGINT <= ift.numero_final
    )
    WHERE c.phone_national IS NOT NULL 
      AND c.phone_national ~ '^[0-9]+$'
      AND length(c.phone_national::text) = 10
      AND c.id <= 100000  -- Solo muestra de 100K
    GROUP BY c.status, ift.tipo_servicio
)
SELECT 
    status_actual,
    nuevo_status,
    cantidad,
    CASE 
        WHEN status_actual != nuevo_status THEN 'CAMBIO'
        ELSE 'SIN CAMBIO'
    END as accion
FROM sample_changes
ORDER BY cantidad DESC;

-- =====================================================
-- PASO 3: FUNCIÓN DE ACTUALIZACIÓN LIGHTNING
-- =====================================================

CREATE OR REPLACE FUNCTION lightning_fast_update()
RETURNS TABLE(
    total_processed BIGINT,
    total_updated BIGINT,
    verified_to_not_mobile BIGINT,
    not_mobile_to_verified BIGINT,
    operators_updated BIGINT,
    execution_time_seconds NUMERIC
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    processed_count BIGINT := 0;
    updated_count BIGINT := 0;
    v_to_nm_count BIGINT := 0;
    nm_to_v_count BIGINT := 0;
    op_updated_count BIGINT := 0;
BEGIN
    start_time := clock_timestamp();
    
    -- Log inicio
    INSERT INTO contacts_ift_changes (contact_id, phone_national, status_anterior, status_nuevo, operator_anterior, operator_nuevo, tipo_servicio_ift, found_in_ift)
    VALUES (0, '0', 'SYSTEM', 'LIGHTNING_START', 'SYSTEM', 'SYSTEM', 'SYSTEM', TRUE);
    
    -- Crear tabla temporal con todos los cambios necesarios
    CREATE TEMP TABLE temp_all_updates AS
    SELECT 
        c.id,
        c.phone_national,
        c.status::TEXT as status_actual,
        c.operator as operator_actual,
        CASE 
            WHEN ift.tipo_servicio = 'CPP' THEN 'VERIFIED'
            WHEN ift.tipo_servicio IN ('MPP', 'FIJO') THEN 'NOT_MOBILE'
            ELSE c.status::TEXT
        END as nuevo_status,
        COALESCE(ift.operador, c.operator) as nuevo_operator,
        ift.tipo_servicio,
        CASE WHEN ift.id IS NOT NULL THEN TRUE ELSE FALSE END as encontrado_ift
    FROM contacts c
    LEFT JOIN ift_rangos ift ON (
        c.phone_national::BIGINT >= ift.numero_inicial 
        AND c.phone_national::BIGINT <= ift.numero_final
    )
    WHERE c.phone_national IS NOT NULL 
      AND c.phone_national ~ '^[0-9]+$'
      AND length(c.phone_national::text) = 10;
    
    -- Crear índice en tabla temporal
    CREATE INDEX idx_temp_updates_id ON temp_all_updates (id);
    
    -- Contar registros procesados
    SELECT COUNT(*) INTO processed_count FROM temp_all_updates;
    
    -- ACTUALIZACIÓN MASIVA LIGHTNING ⚡
    UPDATE contacts 
    SET 
        status = tau.nuevo_status::contactstatus,
        operator = tau.nuevo_operator,
        updated_at = NOW()
    FROM temp_all_updates tau
    WHERE contacts.id = tau.id
      AND (tau.nuevo_status != tau.status_actual OR tau.nuevo_operator != tau.operator_actual);
    
    -- Obtener número de filas actualizadas
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    
    -- Contar tipos de cambios
    SELECT COUNT(*) INTO v_to_nm_count
    FROM temp_all_updates 
    WHERE status_actual = 'VERIFIED' AND nuevo_status = 'NOT_MOBILE';
    
    SELECT COUNT(*) INTO nm_to_v_count
    FROM temp_all_updates 
    WHERE status_actual = 'NOT_MOBILE' AND nuevo_status = 'VERIFIED';
    
    SELECT COUNT(*) INTO op_updated_count
    FROM temp_all_updates 
    WHERE nuevo_operator != operator_actual AND encontrado_ift = TRUE;
    
    -- Log masivo de cambios (solo una muestra para no saturar)
    INSERT INTO contacts_ift_changes (
        contact_id, phone_national, status_anterior, status_nuevo, 
        operator_anterior, operator_nuevo, tipo_servicio_ift, found_in_ift
    )
    SELECT 
        tau.id,
        tau.phone_national,
        tau.status_actual,
        tau.nuevo_status,
        tau.operator_actual,
        tau.nuevo_operator,
        tau.tipo_servicio,
        tau.encontrado_ift
    FROM temp_all_updates tau
    WHERE tau.nuevo_status != tau.status_actual
      AND tau.id % 1000 = 0  -- Solo 1 de cada 1000 para muestra
    LIMIT 10000;  -- Máximo 10K registros en log
    
    -- Limpiar tabla temporal
    DROP TABLE temp_all_updates;
    
    end_time := clock_timestamp();
    
    -- Log finalización
    INSERT INTO contacts_ift_changes (contact_id, phone_national, status_anterior, status_nuevo, operator_anterior, operator_nuevo, tipo_servicio_ift, found_in_ift)
    VALUES (0, '0', 'SYSTEM', 'LIGHTNING_END', 'SYSTEM', 'SYSTEM', 'SYSTEM', TRUE);
    
    RETURN QUERY SELECT 
        processed_count,
        updated_count,
        v_to_nm_count,
        nm_to_v_count,
        op_updated_count,
        EXTRACT(EPOCH FROM (end_time - start_time))::NUMERIC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- PASO 4: EJECUCIÓN LIGHTNING FAST
-- =====================================================

SELECT '=== INICIANDO ACTUALIZACIÓN LIGHTNING FAST ===' as titulo;
SELECT 'Tiempo estimado: 5-15 minutos' as estimacion;
SELECT 'Velocidad objetivo: 10,000+ contactos/segundo' as velocidad;

-- EJECUTAR ACTUALIZACIÓN LIGHTNING ⚡⚡⚡
SELECT * FROM lightning_fast_update();

-- =====================================================
-- PASO 5: VERIFICACIÓN POST-ACTUALIZACIÓN
-- =====================================================

SELECT '=== VERIFICACIÓN POST-ACTUALIZACIÓN ===' as titulo;

-- Estado final
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

-- Resumen de cambios
SELECT '=== RESUMEN DE CAMBIOS ===' as titulo;

SELECT 
    status_anterior,
    status_nuevo,
    COUNT(*) as cantidad
FROM contacts_ift_changes
WHERE status_anterior != 'SYSTEM'
  AND status_nuevo != status_anterior
GROUP BY status_anterior, status_nuevo
ORDER BY cantidad DESC;

-- Top operadores actualizados
SELECT '=== TOP 10 OPERADORES ACTUALIZADOS ===' as titulo;

SELECT 
    operator_nuevo,
    COUNT(*) as cantidad
FROM contacts_ift_changes
WHERE found_in_ift = TRUE
  AND operator_anterior != operator_nuevo
  AND operator_nuevo != 'SYSTEM'
GROUP BY operator_nuevo
ORDER BY cantidad DESC
LIMIT 10;

-- Estadísticas de performance
SELECT '=== ESTADÍSTICAS DE PERFORMANCE ===' as titulo;

WITH performance_stats AS (
    SELECT 
        (SELECT COUNT(*) FROM contacts_ift_changes WHERE status_anterior = 'LIGHTNING_START') as executions,
        (SELECT MAX(change_timestamp) - MIN(change_timestamp) FROM contacts_ift_changes WHERE status_anterior IN ('LIGHTNING_START', 'LIGHTNING_END')) as total_time
)
SELECT 
    executions,
    total_time,
    CASE 
        WHEN total_time > interval '0' THEN 
            ROUND((31833272 / EXTRACT(EPOCH FROM total_time))::NUMERIC, 0)
        ELSE 0 
    END as contactos_por_segundo
FROM performance_stats;

-- =====================================================
-- PASO 6: OPTIMIZACIONES POST-ACTUALIZACIÓN
-- =====================================================

-- Actualizar estadísticas de tablas
ANALYZE contacts;
ANALYZE contacts_ift_changes;

-- Limpiar índices temporales si se crearon
-- DROP INDEX IF EXISTS idx_contacts_phone_bigint;

SELECT '=== ACTUALIZACIÓN LIGHTNING FAST COMPLETADA ===' as titulo;
SELECT 'Revisa las estadísticas arriba para confirmar los resultados' as instruccion;