#!/usr/bin/env python3
"""
CARGA ROBUSTA DE CSV - MANEJA ERRORES DE DATOS
Versión que tolera problemas en el CSV como campos faltantes
"""

import subprocess
import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

class CSVRobustLoader:
    """Cargador robusto de CSV que maneja errores de datos"""
    
    def __init__(self):
        self.start_time = None
        self.csv_path = "data/TELCEL2022.csv"
        
    def log_message(self, message, level="INFO"):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def create_flexible_raw_table(self):
        """Crear tabla raw flexible para CSV con problemas"""
        self.log_message("🏗️  Creando tabla raw flexible...")
        
        create_table_sql = """
-- Crear tabla raw flexible
DROP TABLE IF EXISTS raw_telcel_data CASCADE;

CREATE TABLE raw_telcel_data (
    id SERIAL PRIMARY KEY,
    phone TEXT,
    name TEXT,
    field3 TEXT,
    address TEXT,
    neighborhood TEXT,
    city TEXT,
    state_sep TEXT,
    municipality_sep TEXT,
    state_cof TEXT,
    municipality_cof TEXT,
    raw_line TEXT,
    line_number BIGINT,
    loaded_at TIMESTAMP DEFAULT NOW()
);

-- Crear índices
CREATE INDEX IF NOT EXISTS idx_raw_phone ON raw_telcel_data(phone);
CREATE INDEX IF NOT EXISTS idx_raw_state ON raw_telcel_data(state_sep);

SELECT 'Tabla raw_telcel_data creada exitosamente' as resultado;
"""
        
        try:
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', create_table_sql
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.log_message("✅ Tabla raw flexible creada")
                return True
            else:
                self.log_message(f"❌ Error creando tabla: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Error creando tabla: {e}", "ERROR")
            return False
    
    def load_csv_with_python_parser(self):
        """Cargar CSV usando parser Python para manejar errores"""
        self.log_message("🐍 Cargando CSV con parser Python robusto...")
        
        import csv
        import tempfile
        
        # Crear archivo SQL temporal para inserción por lotes
        temp_sql_path = tempfile.mktemp(suffix='.sql')
        
        try:
            processed_lines = 0
            error_lines = 0
            batch_size = 10000
            current_batch = []
            
            self.log_message("📖 Procesando archivo CSV...")
            
            with open(self.csv_path, 'r', encoding='utf-8', errors='replace') as csvfile:
                # Detectar delimitador
                sample = csvfile.read(1024)
                csvfile.seek(0)
                
                sniffer = csv.Sniffer()
                delimiter = ';'  # Ya sabemos que es punto y coma
                
                # Saltar header
                header = csvfile.readline()
                self.log_message(f"📋 Header: {header.strip()}")
                
                line_number = 1
                
                for line in csvfile:
                    line_number += 1
                    processed_lines += 1
                    
                    try:
                        # Limpiar línea
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Dividir por delimitador
                        fields = line.split(delimiter)
                        
                        # Asegurar que tenemos al menos los campos básicos
                        while len(fields) < 10:
                            fields.append('')
                        
                        # Limpiar campos
                        phone = fields[0].strip() if len(fields) > 0 else ''
                        name = fields[1].strip().replace("'", "''") if len(fields) > 1 else ''
                        field3 = fields[2].strip().replace("'", "''") if len(fields) > 2 else ''
                        address = fields[3].strip().replace("'", "''") if len(fields) > 3 else ''
                        neighborhood = fields[4].strip().replace("'", "''") if len(fields) > 4 else ''
                        city = fields[5].strip().replace("'", "''") if len(fields) > 5 else ''
                        state_sep = fields[6].strip().replace("'", "''") if len(fields) > 6 else ''
                        municipality_sep = fields[7].strip().replace("'", "''") if len(fields) > 7 else ''
                        state_cof = fields[8].strip().replace("'", "''") if len(fields) > 8 else ''
                        municipality_cof = fields[9].strip().replace("'", "''") if len(fields) > 9 else ''
                        raw_line = line.replace("'", "''")
                        
                        # Validar teléfono básico
                        if not phone or not phone.isdigit() or len(phone) != 10:
                            error_lines += 1
                            continue
                        
                        # Agregar a batch
                        insert_values = f"('{phone}', '{name}', '{field3}', '{address}', '{neighborhood}', '{city}', '{state_sep}', '{municipality_sep}', '{state_cof}', '{municipality_cof}', '{raw_line}', {line_number})"
                        current_batch.append(insert_values)
                        
                        # Procesar batch
                        if len(current_batch) >= batch_size:
                            success = self.insert_batch(current_batch)
                            if success:
                                self.log_message(f"✅ Procesadas {processed_lines:,} líneas ({error_lines:,} errores)")
                            current_batch = []
                    
                    except Exception as e:
                        error_lines += 1
                        if error_lines <= 10:  # Solo mostrar primeros 10 errores
                            self.log_message(f"⚠️  Error línea {line_number}: {str(e)[:100]}", "WARNING")
                        continue
                    
                    # Progreso cada 100K líneas
                    if processed_lines % 100000 == 0:
                        self.log_message(f"📊 Progreso: {processed_lines:,} líneas procesadas")
            
            # Procesar último batch
            if current_batch:
                self.insert_batch(current_batch)
            
            self.log_message(f"✅ Procesamiento completado:")
            self.log_message(f"   📊 Total líneas: {processed_lines:,}")
            self.log_message(f"   ❌ Líneas con error: {error_lines:,}")
            self.log_message(f"   ✅ Líneas válidas: {processed_lines - error_lines:,}")
            
            return True
            
        except Exception as e:
            self.log_message(f"❌ Error procesando CSV: {e}", "ERROR")
            return False
    
    def insert_batch(self, batch_values):
        """Insertar lote de registros"""
        if not batch_values:
            return True
        
        insert_sql = f"""
INSERT INTO raw_telcel_data (
    phone, name, field3, address, neighborhood, city,
    state_sep, municipality_sep, state_cof, municipality_cof,
    raw_line, line_number
) VALUES {', '.join(batch_values)};
"""
        
        try:
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', insert_sql
            ], capture_output=True, text=True, timeout=120)
            
            return result.returncode == 0
            
        except Exception as e:
            self.log_message(f"⚠️  Error insertando batch: {e}", "WARNING")
            return False
    
    def create_transformation_functions_simple(self):
        """Crear funciones de transformación simplificadas"""
        self.log_message("🔧 Creando funciones de transformación...")
        
        transformation_sql = """
-- Función para normalizar números de teléfono simplificada
CREATE OR REPLACE FUNCTION normalize_phone_simple(phone_raw TEXT) 
RETURNS TABLE(
    phone_e164 TEXT,
    phone_national TEXT,
    is_mobile BOOLEAN,
    lada TEXT
) AS $$
BEGIN
    -- Limpiar número
    phone_raw := regexp_replace(phone_raw, '[^0-9]', '', 'g');
    
    -- Validar longitud
    IF length(phone_raw) != 10 THEN
        RETURN;
    END IF;
    
    -- Extraer LADA (primeros 3 dígitos)
    lada := substring(phone_raw, 1, 3);
    
    -- Determinar si es móvil (LADAs móviles comunes)
    is_mobile := lada IN ('55', '33', '81', '222', '228', '229', '664', '662', '668', '669', '686', '687', '688', '689');
    
    -- Formatear E.164
    phone_e164 := '+52' || phone_raw;
    
    -- Formatear nacional
    phone_national := phone_raw;
    
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- Función para limpiar texto
CREATE OR REPLACE FUNCTION clean_text_simple(input_text TEXT) 
RETURNS TEXT AS $$
BEGIN
    IF input_text IS NULL OR trim(input_text) = '' THEN
        RETURN NULL;
    END IF;
    
    -- Limpiar y normalizar
    input_text := trim(upper(input_text));
    input_text := regexp_replace(input_text, '\\s+', ' ', 'g');
    
    -- Remover caracteres problemáticos
    input_text := regexp_replace(input_text, '[^A-Z0-9 ÑÁÉÍÓÚÜñáéíóúü.,#-]', '', 'g');
    
    RETURN input_text;
END;
$$ LANGUAGE plpgsql;

-- Función para mapear estados simplificada
CREATE OR REPLACE FUNCTION map_state_simple(state_name TEXT) 
RETURNS TEXT AS $$
BEGIN
    state_name := upper(trim(state_name));
    
    RETURN CASE 
        WHEN state_name LIKE '%BCS%' OR state_name LIKE '%BAJA CALIFORNIA SUR%' THEN 'BCS'
        WHEN state_name LIKE '%BC%' OR state_name LIKE '%BAJA CALIFORNIA%' THEN 'BC'
        WHEN state_name LIKE '%CDMX%' OR state_name LIKE '%DF%' OR state_name LIKE '%MEXICO%' THEN 'CDMX'
        WHEN state_name LIKE '%NL%' OR state_name LIKE '%NUEVO LEON%' THEN 'NL'
        WHEN state_name LIKE '%JAL%' OR state_name LIKE '%JALISCO%' THEN 'JAL'
        WHEN state_name LIKE '%VER%' OR state_name LIKE '%VERACRUZ%' THEN 'VER'
        WHEN state_name LIKE '%PUE%' OR state_name LIKE '%PUEBLA%' THEN 'PUE'
        WHEN state_name LIKE '%GTO%' OR state_name LIKE '%GUANAJUATO%' THEN 'GTO'
        WHEN state_name LIKE '%CHIH%' OR state_name LIKE '%CHIHUAHUA%' THEN 'CHIH'
        WHEN state_name LIKE '%MICH%' OR state_name LIKE '%MICHOACAN%' THEN 'MICH'
        WHEN state_name LIKE '%OAX%' OR state_name LIKE '%OAXACA%' THEN 'OAX'
        WHEN state_name LIKE '%CHIS%' OR state_name LIKE '%CHIAPAS%' THEN 'CHIS'
        WHEN state_name LIKE '%TAMS%' OR state_name LIKE '%TAMAULIPAS%' THEN 'TAMS'
        WHEN state_name LIKE '%SIN%' OR state_name LIKE '%SINALOA%' THEN 'SIN'
        ELSE left(state_name, 10)
    END;
END;
$$ LANGUAGE plpgsql;

SELECT 'Funciones de transformación creadas exitosamente' as resultado;
"""
        
        try:
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', transformation_sql
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.log_message("✅ Funciones creadas exitosamente")
                return True
            else:
                self.log_message(f"❌ Error creando funciones: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Error creando funciones: {e}", "ERROR")
            return False
    
    def transform_and_load_final(self):
        """Transformar y cargar datos finales"""
        self.log_message("🔄 Transformando y cargando datos finales...")
        
        transform_sql = """
-- Limpiar tabla contacts
TRUNCATE TABLE contacts RESTART IDENTITY CASCADE;

-- Insertar datos transformados desde raw_telcel_data
INSERT INTO contacts (
    phone_e164, phone_national, phone_original, full_name, address, neighborhood,
    lada, state_code, state_name, municipality, city, is_mobile, operator,
    status, source, created_at, updated_at, send_count, validation_attempts
)
SELECT 
    np.phone_e164,
    np.phone_national,
    r.phone as phone_original,
    clean_text_simple(r.name) as full_name,
    clean_text_simple(r.address) as address,
    clean_text_simple(r.neighborhood) as neighborhood,
    np.lada,
    map_state_simple(r.state_sep) as state_code,
    clean_text_simple(r.state_sep) as state_name,
    clean_text_simple(r.municipality_sep) as municipality,
    clean_text_simple(r.city) as city,
    np.is_mobile,
    CASE WHEN np.is_mobile THEN 'Telcel' ELSE 'Telmex' END as operator,
    CASE WHEN np.is_mobile THEN 'VERIFIED' ELSE 'NOT_MOBILE' END as status,
    'TELCEL2022' as source,
    NOW() as created_at,
    NOW() as updated_at,
    0 as send_count,
    0 as validation_attempts
FROM raw_telcel_data r
CROSS JOIN LATERAL normalize_phone_simple(r.phone) np
WHERE np.phone_e164 IS NOT NULL
  AND r.phone IS NOT NULL
  AND length(r.phone) = 10
ON CONFLICT (phone_e164) DO NOTHING;

-- Estadísticas finales
SELECT 'Transformación completada' as resultado;
SELECT COUNT(*) as total_contacts FROM contacts;

SELECT 
    'Distribución por tipo' as analisis,
    is_mobile,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM contacts), 2) as porcentaje
FROM contacts 
GROUP BY is_mobile
ORDER BY is_mobile DESC;

SELECT 'Top 10 estados' as analisis;
SELECT state_code, COUNT(*) as cantidad 
FROM contacts 
WHERE state_code IS NOT NULL 
GROUP BY state_code 
ORDER BY COUNT(*) DESC 
LIMIT 10;
"""
        
        transform_start = time.time()
        
        try:
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', transform_sql
            ], capture_output=True, text=True, timeout=1800)  # 30 min timeout
            
            transform_time = time.time() - transform_start
            
            if result.returncode == 0:
                self.log_message(f"✅ Transformación completada en {transform_time/60:.1f} minutos")
                
                # Mostrar estadísticas del output
                self.log_message("📊 Estadísticas finales:")
                lines = result.stdout.split('\n')
                for line in lines:
                    if line.strip() and ('total_contacts' in line or 'cantidad' in line or 'porcentaje' in line or line.strip().isdigit()):
                        self.log_message(f"   {line.strip()}")
                
                return True
            else:
                self.log_message(f"❌ Error en transformación: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_message("❌ Timeout en transformación (>30 min)", "ERROR")
            return False
        except Exception as e:
            self.log_message(f"❌ Error en transformación: {e}", "ERROR")
            return False
    
    def get_final_statistics(self):
        """Obtener estadísticas finales"""
        self.log_message("📊 Obteniendo estadísticas finales...")
        
        stats_sql = """
SELECT 
    'ESTADÍSTICAS FINALES' as titulo,
    COUNT(*) as total_registros,
    COUNT(CASE WHEN is_mobile THEN 1 END) as moviles,
    COUNT(CASE WHEN NOT is_mobile THEN 1 END) as fijos,
    COUNT(DISTINCT state_code) as estados_unicos,
    COUNT(DISTINCT lada) as ladas_unicas
FROM contacts;

-- Top 5 estados
SELECT 'Top 5 Estados:' as ranking, state_code, COUNT(*) as registros
FROM contacts 
WHERE state_code IS NOT NULL 
GROUP BY state_code 
ORDER BY COUNT(*) DESC 
LIMIT 5;
"""
        
        try:
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', stats_sql
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.log_message("📈 Estadísticas finales:")
                lines = result.stdout.split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('-') and '|' in line:
                        self.log_message(f"   {line.strip()}")
        except Exception as e:
            self.log_message(f"⚠️  Error obteniendo estadísticas: {e}", "WARNING")
    
    def cleanup_raw_data(self):
        """Limpiar datos raw"""
        self.log_message("🧹 Limpiando datos temporales...")
        
        try:
            cleanup_sql = "DROP TABLE IF EXISTS raw_telcel_data CASCADE; VACUUM ANALYZE contacts;"
            
            subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', cleanup_sql
            ], capture_output=True, text=True, timeout=300)
            
            self.log_message("✅ Limpieza completada")
        except Exception as e:
            self.log_message(f"⚠️  Error en limpieza: {e}", "WARNING")
    
    def execute_robust_csv_load(self):
        """Ejecutar carga robusta completa"""
        self.start_time = time.time()
        
        self.log_message("🚀 INICIANDO CARGA ROBUSTA DE CSV TELCEL2022")
        self.log_message("=" * 70)
        
        # FASE 1: Preparación
        self.log_message("📋 FASE 1: PREPARACIÓN DE TABLA FLEXIBLE")
        if not self.create_flexible_raw_table():
            return False
        
        # FASE 2: Carga con parser Python
        self.log_message("\n🐍 FASE 2: CARGA CON PARSER PYTHON ROBUSTO")
        if not self.load_csv_with_python_parser():
            return False
        
        # FASE 3: Funciones de transformación
        self.log_message("\n🔧 FASE 3: FUNCIONES DE TRANSFORMACIÓN")
        if not self.create_transformation_functions_simple():
            return False
        
        # FASE 4: Transformación final
        self.log_message("\n🔄 FASE 4: TRANSFORMACIÓN Y CARGA FINAL")
        if not self.transform_and_load_final():
            return False
        
        # FASE 5: Estadísticas
        self.log_message("\n📊 FASE 5: ESTADÍSTICAS FINALES")
        self.get_final_statistics()
        
        # FASE 6: Limpieza
        self.log_message("\n🧹 FASE 6: LIMPIEZA")
        self.cleanup_raw_data()
        
        # Resumen final
        total_time = time.time() - self.start_time
        
        self.log_message("\n" + "=" * 70)
        self.log_message("🎯 CARGA ROBUSTA DE CSV COMPLETADA")
        self.log_message("=" * 70)
        self.log_message(f"⏱️  Tiempo total: {total_time/60:.1f} minutos")
        self.log_message(f"📁 Archivo: {self.csv_path} (4.0GB)")
        self.log_message(f"🛡️  Método: Parser Python + Transformación SQL")
        self.log_message(f"✅ Tolerancia a errores: Activada")
        
        return True

def main():
    """Función principal"""
    loader = CSVRobustLoader()
    
    print("🔥 CARGA ROBUSTA DE CSV TELCEL2022")
    print("🛡️  PARSER PYTHON + TOLERANCIA A ERRORES")
    print("⏱️  TIEMPO ESTIMADO: 15-45 minutos")
    print("📋 Características:")
    print("   - Parser Python robusto")
    print("   - Tolerancia a campos faltantes")
    print("   - Limpieza automática de datos")
    print("   - Inserción por lotes optimizada")
    print("   - Transformación SQL final")
    print("   - Manejo de errores avanzado")
    
    confirm = input("\n¿Continuar con la carga robusta? (yes/no): ").lower().strip()
    
    if confirm == 'yes':
        success = loader.execute_robust_csv_load()
        
        if success:
            print("\n🎉 ¡CARGA ROBUSTA COMPLETADA EXITOSAMENTE!")
            print("📊 Los datos están listos en la tabla contacts")
        else:
            print("\n❌ CARGA FALLÓ - Revisa los logs para detalles")
    else:
        print("\n❌ Carga cancelada por el usuario")

if __name__ == "__main__":
    main()