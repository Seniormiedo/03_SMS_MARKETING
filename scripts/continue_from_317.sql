-- Continuación automática desde lote 317 hasta 733 (lotes de 50,000 IDs)
\timing on
DO $$
DECLARE
    batch_start BIGINT := 15800001; -- Inicio de 317
    batch_end   BIGINT;
    max_id      BIGINT := (SELECT MAX(id) FROM contacts);
    batch_size  BIGINT := 50000;
    lote_num    INT := 317;
BEGIN
    WHILE batch_start <= max_id LOOP
        batch_end := LEAST(batch_start + batch_size - 1, max_id);

        RAISE NOTICE '🔄 Ejecutando lote % (IDs % - %)', lote_num, batch_start, batch_end;

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
            WHERE c.id BETWEEN batch_start AND batch_end
              AND c.phone_national IS NOT NULL
        ),
        contacts_to_update AS (
            SELECT * FROM batch_updates
            WHERE nuevo_status <> status_actual OR nuevo_operator <> operator_actual
        )
        UPDATE contacts
           SET status = ctu.nuevo_status,
               operator = ctu.nuevo_operator,
               updated_at = NOW()
          FROM contacts_to_update ctu
         WHERE contacts.id = ctu.id;

        RAISE NOTICE '✅ Lote % completado', lote_num;

        batch_start := batch_end + 1;
        lote_num := lote_num + 1;
    END LOOP;
END $$;

