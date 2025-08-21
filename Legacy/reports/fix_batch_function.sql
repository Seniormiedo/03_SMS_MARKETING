-- CORRECCIÓN DE LA FUNCIÓN BATCH PARA MANEJAR ENUM contactstatus

-- Primero, ver qué tipo de enum es
SELECT 'Verificando tipo de status' as mensaje;
SELECT column_name, data_type, udt_name 
FROM information_schema.columns 
WHERE table_name = 'contacts' AND column_name = 'status';

-- Función corregida para manejar el enum contactstatus
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
    -- Procesar lote con conversiones explícitas de tipo
    WITH batch_updates AS (
        SELECT 
            c.id,
            c.phone_national,
            c.status::TEXT as status_actual,
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
                THEN bu.nuevo_status::contactstatus
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
               (bu.encontrado = TRUE AND bu.operador_ift IS DISTINCT FROM bu.operator_actual))
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
        COUNT(*)::INTEGER as total_processed,
        (SELECT COUNT(*)::INTEGER FROM contact_updates) as total_updated,
        (SELECT COUNT(*)::INTEGER FROM contact_updates WHERE status_actual = 'VERIFIED' AND nuevo_status = 'NOT_MOBILE') as v_to_nm_count,
        (SELECT COUNT(*)::INTEGER FROM contact_updates WHERE status_actual = 'NOT_MOBILE' AND nuevo_status = 'VERIFIED') as nm_to_v_count,
        (SELECT COUNT(*)::INTEGER FROM batch_updates WHERE nuevo_status = status_actual) as no_change_count,
        (SELECT COUNT(*)::INTEGER FROM batch_updates WHERE encontrado = FALSE) as not_found_count
    FROM batch_updates
    INTO proc_count, upd_count, v_to_nm, nm_to_v, no_change, not_found_count;
    
    RETURN QUERY SELECT proc_count, upd_count, v_to_nm, nm_to_v, no_change, not_found_count;
END;
$$ LANGUAGE plpgsql;