-- =====================================================
-- SCRIPT: Crear tabla de números de validación
-- Propósito: Almacenar números hardcodeados para validar 
--           recepción de campañas SMS
-- Fecha: 2025-01-10
-- =====================================================

-- Crear tabla de números de validación
CREATE TABLE IF NOT EXISTS validation_numbers (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(15) NOT NULL UNIQUE,
    description VARCHAR(100) DEFAULT 'Número de validación de campañas SMS',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    
    -- Metadatos adicionales
    lada VARCHAR(3) GENERATED ALWAYS AS (SUBSTRING(phone_number, 1, 3)) STORED,
    state_validation VARCHAR(20) DEFAULT 'VALIDACION',
    municipality_validation VARCHAR(20) DEFAULT 'VALIDACION'
);

-- Crear índices para optimización
CREATE INDEX IF NOT EXISTS idx_validation_numbers_active ON validation_numbers(is_active);
CREATE INDEX IF NOT EXISTS idx_validation_numbers_phone ON validation_numbers(phone_number);
CREATE INDEX IF NOT EXISTS idx_validation_numbers_lada ON validation_numbers(lada);
CREATE INDEX IF NOT EXISTS idx_validation_numbers_usage ON validation_numbers(usage_count);

-- Insertar los 25 números hardcodeados
INSERT INTO validation_numbers (phone_number, description) VALUES 
('526674355781', 'Número de validación #1 - Campaña SMS'),
('526679827455', 'Número de validación #2 - Campaña SMS'),
('526672382990', 'Número de validación #3 - Campaña SMS'),
('526671305264', 'Número de validación #4 - Campaña SMS'),
('526678474107', 'Número de validación #5 - Campaña SMS'),
('526679637434', 'Número de validación #6 - Campaña SMS'),
('526674358223', 'Número de validación #7 - Campaña SMS'),
('526679073419', 'Número de validación #8 - Campaña SMS'),
('526679073282', 'Número de validación #9 - Campaña SMS'),
('526678223874', 'Número de validación #10 - Campaña SMS'),
('526678643713', 'Número de validación #11 - Campaña SMS'),
('526673775171', 'Número de validación #12 - Campaña SMS'),
('526673822551', 'Número de validación #13 - Campaña SMS'),
('526677946440', 'Número de validación #14 - Campaña SMS'),
('526671489540', 'Número de validación #15 - Campaña SMS'),
('526679584431', 'Número de validación #16 - Campaña SMS'),
('526679584435', 'Número de validación #17 - Campaña SMS'),
('526673737165', 'Número de validación #18 - Campaña SMS'),
('526679584393', 'Número de validación #19 - Campaña SMS'),
('526674373669', 'Número de validación #20 - Campaña SMS'),
('526671556397', 'Número de validación #21 - Campaña SMS'),
('526679637352', 'Número de validación #22 - Campaña SMS'),
('526678642322', 'Número de validación #23 - Campaña SMS'),
('526673723504', 'Número de validación #24 - Campaña SMS'),
('526674355241', 'Número de validación #25 - Campaña SMS')
ON CONFLICT (phone_number) DO UPDATE SET
    description = EXCLUDED.description,
    is_active = TRUE;

-- Verificar inserción
SELECT 
    COUNT(*) as total_numeros,
    COUNT(CASE WHEN is_active THEN 1 END) as activos,
    MIN(created_at) as primer_registro,
    MAX(created_at) as ultimo_registro
FROM validation_numbers;

-- Mostrar muestra de números insertados
SELECT 
    id,
    phone_number,
    lada,
    state_validation,
    municipality_validation,
    is_active,
    created_at
FROM validation_numbers 
ORDER BY id 
LIMIT 10;

-- Crear vista para consultas rápidas
CREATE OR REPLACE VIEW v_active_validation_numbers AS
SELECT 
    id,
    phone_number,
    lada,
    state_validation as state_name,
    municipality_validation as municipality,
    usage_count,
    last_used,
    created_at
FROM validation_numbers 
WHERE is_active = TRUE
ORDER BY usage_count ASC, RANDOM();

COMMENT ON TABLE validation_numbers IS 'Números hardcodeados para validar recepción de campañas SMS';
COMMENT ON VIEW v_active_validation_numbers IS 'Vista de números de validación activos ordenados por uso';

-- Script completado exitosamente
SELECT 'Tabla validation_numbers creada exitosamente con ' || COUNT(*) || ' números' as resultado
FROM validation_numbers;
