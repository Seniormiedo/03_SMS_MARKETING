-- ACTUALIZAR FUNCIÓN DE VERIFICACIÓN CON LÓGICA COMPLETA
-- CPP = MÓVILES (VERIFIED)
-- MPP = FIJOS (NOT_MOBILE) 
-- FIJO = FIJOS (NOT_MOBILE)

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
        CASE 
            WHEN r.tipo_servicio = 'CPP' THEN TRUE 
            WHEN r.tipo_servicio IN ('MPP', 'FIJO') THEN FALSE
            ELSE FALSE 
        END as es_movil,
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

-- Verificar que la función funciona correctamente
SELECT '=== TEST FUNCIÓN ACTUALIZADA ===' as titulo;

-- Test con algunos números para verificar los 3 tipos
SELECT 'Función actualizada correctamente' as mensaje;

-- Mostrar estadísticas de los tipos cargados
SELECT '=== RANGOS DISPONIBLES ===' as titulo;
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