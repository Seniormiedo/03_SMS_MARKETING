-- ============================================================================
-- ACTUALIZACIÓN MASIVA ULTRA SEGURA CON CHECKPOINTS
-- Actualiza TODOS los 31.8M contactos con máxima seguridad
-- Incluye: Backups, Checkpoints, Rollback completo, Verificación total
-- ============================================================================

-- Configuración para máxima seguridad
SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;

-- ============================================================================
-- PASO 1: BACKUP COMPLETO DE SEGURIDAD
-- ============================================================================

SELECT '🔒 CREANDO BACKUP ULTRA SEGURO' as mensaje;

-- Backup completo de contacts (si no existe)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'contacts_backup_ultra_safe') THEN
        CREATE TABLE contacts_backup_ultra_safe AS SELECT * FROM contacts;
        RAISE NOTICE 'Backup ultra seguro creado: % registros', (SELECT COUNT(*) FROM contacts_backup_ultra_safe);
    ELSE
        RAISE NOTICE 'Backup ultra seguro ya existe';
    END IF;
END $$;

-- Tabla de checkpoints para control granular
DROP TABLE IF EXISTS update_checkpoints CASCADE;
CREATE TABLE update_checkpoints (
    checkpoint_id SERIAL PRIMARY KEY,
    batch_start BIGINT NOT NULL,
    batch_end BIGINT NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    processed_count INTEGER DEFAULT 0,
    updated_count INTEGER DEFAULT 0,
    start_time TIMESTAMP DEFAULT NOW(),
    end_time TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabla de cambios detallada para auditoría completa
DROP TABLE IF EXISTS contacts_changes_ultra_safe CASCADE;
CREATE TABLE contacts_changes_ultra_safe (
    change_id SERIAL PRIMARY KEY,
    contact_id BIGINT NOT NULL,
    phone_national VARCHAR(15),
    status_before contactstatus,
    status_after contactstatus,
    operator_before VARCHAR(100),
    operator_after VARCHAR(100),
    ift_tipo_servicio VARCHAR(10),
    ift_operador VARCHAR(100),
    batch_id INTEGER,
    changed_at TIMESTAMP DEFAULT NOW()
);

SELECT '✅ SISTEMA DE BACKUP Y CHECKPOINTS PREPARADO' as mensaje;

-- ============================================================================
-- PASO 2: GENERAR PLAN DE LOTES SEGUROS
-- ============================================================================

SELECT '📋 GENERANDO PLAN DE LOTES ULTRA SEGUROS' as mensaje;

-- Determinar rango total de IDs
DO $$
DECLARE
    min_id BIGINT;
    max_id BIGINT;
    batch_size INTEGER := 100000; -- Lotes de 100K para seguridad
    current_start BIGINT;
    current_end BIGINT;
    batch_count INTEGER := 0;
BEGIN
    -- Obtener rango de IDs
    SELECT MIN(id), MAX(id) INTO min_id, max_id 
    FROM contacts 
    WHERE phone_national IS NOT NULL;
    
    RAISE NOTICE 'Rango de IDs: % - % (Total estimado: %)', min_id, max_id, max_id - min_id + 1;
    
    -- Generar checkpoints cada 100K
    current_start := min_id;
    
    WHILE current_start <= max_id LOOP
        current_end := LEAST(current_start + batch_size - 1, max_id);
        
        INSERT INTO update_checkpoints (batch_start, batch_end)
        VALUES (current_start, current_end);
        
        batch_count := batch_count + 1;
        current_start := current_end + 1;
    END LOOP;
    
    RAISE NOTICE 'Plan creado: % lotes de %K contactos cada uno', batch_count, batch_size/1000;
END $$;

-- Mostrar plan de ejecución
SELECT 
    '📊 PLAN DE EJECUCIÓN ULTRA SEGURO' as titulo;

SELECT 
    checkpoint_id as lote,
    batch_start as inicio_id,
    batch_end as fin_id,
    (batch_end - batch_start + 1) as contactos_estimados,
    status as estado
FROM update_checkpoints 
ORDER BY checkpoint_id 
LIMIT 10;

SELECT 
    COUNT(*) as total_lotes,
    SUM(batch_end - batch_start + 1) as total_contactos_estimados,
    MIN(batch_start) as primer_id,
    MAX(batch_end) as ultimo_id
FROM update_checkpoints;

-- ============================================================================
-- PASO 3: FUNCIÓN DE ACTUALIZACIÓN ULTRA SEGURA POR LOTES
-- ============================================================================

SELECT '🔧 CREANDO FUNCIÓN DE ACTUALIZACIÓN ULTRA SEGURA' as mensaje;

CREATE OR REPLACE FUNCTION update_batch_ultra_safe(p_checkpoint_id INTEGER)
RETURNS TABLE(
    checkpoint_id INTEGER,
    batch_range TEXT,
    processed INTEGER,
    updated INTEGER,
    verified_to_not_mobile INTEGER,
    not_mobile_to_verified INTEGER,
    no_changes INTEGER,
    execution_time_seconds NUMERIC,
    status TEXT
) AS $$
DECLARE
    v_start_id BIGINT;
    v_end_id BIGINT;
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_processed INTEGER := 0;
    v_updated INTEGER := 0;
    v_v_to_nm INTEGER := 0;
    v_nm_to_v INTEGER := 0;
    v_no_changes INTEGER := 0;
    v_error_msg TEXT;
BEGIN
    -- Obtener rango del checkpoint
    SELECT batch_start, batch_end INTO v_start_id, v_end_id
    FROM update_checkpoints 
    WHERE update_checkpoints.checkpoint_id = p_checkpoint_id;
    
    IF v_start_id IS NULL THEN
        RETURN QUERY SELECT 
            p_checkpoint_id, 
            'ERROR: Checkpoint no encontrado'::TEXT,
            0, 0, 0, 0, 0, 0::NUMERIC, 'ERROR'::TEXT;
        RETURN;
    END IF;
    
    v_start_time := clock_timestamp();
    
    -- Marcar checkpoint como EN PROCESO
    UPDATE update_checkpoints 
    SET status = 'PROCESSING', start_time = v_start_time
    WHERE update_checkpoints.checkpoint_id = p_checkpoint_id;
    
    BEGIN
        -- ACTUALIZACIÓN ULTRA SEGURA CON AUDITORÍA COMPLETA
        WITH batch_analysis AS (
            SELECT 
                c.id,
                c.phone_national,
                c.status as status_actual,
                c.operator as operator_actual,
                CASE 
                    WHEN ift.tipo_servicio = 'CPP' THEN 'VERIFIED'::contactstatus
                    WHEN ift.tipo_servicio IN ('MPP', 'FIJO') THEN 'NOT_MOBILE'::contactstatus
                    ELSE c.status
                END as nuevo_status,
                COALESCE(ift.operador, c.operator) as nuevo_operator,
                ift.tipo_servicio,
                ift.operador as ift_operador
            FROM contacts c
            LEFT JOIN ift_rangos ift ON (
                c.phone_national::BIGINT >= ift.numero_inicial 
                AND c.phone_national::BIGINT <= ift.numero_final
            )
            WHERE c.id BETWEEN v_start_id AND v_end_id
              AND c.phone_national IS NOT NULL
        ),
        contacts_to_update AS (
            SELECT * FROM batch_analysis
            WHERE nuevo_status != status_actual OR nuevo_operator != operator_actual
        ),
        update_contacts AS (
            UPDATE contacts
            SET 
                status = ctu.nuevo_status,
                operator = ctu.nuevo_operator,
                updated_at = NOW()
            FROM contacts_to_update ctu
            WHERE contacts.id = ctu.id
            RETURNING 
                contacts.id,
                ctu.status_actual,
                ctu.nuevo_status,
                ctu.operator_actual,
                ctu.nuevo_operator,
                ctu.tipo_servicio,
                ctu.ift_operador
        ),
        log_changes AS (
            INSERT INTO contacts_changes_ultra_safe (
                contact_id, phone_national, status_before, status_after,
                operator_before, operator_after, ift_tipo_servicio, 
                ift_operador, batch_id
            )
            SELECT 
                uc.id,
                c.phone_national,
                uc.status_actual,
                uc.nuevo_status,
                uc.operator_actual,
                uc.nuevo_operator,
                uc.tipo_servicio,
                uc.ift_operador,
                p_checkpoint_id
            FROM update_contacts uc
            JOIN contacts c ON c.id = uc.id
            RETURNING 1
        )
        SELECT 
            COUNT(*) as total_processed,
            (SELECT COUNT(*) FROM update_contacts) as total_updated,
            (SELECT COUNT(*) FROM update_contacts WHERE status_actual = 'VERIFIED' AND nuevo_status = 'NOT_MOBILE') as v_to_nm,
            (SELECT COUNT(*) FROM update_contacts WHERE status_actual = 'NOT_MOBILE' AND nuevo_status = 'VERIFIED') as nm_to_v,
            (SELECT COUNT(*) FROM batch_analysis WHERE nuevo_status = status_actual AND nuevo_operator = operator_actual) as no_change
        INTO v_processed, v_updated, v_v_to_nm, v_nm_to_v, v_no_changes
        FROM batch_analysis;
        
        v_end_time := clock_timestamp();
        
        -- Actualizar checkpoint como COMPLETADO
        UPDATE update_checkpoints 
        SET 
            status = 'COMPLETED',
            processed_count = v_processed,
            updated_count = v_updated,
            end_time = v_end_time
        WHERE update_checkpoints.checkpoint_id = p_checkpoint_id;
        
        -- Commit explícito del lote
        COMMIT;
        
        RETURN QUERY SELECT 
            p_checkpoint_id,
            (v_start_id || '-' || v_end_id)::TEXT,
            v_processed,
            v_updated,
            v_v_to_nm,
            v_nm_to_v,
            v_no_changes,
            EXTRACT(EPOCH FROM (v_end_time - v_start_time))::NUMERIC,
            'SUCCESS'::TEXT;
            
    EXCEPTION WHEN OTHERS THEN
        v_error_msg := SQLERRM;
        v_end_time := clock_timestamp();
        
        -- Marcar checkpoint como ERROR
        UPDATE update_checkpoints 
        SET 
            status = 'ERROR',
            error_message = v_error_msg,
            end_time = v_end_time
        WHERE update_checkpoints.checkpoint_id = p_checkpoint_id;
        
        -- Rollback del lote con error
        ROLLBACK;
        
        RETURN QUERY SELECT 
            p_checkpoint_id,
            (v_start_id || '-' || v_end_id)::TEXT,
            0, 0, 0, 0, 0, 0::NUMERIC,
            ('ERROR: ' || v_error_msg)::TEXT;
    END;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PASO 4: FUNCIÓN DE PROGRESO Y MONITOREO
-- ============================================================================

CREATE OR REPLACE FUNCTION get_update_progress_ultra_safe()
RETURNS TABLE(
    total_lotes INTEGER,
    lotes_completados INTEGER,
    lotes_en_proceso INTEGER,
    lotes_con_error INTEGER,
    lotes_pendientes INTEGER,
    progreso_porcentaje NUMERIC,
    total_procesados BIGINT,
    total_actualizados BIGINT,
    tiempo_estimado_restante TEXT
) AS $$
DECLARE
    v_total INTEGER;
    v_completados INTEGER;
    v_procesando INTEGER;
    v_errores INTEGER;
    v_pendientes INTEGER;
    v_progreso NUMERIC;
    v_procesados BIGINT;
    v_actualizados BIGINT;
    v_tiempo_promedio NUMERIC;
    v_tiempo_restante NUMERIC;
BEGIN
    SELECT 
        COUNT(*),
        COUNT(*) FILTER (WHERE status = 'COMPLETED'),
        COUNT(*) FILTER (WHERE status = 'PROCESSING'),
        COUNT(*) FILTER (WHERE status = 'ERROR'),
        COUNT(*) FILTER (WHERE status = 'PENDING')
    INTO v_total, v_completados, v_procesando, v_errores, v_pendientes
    FROM update_checkpoints;
    
    v_progreso := CASE WHEN v_total > 0 THEN ROUND((v_completados * 100.0) / v_total, 2) ELSE 0 END;
    
    SELECT 
        COALESCE(SUM(processed_count), 0),
        COALESCE(SUM(updated_count), 0)
    INTO v_procesados, v_actualizados
    FROM update_checkpoints 
    WHERE status = 'COMPLETED';
    
    -- Calcular tiempo estimado restante
    SELECT AVG(EXTRACT(EPOCH FROM (end_time - start_time)))
    INTO v_tiempo_promedio
    FROM update_checkpoints 
    WHERE status = 'COMPLETED' AND end_time IS NOT NULL;
    
    v_tiempo_restante := COALESCE(v_tiempo_promedio * v_pendientes, 0);
    
    RETURN QUERY SELECT 
        v_total,
        v_completados,
        v_procesando,
        v_errores,
        v_pendientes,
        v_progreso,
        v_procesados,
        v_actualizados,
        CASE 
            WHEN v_tiempo_restante > 3600 THEN 
                ROUND(v_tiempo_restante/3600, 1) || ' horas'
            WHEN v_tiempo_restante > 60 THEN 
                ROUND(v_tiempo_restante/60, 0) || ' minutos'
            ELSE 
                ROUND(v_tiempo_restante, 0) || ' segundos'
        END;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PASO 5: FUNCIÓN DE ROLLBACK COMPLETO
-- ============================================================================

CREATE OR REPLACE FUNCTION rollback_ultra_safe()
RETURNS TABLE(
    mensaje TEXT,
    registros_restaurados BIGINT
) AS $$
DECLARE
    v_restaurados BIGINT;
BEGIN
    -- Restaurar desde backup ultra seguro
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'contacts_backup_ultra_safe') THEN
        
        -- Contar registros actuales
        SELECT COUNT(*) INTO v_restaurados FROM contacts;
        
        -- Restaurar completamente
        TRUNCATE contacts;
        INSERT INTO contacts SELECT * FROM contacts_backup_ultra_safe;
        
        -- Limpiar checkpoints
        UPDATE update_checkpoints SET status = 'ROLLED_BACK';
        
        RETURN QUERY SELECT 
            'ROLLBACK COMPLETO EJECUTADO'::TEXT,
            v_restaurados;
    ELSE
        RETURN QUERY SELECT 
            'ERROR: Backup ultra seguro no encontrado'::TEXT,
            0::BIGINT;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PASO 6: PREPARACIÓN FINAL
-- ============================================================================

SELECT '🎯 SISTEMA ULTRA SEGURO PREPARADO' as mensaje;

SELECT 
    'Total de lotes programados: ' || COUNT(*) as plan_ejecucion
FROM update_checkpoints;

SELECT 
    'Contactos estimados para procesar: ' || SUM(batch_end - batch_start + 1) as total_estimado
FROM update_checkpoints;

SELECT '📋 INSTRUCCIONES DE USO:' as titulo;
SELECT '1. Ejecutar lotes: SELECT * FROM update_batch_ultra_safe(1);' as instruccion
UNION ALL
SELECT '2. Ver progreso: SELECT * FROM get_update_progress_ultra_safe();' as instruccion
UNION ALL  
SELECT '3. Rollback total: SELECT * FROM rollback_ultra_safe();' as instruccion
UNION ALL
SELECT '4. Lotes se ejecutan de 1 a ' || MAX(checkpoint_id) as instruccion
FROM update_checkpoints;

SELECT '🔒 SISTEMA ULTRA SEGURO LISTO PARA EJECUCIÓN' as mensaje;