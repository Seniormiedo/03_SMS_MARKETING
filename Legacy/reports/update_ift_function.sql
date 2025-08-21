-- Actualizar función de verificación IFT con lógica correcta
-- CPP = MÓVILES (VERIFIED)
-- MPP/FPP = FIJOS (NOT_MOBILE)

CREATE OR REPLACE FUNCTION verificar_numero_ift(numero_telefono BIGINT)
RETURNS TABLE(
    es_movil BOOLEAN,
    operador TEXT,
    tipo_servicio VARCHAR(10),
    fecha_asignacion DATE,
    encontrado BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE WHEN r.tipo_servicio = 'CPP' THEN TRUE ELSE FALSE END as es_movil,
        r.operador,
        r.tipo_servicio,
        r.fecha_asignacion,
        TRUE as encontrado
    FROM ift_rangos r
    WHERE numero_telefono >= r.numero_inicial 
      AND numero_telefono <= r.numero_final
    LIMIT 1;
    
    -- Si no se encuentra, devolver valores por defecto
    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'DESCONOCIDO'::TEXT, 'UNKNOWN'::VARCHAR(10), NULL::DATE, FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Test de la función con algunos números
SELECT 'Test función actualizada:' as mensaje;
SELECT * FROM verificar_numero_ift(5551234567);
SELECT * FROM verificar_numero_ift(8181234567);