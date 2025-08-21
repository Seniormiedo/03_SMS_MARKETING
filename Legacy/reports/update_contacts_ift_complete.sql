-- =====================================================
-- SCRIPT DE ACTUALIZACIÓN MASIVA CON RANGOS IFT
-- =====================================================
-- Actualiza TODOS los contactos (31.8M) con clasificación IFT oficial
-- CPP = MÓVILES (VERIFIED)
-- MPP + FIJO = FIJOS (NOT_MOBILE)

-- =====================================================
-- PASO 1: BACKUP Y PREPARACIÓN
-- =====================================================

-- Crear tabla de backup antes de la actualización
CREATE TABLE IF NOT EXISTS contacts_backup_pre_ift AS 
SELECT 
    id,
    phone_national,
    status,
    operator,
    updated_at,
    NOW() as backup_timestamp
FROM contacts 
WHERE phone_national IS NOT NULL 
  AND phone_national ~ '^[0-9]+$'
  AND length(phone_national::text) = 10;

-- Verificar backup
SELECT 'BACKUP CREADO' as mensaje, COUNT(*) as registros_backup FROM contacts_backup_pre_ift;

-- =====================================================
-- PASO 2: CREAR TABLA DE CAMBIOS PARA LOGGING
-- =====================================================

CREATE TABLE IF NOT EXISTS contacts_ift_changes (
    id SERIAL PRIMARY KEY,
    contact_id BIGINT,
    phone_national VARCHAR(15),
    status_anterior VARCHAR(20),
    status_nuevo VARCHAR(20),
    operator_anterior TEXT,
    operator_nuevo TEXT,
    tipo_servicio_ift VARCHAR(10),
    found_in_ift BOOLEAN,
    change_timestamp TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- PASO 3: ESTADÍSTICAS ANTES DE LA ACTUALIZACIÓN
-- =====================================================

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

-- =====================================================
-- PASO 4: FUNCIÓN OPTIMIZADA PARA ACTUALIZACIÓN MASIVA
-- =====================================================

-- Crear función optimizada que devuelve solo los datos necesarios
CREATE OR REPLACE FUNCTION get_ift_classification(numero_telefono BIGINT)
RETURNS TABLE(
    nuevo_status VARCHAR(20),
    operador_ift TEXT,
    tipo_servicio VARCHAR(10),
    encontrado BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE 
            WHEN r.tipo_servicio = 'CPP' THEN 'VERIFIED'::VARCHAR(20)
            WHEN r.tipo_servicio IN ('MPP', 'FIJO') THEN 'NOT_MOBILE'::VARCHAR(20)
            ELSE 'UNKNOWN'::VARCHAR(20)
        END as nuevo_status,
        r.operador as operador_ift,
        r.tipo_servicio,
        TRUE as encontrado
    FROM ift_rangos r
    WHERE numero_telefono >= r.numero_inicial 
      AND numero_telefono <= r.numero_final
    LIMIT 1;
    
    -- Si no se encuentra, mantener status actual
    IF NOT FOUND THEN
        RETURN QUERY SELECT 'NO_CHANGE'::VARCHAR(20), 'UNKNOWN'::TEXT, 'UNKNOWN'::VARCHAR(10), FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- PASO 5: ACTUALIZACIÓN POR LOTES (BATCH PROCESSING)
-- =====================================================

-- Crear función para procesar lotes
CREATE OR REPLACE FUNCTION update_contacts_batch(
    batch_start BIGINT,
    batch_end BIGINT
) RETURNS TABLE(
    processed INTEGER,
    updated INTEGER,
    verified_to_not_mobile INTEGER,
    not_mobile_to_verified INTEGER,
    no_changes INTEGER,
    not_found INTEGER
) AS $$
DECLARE
    proc_count INTEGER := 0;
    upd_count INTEGER := 0;
    v_to_nm INTEGER := 0;
    nm_to_v INTEGER := 0;
    no_change INTEGER := 0;
    not_found_count INTEGER := 0;
BEGIN
    -- Procesar lote
    WITH batch_updates AS (
        SELECT 
            c.id,
            c.phone_national,
            c.status as status_actual,
            c.operator as operator_actual,
            ift.nuevo_status,
            ift.operador_ift,
            ift.tipo_servicio,
            ift.encontrado
        FROM contacts c
        CROSS JOIN LATERAL get_ift_classification(c.phone_national::BIGINT) ift
        WHERE c.id BETWEEN batch_start AND batch_end
          AND c.phone_national IS NOT NULL 
          AND c.phone_national ~ '^[0-9]+$'
          AND length(c.phone_national::text) = 10
    ),
    contact_updates AS (
        UPDATE contacts 
        SET 
            status = CASE 
                WHEN bu.nuevo_status != 'NO_CHANGE' AND bu.nuevo_status != bu.status_actual 
                THEN bu.nuevo_status 
                ELSE status 
            END,
            operator = CASE 
                WHEN bu.encontrado = TRUE AND bu.operador_ift IS NOT NULL 
                THEN bu.operador_ift 
                ELSE operator 
            END,
            updated_at = NOW()
        FROM batch_updates bu
        WHERE contacts.id = bu.id
          AND (bu.nuevo_status != bu.status_actual OR 
               (bu.encontrado = TRUE AND bu.operador_ift != bu.operator_actual))
        RETURNING 
            contacts.id,
            bu.status_actual,
            bu.nuevo_status,
            bu.operator_actual,
            bu.operador_ift,
            bu.tipo_servicio,
            bu.encontrado
    ),
    log_changes AS (
        INSERT INTO contacts_ift_changes (
            contact_id, phone_national, status_anterior, status_nuevo, 
            operator_anterior, operator_nuevo, tipo_servicio_ift, found_in_ift
        )
        SELECT 
            cu.id,
            c.phone_national,
            cu.status_actual,
            cu.nuevo_status,
            cu.operator_actual,
            cu.operador_ift,
            cu.tipo_servicio,
            cu.encontrado
        FROM contact_updates cu
        JOIN contacts c ON c.id = cu.id
        RETURNING 1
    )
    SELECT 
        COUNT(*) as total_processed,
        (SELECT COUNT(*) FROM contact_updates) as total_updated,
        (SELECT COUNT(*) FROM contact_updates WHERE status_actual = 'VERIFIED' AND nuevo_status = 'NOT_MOBILE') as v_to_nm_count,
        (SELECT COUNT(*) FROM contact_updates WHERE status_actual = 'NOT_MOBILE' AND nuevo_status = 'VERIFIED') as nm_to_v_count,
        (SELECT COUNT(*) FROM batch_updates WHERE nuevo_status = status_actual) as no_change_count,
        (SELECT COUNT(*) FROM batch_updates WHERE encontrado = FALSE) as not_found_count
    FROM batch_updates
    INTO proc_count, upd_count, v_to_nm, nm_to_v, no_change, not_found_count;
    
    RETURN QUERY SELECT proc_count, upd_count, v_to_nm, nm_to_v, no_change, not_found_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- PASO 6: SCRIPT DE EJECUCIÓN POR LOTES
-- =====================================================

-- Obtener rango de IDs para procesamiento
SELECT '=== RANGO DE IDS PARA PROCESAMIENTO ===' as titulo;
SELECT 
    MIN(id) as min_id,
    MAX(id) as max_id,
    COUNT(*) as total_contacts
FROM contacts
WHERE phone_national IS NOT NULL 
  AND phone_national ~ '^[0-9]+$'
  AND length(phone_national::text) = 10;

-- =====================================================
-- PASO 7: EJECUTAR ACTUALIZACIÓN EN LOTES DE 100K
-- =====================================================

-- Nota: Este script debe ejecutarse por lotes para evitar timeouts
-- Ejemplo de ejecución por lotes (ajustar según el rango real):

/*
EJEMPLO DE EJECUCIÓN POR LOTES:

-- Lote 1: IDs 1-100000
SELECT 'PROCESANDO LOTE 1 (1-100000)' as mensaje;
SELECT * FROM update_contacts_batch(1, 100000);

-- Lote 2: IDs 100001-200000
SELECT 'PROCESANDO LOTE 2 (100001-200000)' as mensaje;
SELECT * FROM update_contacts_batch(100001, 200000);

-- Continuar hasta completar todos los IDs...
*/

-- =====================================================
-- PASO 8: FUNCIONES DE MONITOREO
-- =====================================================

-- Función para ver progreso de actualización
CREATE OR REPLACE FUNCTION get_update_progress()
RETURNS TABLE(
    total_contacts BIGINT,
    contacts_processed BIGINT,
    percentage_complete NUMERIC,
    verified_count BIGINT,
    not_mobile_count BIGINT,
    changes_made BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM contacts WHERE phone_national IS NOT NULL) as total,
        (SELECT COUNT(*) FROM contacts_ift_changes) as processed,
        ROUND((SELECT COUNT(*) FROM contacts_ift_changes) * 100.0 / 
              (SELECT COUNT(*) FROM contacts WHERE phone_national IS NOT NULL), 2) as pct,
        (SELECT COUNT(*) FROM contacts WHERE status = 'VERIFIED') as verified,
        (SELECT COUNT(*) FROM contacts WHERE status = 'NOT_MOBILE') as not_mobile,
        (SELECT COUNT(*) FROM contacts_ift_changes WHERE status_anterior != status_nuevo) as changes;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- PASO 9: VERIFICACIÓN POST-ACTUALIZACIÓN
-- =====================================================

-- Script de verificación (ejecutar después de completar todos los lotes)
CREATE OR REPLACE FUNCTION verify_ift_update()
RETURNS TABLE(
    verification_step TEXT,
    result TEXT,
    count_value BIGINT
) AS $$
BEGIN
    -- Total de contactos actualizados
    RETURN QUERY
    SELECT 'Total contactos procesados' as step, 
           'OK' as result, 
           COUNT(*)::BIGINT as count_val
    FROM contacts_ift_changes;
    
    -- Distribución final por status
    RETURN QUERY
    SELECT 'VERIFIED final' as step,
           'Count' as result,
           COUNT(*)::BIGINT as count_val
    FROM contacts 
    WHERE status = 'VERIFIED' 
      AND phone_national IS NOT NULL;
    
    RETURN QUERY
    SELECT 'NOT_MOBILE final' as step,
           'Count' as result,
           COUNT(*)::BIGINT as count_val
    FROM contacts 
    WHERE status = 'NOT_MOBILE' 
      AND phone_national IS NOT NULL;
    
    -- Cambios principales
    RETURN QUERY
    SELECT 'VERIFIED -> NOT_MOBILE' as step,
           'Changes' as result,
           COUNT(*)::BIGINT as count_val
    FROM contacts_ift_changes 
    WHERE status_anterior = 'VERIFIED' AND status_nuevo = 'NOT_MOBILE';
    
    RETURN QUERY
    SELECT 'NOT_MOBILE -> VERIFIED' as step,
           'Changes' as result,
           COUNT(*)::BIGINT as count_val
    FROM contacts_ift_changes 
    WHERE status_anterior = 'NOT_MOBILE' AND status_nuevo = 'VERIFIED';
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- PASO 10: PLAN DE ROLLBACK
-- =====================================================

-- Función de rollback (en caso de problemas)
CREATE OR REPLACE FUNCTION rollback_ift_update()
RETURNS TABLE(
    rollback_step TEXT,
    result TEXT,
    affected_rows BIGINT
) AS $$
DECLARE
    affected_count BIGINT;
BEGIN
    -- Restaurar desde backup
    UPDATE contacts 
    SET 
        status = backup.status,
        operator = backup.operator,
        updated_at = backup.updated_at
    FROM contacts_backup_pre_ift backup
    WHERE contacts.id = backup.id;
    
    GET DIAGNOSTICS affected_count = ROW_COUNT;
    
    RETURN QUERY
    SELECT 'Contacts restored' as step,
           'OK' as result,
           affected_count as affected;
    
    -- Limpiar tablas de cambios
    DELETE FROM contacts_ift_changes;
    
    RETURN QUERY
    SELECT 'Change log cleared' as step,
           'OK' as result,
           0::BIGINT as affected;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- INSTRUCCIONES DE USO
-- =====================================================

/*
INSTRUCCIONES PARA EJECUTAR LA ACTUALIZACIÓN MASIVA:

1. PREPARACIÓN:
   - Ejecutar este script completo para crear funciones
   - Verificar que el backup se creó correctamente

2. EJECUCIÓN POR LOTES:
   - Obtener rango de IDs con la consulta del PASO 6
   - Ejecutar update_contacts_batch() en lotes de 100K
   - Monitorear progreso con get_update_progress()

3. VERIFICACIÓN:
   - Ejecutar verify_ift_update() al finalizar
   - Revisar logs en contacts_ift_changes

4. ROLLBACK (si necesario):
   - Ejecutar rollback_ift_update()

EJEMPLO DE EJECUCIÓN:
SELECT * FROM update_contacts_batch(1, 100000);
SELECT * FROM get_update_progress();
*/

-- Mostrar mensaje final
SELECT '=== SCRIPT DE ACTUALIZACIÓN MASIVA PREPARADO ===' as mensaje;
SELECT 'Ejecutar por lotes usando update_contacts_batch(start_id, end_id)' as instruccion;