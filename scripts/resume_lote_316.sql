-- Reanudar actualización: LOTE 316 (IDs 15,750,001 - 15,800,000)
\timing on
WITH batch_updates AS (
    SELECT 
        c.id,
        c.phone_national,
        c.status AS status_actual,
        c.operator AS operator_actual,
        CASE 
            WHEN ift.tipo_servicio = 'CPP' THEN 'VERIFIED'::contactstatus
            WHEN ift.tipo_servicio IN ('MPP','FIJO') THEN 'NOT_MOBILE'::contactstatus
            ELSE c.status
        END AS nuevo_status,
        LEFT(COALESCE(ift.operador, c.operator), 50) AS nuevo_operator,
        ift.tipo_servicio
    FROM contacts c
    LEFT JOIN ift_rangos ift 
      ON (c.phone_national::BIGINT >= ift.numero_inicial AND c.phone_national::BIGINT <= ift.numero_final)
    WHERE c.id BETWEEN 15750001 AND 15800000
      AND c.phone_national IS NOT NULL
),
contacts_to_update AS (
    SELECT * FROM batch_updates
    WHERE nuevo_status <> status_actual OR nuevo_operator <> operator_actual
),
update_result AS (
    UPDATE contacts
       SET status = ctu.nuevo_status,
           operator = ctu.nuevo_operator,
           updated_at = NOW()
      FROM contacts_to_update ctu
     WHERE contacts.id = ctu.id
  RETURNING contacts.id
)
SELECT 
    'LOTE 316' AS lote,
    COUNT(*) AS procesados,
    (SELECT COUNT(*) FROM update_result) AS actualizados,
    (SELECT COUNT(*) FROM contacts_to_update WHERE status_actual = 'NOT_MOBILE' AND nuevo_status = 'VERIFIED') AS nm_to_v,
    (SELECT COUNT(*) FROM contacts_to_update WHERE status_actual = 'VERIFIED' AND nuevo_status = 'NOT_MOBILE') AS v_to_nm
FROM batch_updates;

