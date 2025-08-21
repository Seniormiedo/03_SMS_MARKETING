-- ==========================================
-- ESTRATEGIA ÓPTIMA: ACTUALIZACIÓN MASIVA POR LADAS
-- ==========================================
-- Objetivo: Actualizar state_name y municipality de 31.8M contactos
-- basándose en la LADA usando datos del archivo LADAS2025.CSV
-- 
-- ESTRATEGIA: Tabla de referencia + UPDATE masivo con JOIN
-- Rendimiento estimado: ~5-10 minutos para 31.8M registros
-- ==========================================

-- PASO 1: Crear tabla de referencia para LADAs
DROP TABLE IF EXISTS ladas_reference CASCADE;

CREATE TABLE ladas_reference (
    lada VARCHAR(3) PRIMARY KEY,
    estado VARCHAR(50) NOT NULL,
    municipio VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear índice para optimizar JOINs
CREATE INDEX idx_ladas_reference_lada ON ladas_reference(lada);

-- PASO 2: Cargar datos del CSV (se hará vía COPY o INSERT)
-- Los datos se cargarán desde LADAS2025.CSV

-- PASO 3: Crear función de actualización masiva optimizada
CREATE OR REPLACE FUNCTION update_contacts_by_lada()
RETURNS TABLE(
    total_updated BIGINT,
    execution_time INTERVAL,
    ladas_matched INTEGER,
    ladas_not_found INTEGER
) 
LANGUAGE plpgsql AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    updated_count BIGINT;
    matched_ladas INTEGER;
    missing_ladas INTEGER;
BEGIN
    start_time := clock_timestamp();
    
    -- Contar LADAs que coinciden
    SELECT COUNT(DISTINCT c.lada) INTO matched_ladas
    FROM contacts c 
    INNER JOIN ladas_reference lr ON c.lada = lr.lada
    WHERE c.lada IS NOT NULL;
    
    -- Contar LADAs que NO coinciden
    SELECT COUNT(DISTINCT c.lada) INTO missing_ladas
    FROM contacts c 
    LEFT JOIN ladas_reference lr ON c.lada = lr.lada
    WHERE c.lada IS NOT NULL AND lr.lada IS NULL;
    
    -- Actualización masiva optimizada
    -- Usamos UPPER() para normalizar estados
    UPDATE contacts 
    SET 
        state_name = UPPER(TRIM(lr.estado)),
        municipality = UPPER(TRIM(lr.municipio)),
        updated_at = CURRENT_TIMESTAMP
    FROM ladas_reference lr 
    WHERE contacts.lada = lr.lada 
      AND contacts.lada IS NOT NULL;
    
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT 
        updated_count,
        end_time - start_time,
        matched_ladas,
        missing_ladas;
END;
$$;

-- PASO 4: Crear función para validar resultados
CREATE OR REPLACE FUNCTION validate_ladas_update()
RETURNS TABLE(
    lada_code VARCHAR(3),
    estado_csv VARCHAR(50),
    estado_bd VARCHAR(50),
    municipio_csv VARCHAR(100),
    municipio_bd VARCHAR(100),
    total_contacts BIGINT,
    match_estado BOOLEAN,
    match_municipio BOOLEAN
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT 
        lr.lada,
        lr.estado,
        c.state_name,
        lr.municipio,
        c.municipality,
        COUNT(c.id) as total_contacts,
        (UPPER(TRIM(lr.estado)) = UPPER(TRIM(c.state_name))) as match_estado,
        (UPPER(TRIM(lr.municipio)) = UPPER(TRIM(c.municipality))) as match_municipio
    FROM ladas_reference lr
    LEFT JOIN contacts c ON lr.lada = c.lada
    WHERE c.lada IS NOT NULL
    GROUP BY lr.lada, lr.estado, lr.municipio, c.state_name, c.municipality
    ORDER BY COUNT(c.id) DESC
    LIMIT 50;
END;
$$;

-- PASO 5: Crear índices adicionales para optimizar la actualización
-- (Solo si no existen)
CREATE INDEX IF NOT EXISTS idx_contacts_lada_state ON contacts(lada, state_name);
CREATE INDEX IF NOT EXISTS idx_contacts_updated_at ON contacts(updated_at);

-- PASO 6: Configuración de PostgreSQL para optimizar UPDATE masivo
-- Estas configuraciones se aplicarán durante la ejecución:
-- SET work_mem = '512MB';
-- SET maintenance_work_mem = '1GB';
-- SET synchronous_commit = OFF;
-- SET checkpoint_completion_target = 0.9;

-- ==========================================
-- COMANDOS DE EJECUCIÓN:
-- ==========================================
-- 1. Cargar CSV: \copy ladas_reference(lada,estado,municipio) FROM 'LADAS2025.CSV' CSV HEADER;
-- 2. Ejecutar: SELECT * FROM update_contacts_by_lada();
-- 3. Validar: SELECT * FROM validate_ladas_update();
-- ==========================================

-- ESTIMACIÓN DE RENDIMIENTO:
-- - Carga CSV: ~1 segundo (397 registros)
-- - UPDATE masivo: ~5-10 minutos (31.8M registros)
-- - Validación: ~30 segundos
-- TOTAL: ~10-15 minutos máximo
-- ==========================================
