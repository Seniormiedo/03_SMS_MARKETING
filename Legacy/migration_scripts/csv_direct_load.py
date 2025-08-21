#!/usr/bin/env python3
"""
CARGA DIRECTA DE CSV A POSTGRESQL
Estrategia: Cargar CSV raw primero, transformar después en PostgreSQL
"""

import subprocess
import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

class CSVDirectLoader:
    """Cargador directo de CSV a PostgreSQL"""
    
    def __init__(self):
        self.start_time = None
        self.csv_path = "data/TELCEL2022.csv"
        
    def log_message(self, message, level="INFO"):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def analyze_csv_structure(self):
        """Analizar estructura del CSV"""
        self.log_message("🔍 Analizando estructura del CSV...")
        
        try:
            # Leer primeras líneas para entender estructura
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                header = f.readline().strip()
                sample_lines = [f.readline().strip() for _ in range(3)]
            
            # Analizar delimitador y columnas
            delimiter = ';'  # Visto en el sample
            columns = header.split(delimiter)
            
            self.log_message(f"📊 Estructura CSV detectada:")
            self.log_message(f"   📁 Archivo: {self.csv_path}")
            self.log_message(f"   📏 Tamaño: 4.0GB")
            self.log_message(f"   🔗 Delimitador: '{delimiter}'")
            self.log_message(f"   📋 Columnas: {len(columns)}")
            
            for i, col in enumerate(columns):
                self.log_message(f"      {i+1}. {col}")
            
            # Mostrar muestra de datos
            self.log_message(f"📄 Muestra de datos:")
            for i, line in enumerate(sample_lines[:2]):
                if line:
                    values = line.split(delimiter)
                    self.log_message(f"   Registro {i+1}: {len(values)} campos")
            
            return {
                "delimiter": delimiter,
                "columns": columns,
                "sample_data": sample_lines
            }
            
        except Exception as e:
            self.log_message(f"❌ Error analizando CSV: {e}", "ERROR")
            return None
    
    def create_raw_table(self, structure):
        """Crear tabla raw para cargar CSV"""
        self.log_message("🏗️  Creando tabla raw para CSV...")
        
        # Mapear columnas CSV a tabla PostgreSQL
        columns = structure["columns"]
        
        # Crear definición de tabla con todas las columnas como TEXT
        column_definitions = []
        for col in columns:
            # Limpiar nombre de columna
            clean_col = col.replace(" ", "_").replace("-", "_").lower()
            if not clean_col:
                clean_col = f"campo_{len(column_definitions)+1}"
            column_definitions.append(f"{clean_col} TEXT")
        
        create_table_sql = f"""
-- Crear tabla raw para carga CSV
DROP TABLE IF EXISTS raw_telcel_data CASCADE;

CREATE TABLE raw_telcel_data (
    id SERIAL PRIMARY KEY,
    {', '.join(column_definitions)},
    loaded_at TIMESTAMP DEFAULT NOW()
);

-- Crear índice en el campo principal (número de teléfono)
CREATE INDEX IF NOT EXISTS idx_raw_telcel_campo1 ON raw_telcel_data(campo1);

-- Mostrar estructura creada
SELECT 'Tabla raw_telcel_data creada exitosamente' as resultado;
"""
        
        try:
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', create_table_sql
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.log_message("✅ Tabla raw creada exitosamente")
                self.log_message(f"📋 Estructura:")
                # Mostrar output de \d
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'campo' in line.lower() or 'column' in line.lower():
                        self.log_message(f"   {line.strip()}")
                return True
            else:
                self.log_message(f"❌ Error creando tabla: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Error creando tabla: {e}", "ERROR")
            return False
    
    def load_csv_direct(self):
        """Cargar CSV directamente usando COPY"""
        self.log_message("🚀 Cargando CSV directamente con COPY...")
        
        # Copiar CSV al contenedor
        self.log_message("📋 Copiando CSV al contenedor PostgreSQL...")
        copy_start = time.time()
        
        try:
            copy_result = subprocess.run([
                'docker', 'cp', self.csv_path, 'sms_postgres:/tmp/telcel_data.csv'
            ], capture_output=True, text=True, timeout=300)  # 5 min timeout
            
            copy_time = time.time() - copy_start
            
            if copy_result.returncode != 0:
                self.log_message(f"❌ Error copiando CSV: {copy_result.stderr}", "ERROR")
                return False
            
            self.log_message(f"✅ CSV copiado en {copy_time:.1f}s")
            
        except subprocess.TimeoutExpired:
            self.log_message("❌ Timeout copiando CSV (>5 min)", "ERROR")
            return False
        except Exception as e:
            self.log_message(f"❌ Error copiando CSV: {e}", "ERROR")
            return False
        
        # Ejecutar COPY FROM
        self.log_message("💾 Ejecutando COPY FROM (esto puede tomar varios minutos)...")
        load_start = time.time()
        
        copy_sql = """
-- Cargar CSV usando COPY
COPY raw_telcel_data (
    campo1, campo2, campo3, campo4, campo5, campo6, 
    edosep, mposep, edocof, mpocof
) FROM '/tmp/telcel_data.csv' 
WITH (
    FORMAT csv,
    DELIMITER ';',
    HEADER true,
    ENCODING 'UTF8'
);

-- Mostrar estadísticas de carga
SELECT 'Carga CSV completada' as resultado;
SELECT COUNT(*) as registros_cargados FROM raw_telcel_data;
SELECT 'Primeros 3 registros:' as muestra;
SELECT id, campo1, campo2, left(campo4, 50) as direccion_preview 
FROM raw_telcel_data 
ORDER BY id 
LIMIT 3;
"""
        
        try:
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', copy_sql
            ], capture_output=True, text=True, timeout=1800)  # 30 min timeout
            
            load_time = time.time() - load_start
            
            if result.returncode == 0:
                self.log_message(f"✅ CSV cargado exitosamente en {load_time/60:.1f} minutos")
                
                # Extraer estadísticas del output
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'registros_cargados' in line or line.strip().isdigit():
                        self.log_message(f"📊 {line.strip()}")
                
                return True
            else:
                self.log_message(f"❌ Error en COPY: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_message("❌ Timeout en COPY (>30 min)", "ERROR")
            return False
        except Exception as e:
            self.log_message(f"❌ Error en COPY: {e}", "ERROR")
            return False
    
    def create_transformation_functions(self):
        """Crear funciones de transformación en PostgreSQL"""
        self.log_message("🔧 Creando funciones de transformación...")
        
        transformation_sql = """
-- Función para normalizar números de teléfono
CREATE OR REPLACE FUNCTION normalize_phone(phone_raw TEXT) 
RETURNS TABLE(
    phone_e164 TEXT,
    phone_national TEXT,
    is_mobile BOOLEAN,
    lada TEXT,
    operator TEXT
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
    
    -- Determinar si es móvil (LADAs móviles mexicanas)
    is_mobile := lada IN ('044', '045') OR 
                 lada ~ '^(55|33|81|222|228|229|246|248|249|271|272|273|274|275|276|278|279|281|282|283|284|285|287|288|294|297|311|312|313|314|315|316|317|318|319|321|322|323|324|325|326|327|328|329|341|342|343|344|345|346|347|348|351|352|353|354|355|356|357|358|359|371|372|373|374|375|376|377|378|381|382|383|384|385|386|387|388|389|391|392|393|394|395|396|397|398|411|412|413|414|415|417|418|421|422|423|424|425|426|427|428|429|431|432|433|434|435|436|437|438|441|442|443|444|445|446|447|448|449|451|452|453|454|455|456|457|458|459|461|462|464|465|466|467|468|469|471|472|473|474|475|476|477|478|481|482|483|484|485|486|487|488|489|492|493|494|496|497|498|499|614|615|616|617|618|621|622|623|624|625|626|627|628|629|631|632|633|634|635|636|637|638|639|641|642|643|644|645|646|647|648|649|651|652|653|656|657|658|659|661|662|664|665|667|668|669|671|672|673|674|675|676|677|686|687|688|689|694|695|696|697|698|711|712|713|714|715|716|717|718|719|721|722|723|724|725|726|727|728|729|731|732|733|734|735|736|737|738|739|741|742|743|744|745|746|747|748|749|751|752|753|754|755|756|757|758|759|761|762|763|764|765|766|767|768|769|771|772|773|774|775|776|777|778|779|781|782|783|784|785|786|787|788|789|797|811|812|813|814|815|816|817|818|819|821|822|823|824|825|826|827|828|829|831|832|833|834|835|836|837|838|841|842|844|845|846|861|862|863|864|866|867|868|869|871|872|873|874|875|876|877|878|879|891|892|894|895|896|897|899|911|912|913|914|915|916|917|918|919|921|922|923|924|925|926|927|928|929|931|932|933|934|935|936|937|938|951|952|953|954|955|956|957|958|959|961|962|963|964|965|966|967|968|971|972|973|974|975|976|977|978|981|982|983|984|985|986|987|988|992|993|994|995|996|997|998|999)$';
    
    -- Formatear E.164
    phone_e164 := '+52' || phone_raw;
    
    -- Formatear nacional
    phone_national := phone_raw;
    
    -- Determinar operador (simplificado)
    operator := CASE 
        WHEN is_mobile THEN 'Telcel'
        ELSE 'Telmex'
    END;
    
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- Función para limpiar y normalizar texto
CREATE OR REPLACE FUNCTION clean_text(input_text TEXT) 
RETURNS TEXT AS $$
BEGIN
    IF input_text IS NULL OR trim(input_text) = '' THEN
        RETURN NULL;
    END IF;
    
    -- Limpiar y normalizar
    input_text := trim(upper(input_text));
    input_text := regexp_replace(input_text, '\\s+', ' ', 'g');
    
    RETURN input_text;
END;
$$ LANGUAGE plpgsql;

-- Función para mapear estados
CREATE OR REPLACE FUNCTION map_state_code(state_name TEXT) 
RETURNS TEXT AS $$
BEGIN
    state_name := upper(trim(state_name));
    
    RETURN CASE 
        WHEN state_name IN ('BAJA CALIFORNIA SUR', 'BCS') THEN 'BCS'
        WHEN state_name IN ('BAJA CALIFORNIA', 'BC') THEN 'BC'
        WHEN state_name IN ('CIUDAD DE MEXICO', 'CDMX', 'DF', 'DISTRITO FEDERAL') THEN 'CDMX'
        WHEN state_name IN ('NUEVO LEON', 'NL') THEN 'NL'
        WHEN state_name IN ('JALISCO', 'JAL') THEN 'JAL'
        WHEN state_name IN ('VERACRUZ', 'VER') THEN 'VER'
        WHEN state_name IN ('PUEBLA', 'PUE') THEN 'PUE'
        WHEN state_name IN ('GUANAJUATO', 'GTO') THEN 'GTO'
        WHEN state_name IN ('CHIHUAHUA', 'CHIH') THEN 'CHIH'
        WHEN state_name IN ('MICHOACAN', 'MICH') THEN 'MICH'
        WHEN state_name IN ('OAXACA', 'OAX') THEN 'OAX'
        WHEN state_name IN ('CHIAPAS', 'CHIS') THEN 'CHIS'
        WHEN state_name IN ('TAMAULIPAS', 'TAMS') THEN 'TAMS'
        WHEN state_name IN ('GUERRERO', 'GRO') THEN 'GRO'
        WHEN state_name IN ('SINALOA', 'SIN') THEN 'SIN'
        WHEN state_name IN ('COAHUILA', 'COAH') THEN 'COAH'
        WHEN state_name IN ('HIDALGO', 'HGO') THEN 'HGO'
        WHEN state_name IN ('SONORA', 'SON') THEN 'SON'
        WHEN state_name IN ('SAN LUIS POTOSI', 'SLP') THEN 'SLP'
        WHEN state_name IN ('TABASCO', 'TAB') THEN 'TAB'
        WHEN state_name IN ('YUCATAN', 'YUC') THEN 'YUC'
        WHEN state_name IN ('QUERETARO', 'QRO') THEN 'QRO'
        WHEN state_name IN ('MORELOS', 'MOR') THEN 'MOR'
        WHEN state_name IN ('DURANGO', 'DUR') THEN 'DUR'
        WHEN state_name IN ('ZACATECAS', 'ZAC') THEN 'ZAC'
        WHEN state_name IN ('QUINTANA ROO', 'QROO') THEN 'QROO'
        WHEN state_name IN ('AGUASCALIENTES', 'AGS') THEN 'AGS'
        WHEN state_name IN ('TLAXCALA', 'TLAX') THEN 'TLAX'
        WHEN state_name IN ('NAYARIT', 'NAY') THEN 'NAY'
        WHEN state_name IN ('CAMPECHE', 'CAM') THEN 'CAM'
        WHEN state_name IN ('COLIMA', 'COL') THEN 'COL'
        ELSE state_name
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
                self.log_message("✅ Funciones de transformación creadas")
                return True
            else:
                self.log_message(f"❌ Error creando funciones: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Error creando funciones: {e}", "ERROR")
            return False
    
    def transform_and_load_contacts(self):
        """Transformar datos raw y cargar en tabla contacts"""
        self.log_message("🔄 Transformando datos y cargando en tabla contacts...")
        
        transform_sql = """
-- Limpiar tabla contacts
TRUNCATE TABLE contacts RESTART IDENTITY CASCADE;

-- Insertar datos transformados
INSERT INTO contacts (
    phone_e164, phone_national, phone_original, full_name, address, neighborhood,
    lada, state_code, state_name, municipality, city, is_mobile, operator,
    status, source, created_at, updated_at, send_count, validation_attempts
)
SELECT 
    np.phone_e164,
    np.phone_national,
    r.campo1 as phone_original,
    clean_text(r.campo2) as full_name,
    clean_text(r.campo4) as address,
    clean_text(r.campo5) as neighborhood,
    np.lada,
    map_state_code(r.edosep) as state_code,
    clean_text(r.edosep) as state_name,
    clean_text(r.mposep) as municipality,
    clean_text(r.campo6) as city,
    np.is_mobile,
    np.operator,
    CASE WHEN np.is_mobile THEN 'VERIFIED' ELSE 'NOT_MOBILE' END as status,
    'TELCEL2022' as source,
    NOW() as created_at,
    NOW() as updated_at,
    0 as send_count,
    0 as validation_attempts
FROM raw_telcel_data r
CROSS JOIN LATERAL normalize_phone(r.campo1) np
WHERE np.phone_e164 IS NOT NULL
ON CONFLICT (phone_e164) DO NOTHING;

-- Mostrar estadísticas de transformación
SELECT 'Transformación completada' as resultado;
SELECT COUNT(*) as total_contacts FROM contacts;
SELECT 
    'Distribución por tipo' as analisis,
    is_mobile,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM contacts), 2) as porcentaje
FROM contacts 
GROUP BY is_mobile;

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
                
                # Mostrar estadísticas
                lines = result.stdout.split('\n')
                for line in lines:
                    if any(word in line.lower() for word in ['total_contacts', 'cantidad', 'porcentaje', 'analisis']):
                        self.log_message(f"📊 {line.strip()}")
                
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
    
    def cleanup_raw_data(self):
        """Limpiar datos raw después de transformación"""
        self.log_message("🧹 Limpiando datos raw...")
        
        cleanup_sql = """
-- Eliminar tabla raw para liberar espacio
DROP TABLE IF EXISTS raw_telcel_data CASCADE;

-- Optimizar tabla contacts
VACUUM ANALYZE contacts;

-- Mostrar estadísticas finales
SELECT 'Limpieza completada' as resultado;
SELECT COUNT(*) as registros_finales FROM contacts;
SELECT pg_size_pretty(pg_total_relation_size('contacts')) as tamaño_tabla;
"""
        
        try:
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', cleanup_sql
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log_message("✅ Limpieza completada")
                return True
            else:
                self.log_message(f"⚠️  Advertencia en limpieza: {result.stderr}", "WARNING")
                return True  # No crítico
                
        except Exception as e:
            self.log_message(f"⚠️  Error en limpieza: {e}", "WARNING")
            return True  # No crítico
    
    def execute_csv_direct_load(self):
        """Ejecutar carga directa completa de CSV"""
        self.start_time = time.time()
        
        self.log_message("🚀 INICIANDO CARGA DIRECTA DE CSV TELCEL2022")
        self.log_message("=" * 70)
        
        # FASE 1: Análisis
        self.log_message("📋 FASE 1: ANÁLISIS DE CSV")
        structure = self.analyze_csv_structure()
        if not structure:
            return False
        
        # FASE 2: Preparación
        self.log_message("\n🏗️  FASE 2: PREPARACIÓN DE TABLA RAW")
        if not self.create_raw_table(structure):
            return False
        
        # FASE 3: Carga directa
        self.log_message("\n💾 FASE 3: CARGA DIRECTA DE CSV")
        if not self.load_csv_direct():
            return False
        
        # FASE 4: Funciones de transformación
        self.log_message("\n🔧 FASE 4: CREACIÓN DE FUNCIONES")
        if not self.create_transformation_functions():
            return False
        
        # FASE 5: Transformación y carga final
        self.log_message("\n🔄 FASE 5: TRANSFORMACIÓN Y CARGA FINAL")
        if not self.transform_and_load_contacts():
            return False
        
        # FASE 6: Limpieza
        self.log_message("\n🧹 FASE 6: LIMPIEZA")
        self.cleanup_raw_data()
        
        # Estadísticas finales
        total_time = time.time() - self.start_time
        
        self.log_message("\n" + "=" * 70)
        self.log_message("🎯 CARGA DIRECTA DE CSV COMPLETADA")
        self.log_message("=" * 70)
        self.log_message(f"⏱️  Tiempo total: {total_time/60:.1f} minutos")
        self.log_message(f"📁 Archivo procesado: {self.csv_path} (4.0GB)")
        self.log_message(f"🚀 Estrategia: Carga directa + Transformación SQL")
        
        return True

def main():
    """Función principal"""
    loader = CSVDirectLoader()
    
    print("🔥 CARGA DIRECTA DE CSV TELCEL2022 A POSTGRESQL")
    print("⚡ ESTRATEGIA OPTIMIZADA - CSV RAW + TRANSFORMACIÓN SQL")
    print("⏱️  TIEMPO ESTIMADO: 10-30 minutos")
    print("📋 Proceso:")
    print("   1. Análisis automático de estructura CSV")
    print("   2. Creación de tabla raw temporal")
    print("   3. Carga directa con PostgreSQL COPY")
    print("   4. Transformación con funciones SQL")
    print("   5. Carga final en tabla contacts")
    print("   6. Limpieza automática")
    
    confirm = input("\n¿Continuar con la carga directa de CSV? (yes/no): ").lower().strip()
    
    if confirm == 'yes':
        success = loader.execute_csv_direct_load()
        
        if success:
            print("\n🎉 ¡CARGA DIRECTA DE CSV COMPLETADA EXITOSAMENTE!")
            print("📊 Los datos están listos en la tabla contacts")
        else:
            print("\n❌ CARGA FALLÓ - Revisa los logs para detalles")
    else:
        print("\n❌ Carga cancelada por el usuario")

if __name__ == "__main__":
    main()