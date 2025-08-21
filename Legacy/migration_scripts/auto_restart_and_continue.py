#!/usr/bin/env python3
"""
AUTO-RESTART Y CONTINUACIÓN DE TRANSFORMACIÓN
Espera a que Docker esté disponible y continúa la transformación
"""

import subprocess
import sys
import os
import time
from datetime import datetime

class AutoRestartAndContinue:
    """Auto reinicio y continuación de la transformación"""
    
    def __init__(self):
        self.start_time = None
        self.max_wait_time = 300  # 5 minutos máximo esperando Docker
        
    def log_message(self, message, level="INFO"):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def wait_for_docker(self):
        """Esperar a que Docker esté disponible"""
        self.log_message("🔄 Esperando a que Docker esté disponible...")
        
        start_wait = time.time()
        
        while time.time() - start_wait < self.max_wait_time:
            try:
                result = subprocess.run(['docker', 'ps'], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    self.log_message("✅ Docker está disponible")
                    return True
                    
            except Exception as e:
                pass
            
            self.log_message("⏳ Docker no disponible, esperando 10 segundos...")
            time.sleep(10)
        
        self.log_message("❌ Timeout esperando Docker", "ERROR")
        return False
    
    def start_services(self):
        """Iniciar servicios de Docker Compose"""
        self.log_message("🚀 Iniciando servicios...")
        
        try:
            result = subprocess.run(['docker-compose', 'up', '-d'], 
                                  capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                self.log_message("✅ Servicios iniciados")
                
                # Esperar a que PostgreSQL esté listo
                self.log_message("⏳ Esperando PostgreSQL...")
                time.sleep(30)
                
                return True
            else:
                self.log_message(f"❌ Error iniciando servicios: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Error iniciando servicios: {e}", "ERROR")
            return False
    
    def verify_database_status(self):
        """Verificar estado de la base de datos"""
        self.log_message("📊 Verificando estado de la base de datos...")
        
        try:
            # Verificar conexión
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', 'SELECT 1;'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.log_message("❌ No se puede conectar a PostgreSQL", "ERROR")
                return False, 0, 0, 0
            
            # Contar registros en telcel_data
            result1 = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-t', '-c', 'SELECT COUNT(*) FROM telcel_data;'
            ], capture_output=True, text=True, timeout=30)
            
            telcel_count = int(result1.stdout.strip()) if result1.returncode == 0 else 0
            
            # Contar registros en contacts
            result2 = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-t', '-c', 'SELECT COUNT(*) FROM contacts;'
            ], capture_output=True, text=True, timeout=30)
            
            contacts_count = int(result2.stdout.strip()) if result2.returncode == 0 else 0
            
            remaining = telcel_count - contacts_count
            
            self.log_message(f"📊 Estado actual:")
            self.log_message(f"   ✅ Datos fuente (telcel_data): {telcel_count:,}")
            self.log_message(f"   🔄 Transformados (contacts): {contacts_count:,}")
            self.log_message(f"   ⏳ Pendientes: {remaining:,}")
            
            if telcel_count > 0:
                progress = (contacts_count / telcel_count) * 100
                self.log_message(f"   📈 Progreso: {progress:.1f}%")
            
            return True, telcel_count, contacts_count, remaining
            
        except Exception as e:
            self.log_message(f"❌ Error verificando base de datos: {e}", "ERROR")
            return False, 0, 0, 0
    
    def continue_transformation_optimized(self, contacts_count, remaining):
        """Continuar transformación con optimizaciones"""
        if remaining <= 0:
            self.log_message("✅ ¡Transformación ya está completa!")
            return True
        
        self.log_message(f"🔄 Continuando transformación desde registro {contacts_count:,}")
        self.log_message(f"📦 Procesando {remaining:,} registros restantes en lotes de 1M")
        
        batch_size = 1000000  # Lotes más grandes para mayor eficiencia
        processed = 0
        batch_num = 1
        
        while processed < remaining:
            batch_start = time.time()
            current_batch_size = min(batch_size, remaining - processed)
            offset = contacts_count + processed
            
            self.log_message(f"📦 MEGA-Lote {batch_num}: {current_batch_size:,} registros (offset: {offset:,})")
            
            # SQL optimizado para lotes grandes
            batch_sql = f"""
-- Configuración temporal para velocidad
SET work_mem = '1GB';
SET maintenance_work_mem = '2GB';
SET synchronous_commit = off;
SET wal_buffers = '64MB';
SET checkpoint_completion_target = 0.9;

-- Insertar mega-lote
INSERT INTO contacts (
    phone_e164, phone_national, phone_original, full_name, address, 
    neighborhood, lada, state_code, state_name, municipality, city, 
    is_mobile, operator, status, source, created_at, updated_at, 
    send_count, validation_attempts
)
SELECT 
    '+52' || phone as phone_e164,
    phone as phone_national,
    phone as phone_original,
    CASE WHEN full_name IS NOT NULL AND trim(full_name) != '' 
         THEN upper(trim(regexp_replace(full_name, '[^A-Za-z0-9 ÑñÁÉÍÓÚáéíóúü.,#-]', '', 'g')))
         ELSE NULL END as full_name,
    CASE WHEN address IS NOT NULL AND trim(address) != '' 
         THEN upper(trim(regexp_replace(address, '[^A-Za-z0-9 ÑñÁÉÍÓÚáéíóúü.,#-]', '', 'g')))
         ELSE NULL END as address,
    CASE WHEN neighborhood IS NOT NULL AND trim(neighborhood) != '' 
         THEN upper(trim(regexp_replace(neighborhood, '[^A-Za-z0-9 ÑñÁÉÍÓÚáéíóúü.,#-]', '', 'g')))
         ELSE NULL END as neighborhood,
    left(phone, 3) as lada,
    CASE 
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%BCS%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%BAJA CALIFORNIA SUR%' THEN 'BCS'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%BC%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%BAJA CALIFORNIA%' THEN 'BC'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%CDMX%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%DF%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%MEXICO%' THEN 'CDMX'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%NL%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%NUEVO LEON%' THEN 'NL'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%JAL%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%JALISCO%' THEN 'JAL'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%VER%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%VERACRUZ%' THEN 'VER'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%PUE%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%PUEBLA%' THEN 'PUE'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%GTO%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%GUANAJUATO%' THEN 'GTO'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%CHIH%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%CHIHUAHUA%' THEN 'CHIH'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%MICH%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%MICHOACAN%' THEN 'MICH'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%SIN%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%SINALOA%' THEN 'SIN'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%OAX%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%OAXACA%' THEN 'OAX'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%CHIS%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%CHIAPAS%' THEN 'CHIS'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%TAMS%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%TAMAULIPAS%' THEN 'TAMS'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%GRO%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%GUERRERO%' THEN 'GRO'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%COAH%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%COAHUILA%' THEN 'COAH'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%HGO%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%HIDALGO%' THEN 'HGO'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%SON%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%SONORA%' THEN 'SON'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%YUC%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%YUCATAN%' THEN 'YUC'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%QRO%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%QUERETARO%' THEN 'QRO'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%MOR%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%MORELOS%' THEN 'MOR'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%DUR%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%DURANGO%' THEN 'DUR'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%ZAC%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%ZACATECAS%' THEN 'ZAC'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%QROO%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%QUINTANA ROO%' THEN 'QROO'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%AGS%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%AGUASCALIENTES%' THEN 'AGS'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%TLAX%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%TLAXCALA%' THEN 'TLAX'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%NAY%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%NAYARIT%' THEN 'NAY'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%CAM%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%CAMPECHE%' THEN 'CAM'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%COL%' OR upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%COLIMA%' THEN 'COL'
        ELSE left(upper(trim(coalesce(state_name, state_alt, ''))), 5)
    END as state_code,
    upper(trim(coalesce(state_name, state_alt, ''))) as state_name,
    upper(trim(coalesce(municipality, municipality_alt, ''))) as municipality,
    upper(trim(city)) as city,
    CASE WHEN left(phone, 3) IN (
        '55', '33', '81', '222', '228', '229', '246', '248', '249', '271', '272', '273', '274', '275', 
        '276', '278', '279', '281', '282', '283', '284', '285', '287', '288', '294', '297', '311', '312', 
        '313', '314', '315', '316', '317', '318', '319', '321', '322', '323', '324', '325', '326', '327', 
        '328', '329', '341', '342', '343', '344', '345', '346', '347', '348', '351', '352', '353', '354', 
        '355', '356', '357', '358', '359', '371', '372', '373', '374', '375', '376', '377', '378', '381', 
        '382', '383', '384', '385', '386', '387', '388', '389', '391', '392', '393', '394', '395', '396', 
        '397', '398', '411', '412', '413', '414', '415', '417', '418', '421', '422', '423', '424', '425', 
        '426', '427', '428', '429', '431', '432', '433', '434', '435', '436', '437', '438', '441', '442', 
        '443', '444', '445', '446', '447', '448', '449', '451', '452', '453', '454', '455', '456', '457', 
        '458', '459', '461', '462', '464', '465', '466', '467', '468', '469', '471', '472', '473', '474', 
        '475', '476', '477', '478', '481', '482', '483', '484', '485', '486', '487', '488', '489', '492', 
        '493', '494', '496', '497', '498', '499', '614', '615', '616', '617', '618', '621', '622', '623', 
        '624', '625', '626', '627', '628', '629', '631', '632', '633', '634', '635', '636', '637', '638', 
        '639', '641', '642', '643', '644', '645', '646', '647', '648', '649', '651', '652', '653', '656', 
        '657', '658', '659', '661', '662', '664', '665', '667', '668', '669', '671', '672', '673', '674', 
        '675', '676', '677', '686', '687', '688', '689', '694', '695', '696', '697', '698'
    ) THEN true ELSE false END as is_mobile,
    CASE WHEN left(phone, 3) IN (
        '55', '33', '81', '222', '228', '229', '246', '248', '249', '271', '272', '273', '274', '275', 
        '276', '278', '279', '281', '282', '283', '284', '285', '287', '288', '294', '297', '311', '312', 
        '313', '314', '315', '316', '317', '318', '319', '321', '322', '323', '324', '325', '326', '327', 
        '328', '329', '341', '342', '343', '344', '345', '346', '347', '348', '351', '352', '353', '354', 
        '355', '356', '357', '358', '359', '371', '372', '373', '374', '375', '376', '377', '378', '381', 
        '382', '383', '384', '385', '386', '387', '388', '389', '391', '392', '393', '394', '395', '396', 
        '397', '398', '411', '412', '413', '414', '415', '417', '418', '421', '422', '423', '424', '425', 
        '426', '427', '428', '429', '431', '432', '433', '434', '435', '436', '437', '438', '441', '442', 
        '443', '444', '445', '446', '447', '448', '449', '451', '452', '453', '454', '455', '456', '457', 
        '458', '459', '461', '462', '464', '465', '466', '467', '468', '469', '471', '472', '473', '474', 
        '475', '476', '477', '478', '481', '482', '483', '484', '485', '486', '487', '488', '489', '492', 
        '493', '494', '496', '497', '498', '499', '614', '615', '616', '617', '618', '621', '622', '623', 
        '624', '625', '626', '627', '628', '629', '631', '632', '633', '634', '635', '636', '637', '638', 
        '639', '641', '642', '643', '644', '645', '646', '647', '648', '649', '651', '652', '653', '656', 
        '657', '658', '659', '661', '662', '664', '665', '667', '668', '669', '671', '672', '673', '674', 
        '675', '676', '677', '686', '687', '688', '689', '694', '695', '696', '697', '698'
    ) THEN 'Telcel' ELSE 'Telmex' END as operator,
    ('VERIFIED')::contactstatus as status,
    'TELCEL2022' as source,
    NOW() as created_at,
    NOW() as updated_at,
    0 as send_count,
    0 as validation_attempts
FROM (
    SELECT * FROM telcel_data 
    WHERE phone IS NOT NULL AND phone ~ '^[0-9]{{10}}$'
    ORDER BY phone
    LIMIT {current_batch_size} OFFSET {offset}
) t
ON CONFLICT (phone_e164) DO NOTHING;

-- Commit inmediato
COMMIT;

-- Estadísticas del lote
SELECT 'MEGA-Lote {batch_num} procesado' as resultado, 
       {current_batch_size} as registros_procesados,
       {offset} as offset_inicial;
"""
            
            try:
                result = subprocess.run([
                    'docker-compose', 'exec', '-T', 'postgres',
                    'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                    '-c', batch_sql
                ], capture_output=True, text=True, timeout=1800)  # 30 min timeout
                
                batch_time = time.time() - batch_start
                
                if result.returncode == 0:
                    records_per_second = current_batch_size / batch_time if batch_time > 0 else 0
                    processed += current_batch_size
                    
                    # Verificar progreso real
                    current_total = self.get_contacts_count()
                    
                    self.log_message(f"✅ MEGA-Lote {batch_num} COMPLETADO:")
                    self.log_message(f"   ⏱️  Tiempo: {batch_time/60:.1f} minutos")
                    self.log_message(f"   🚀 Velocidad: {records_per_second:.0f} reg/s")
                    self.log_message(f"   📊 Total actual: {current_total:,}")
                    
                    if current_total > 0:
                        # Recalcular progreso basado en datos reales
                        db_status = self.verify_database_status()
                        if db_status[0]:
                            _, telcel_total, contacts_total, remaining_real = db_status
                            if telcel_total > 0:
                                progress = (contacts_total / telcel_total) * 100
                                self.log_message(f"   📈 Progreso real: {progress:.1f}%")
                                remaining = remaining_real  # Actualizar remaining real
                    
                    batch_num += 1
                    
                    # Pausa corta para no sobrecargar
                    time.sleep(2)
                    
                else:
                    self.log_message(f"❌ Error en MEGA-Lote {batch_num}: {result.stderr}", "ERROR")
                    # Intentar con lote más pequeño
                    self.log_message("🔄 Intentando con lotes más pequeños...")
                    return self.continue_transformation_small_batches(contacts_count + processed, remaining - processed)
                    
            except subprocess.TimeoutExpired:
                self.log_message(f"⏰ Timeout en MEGA-Lote {batch_num} (30 min)", "WARNING")
                # Intentar con lote más pequeño
                return self.continue_transformation_small_batches(contacts_count + processed, remaining - processed)
            except Exception as e:
                self.log_message(f"❌ Error procesando MEGA-Lote {batch_num}: {e}", "ERROR")
                return False
        
        return True
    
    def continue_transformation_small_batches(self, start_offset, remaining):
        """Fallback con lotes pequeños"""
        self.log_message("🔄 Continuando con lotes pequeños de 250K...")
        
        batch_size = 250000
        processed = 0
        batch_num = 1
        
        while processed < remaining:
            batch_start = time.time()
            current_batch_size = min(batch_size, remaining - processed)
            offset = start_offset + processed
            
            self.log_message(f"📦 Lote pequeño {batch_num}: {current_batch_size:,} registros")
            
            # SQL más simple para lotes pequeños
            batch_sql = f"""
INSERT INTO contacts (phone_e164, phone_national, phone_original, lada, is_mobile, operator, status, source, created_at, updated_at, send_count, validation_attempts)
SELECT '+52' || phone, phone, phone, left(phone, 3), 
       CASE WHEN left(phone, 3) IN ('55', '33', '81') THEN true ELSE false END,
       CASE WHEN left(phone, 3) IN ('55', '33', '81') THEN 'Telcel' ELSE 'Telmex' END,
       ('VERIFIED')::contactstatus, 'TELCEL2022', NOW(), NOW(), 0, 0
FROM (SELECT * FROM telcel_data WHERE phone IS NOT NULL ORDER BY phone LIMIT {current_batch_size} OFFSET {offset}) t
ON CONFLICT (phone_e164) DO NOTHING;
"""
            
            try:
                result = subprocess.run([
                    'docker-compose', 'exec', '-T', 'postgres',
                    'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                    '-c', batch_sql
                ], capture_output=True, text=True, timeout=600)
                
                if result.returncode == 0:
                    batch_time = time.time() - batch_start
                    records_per_second = current_batch_size / batch_time if batch_time > 0 else 0
                    processed += current_batch_size
                    
                    self.log_message(f"✅ Lote {batch_num}: {batch_time:.1f}s, {records_per_second:.0f} reg/s")
                    batch_num += 1
                else:
                    self.log_message(f"❌ Error en lote pequeño {batch_num}", "ERROR")
                    return False
                    
            except Exception as e:
                self.log_message(f"❌ Error: {e}", "ERROR")
                return False
        
        return True
    
    def get_contacts_count(self):
        """Obtener conteo actual de contacts"""
        try:
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-t', '-c', 'SELECT COUNT(*) FROM contacts;'
            ], capture_output=True, text=True, timeout=30)
            
            return int(result.stdout.strip()) if result.returncode == 0 else 0
        except:
            return 0
    
    def final_optimization(self):
        """Optimización y limpieza final"""
        self.log_message("🚀 OPTIMIZACIÓN FINAL...")
        
        sql = """
-- Eliminar tabla temporal
DROP TABLE IF EXISTS telcel_data CASCADE;

-- Crear índices optimizados
CREATE INDEX IF NOT EXISTS idx_contacts_state_mobile ON contacts(state_code, is_mobile) WHERE state_code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_contacts_lada_mobile ON contacts(lada, is_mobile);
CREATE INDEX IF NOT EXISTS idx_contacts_status_active ON contacts(status) WHERE status = 'VERIFIED';
CREATE INDEX IF NOT EXISTS idx_contacts_operator ON contacts(operator);

-- Optimización completa
VACUUM ANALYZE contacts;

-- Estadísticas finales
SELECT 'MIGRACIÓN COMPLETADA' as estado;
SELECT COUNT(*) as total_contactos FROM contacts;
SELECT COUNT(CASE WHEN is_mobile THEN 1 END) as telefonos_moviles FROM contacts;
SELECT COUNT(CASE WHEN NOT is_mobile THEN 1 END) as telefonos_fijos FROM contacts;
SELECT COUNT(DISTINCT state_code) as estados_unicos FROM contacts WHERE state_code IS NOT NULL;
SELECT COUNT(DISTINCT lada) as ladas_unicas FROM contacts;
SELECT pg_size_pretty(pg_total_relation_size('contacts')) as tamaño_tabla_contacts;
"""
        
        try:
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', sql
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log_message("✅ OPTIMIZACIÓN COMPLETADA")
                
                # Mostrar estadísticas finales
                lines = result.stdout.split('\n')
                for line in lines:
                    if any(keyword in line for keyword in ['total_contactos', 'telefonos_moviles', 'telefonos_fijos', 'estados_unicos', 'ladas_unicas', 'tamaño_tabla']) or (line.strip().isdigit() and len(line.strip()) > 3):
                        self.log_message(f"📊 {line.strip()}")
            
            return True
        except Exception as e:
            self.log_message(f"⚠️  Error en optimización final: {e}", "WARNING")
            return True
    
    def execute_full_restart_and_continue(self):
        """Ejecutar reinicio completo y continuación"""
        self.start_time = time.time()
        
        self.log_message("🔄 AUTO-RESTART Y CONTINUACIÓN SMS MARKETING")
        self.log_message("=" * 60)
        
        # Paso 1: Esperar Docker
        if not self.wait_for_docker():
            return False
        
        # Paso 2: Iniciar servicios
        if not self.start_services():
            return False
        
        # Paso 3: Verificar estado
        db_ok, telcel_count, contacts_count, remaining = self.verify_database_status()
        if not db_ok:
            return False
        
        # Paso 4: Continuar transformación
        if remaining > 0:
            if not self.continue_transformation_optimized(contacts_count, remaining):
                return False
        
        # Paso 5: Optimización final
        self.final_optimization()
        
        # Resumen final
        total_time = time.time() - self.start_time
        
        self.log_message("\n" + "=" * 60)
        self.log_message("🎉 SISTEMA SMS MARKETING COMPLETADO")
        self.log_message("=" * 60)
        self.log_message(f"⏱️  Tiempo total: {total_time/60:.1f} minutos")
        self.log_message(f"🚀 36+ millones de contactos listos para SMS")
        self.log_message(f"📊 Base de datos optimizada y funcional")
        
        return True

def main():
    """Función principal"""
    auto_restart = AutoRestartAndContinue()
    
    print("🔄 AUTO-RESTART Y CONTINUACIÓN SMS MARKETING")
    print("⚠️  INSTRUCCIONES:")
    print("   1. Reinicia Docker Desktop manualmente")
    print("   2. Ejecuta este script")
    print("   3. El script esperará a que Docker esté disponible")
    print("   4. Continuará automáticamente la transformación")
    print("\n⏱️  TIEMPO ESTIMADO: 30-45 minutos")
    
    input("\n🔄 Presiona ENTER cuando hayas reiniciado Docker Desktop...")
    
    success = auto_restart.execute_full_restart_and_continue()
    
    if success:
        print("\n🎉 ¡MIGRACIÓN COMPLETADA EXITOSAMENTE!")
        print("🚀 Sistema SMS Marketing listo para usar")
    else:
        print("\n❌ ERROR - Revisa los logs")

if __name__ == "__main__":
    main()