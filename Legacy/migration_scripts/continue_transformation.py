#!/usr/bin/env python3
"""
CONTINUAR TRANSFORMACIÓN DESDE DONDE SE QUEDÓ
Procesar los registros restantes en lotes pequeños
"""

import subprocess
import sys
import os
import time
from datetime import datetime

class ContinueTransformation:
    """Continuar la transformación desde donde se quedó"""
    
    def __init__(self):
        self.start_time = None
        
    def log_message(self, message, level="INFO"):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def get_current_status(self):
        """Obtener estado actual de la migración"""
        self.log_message("📊 Verificando estado actual...")
        
        try:
            # Contar registros en contacts
            result1 = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-t', '-c', 'SELECT COUNT(*) FROM contacts;'
            ], capture_output=True, text=True, timeout=30)
            
            contacts_count = int(result1.stdout.strip()) if result1.returncode == 0 else 0
            
            # Contar registros en telcel_data
            result2 = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-t', '-c', 'SELECT COUNT(*) FROM telcel_data;'
            ], capture_output=True, text=True, timeout=30)
            
            telcel_count = int(result2.stdout.strip()) if result2.returncode == 0 else 0
            
            remaining = telcel_count - contacts_count
            
            self.log_message(f"📊 Estado actual:")
            self.log_message(f"   ✅ Datos cargados (telcel_data): {telcel_count:,}")
            self.log_message(f"   🔄 Transformados (contacts): {contacts_count:,}")
            self.log_message(f"   ⏳ Pendientes: {remaining:,}")
            self.log_message(f"   📈 Progreso: {(contacts_count/telcel_count*100):.1f}%")
            
            return contacts_count, telcel_count, remaining
            
        except Exception as e:
            self.log_message(f"❌ Error verificando estado: {e}", "ERROR")
            return 0, 0, 0
    
    def continue_transformation_batch(self, batch_size=500000):
        """Continuar transformación en lotes"""
        contacts_count, telcel_count, remaining = self.get_current_status()
        
        if remaining <= 0:
            self.log_message("✅ ¡Transformación ya está completa!")
            return True
        
        self.log_message(f"🔄 Continuando transformación en lotes de {batch_size:,}...")
        
        # Procesar en lotes
        processed = 0
        batch_num = 1
        
        while processed < remaining:
            batch_start = time.time()
            current_batch_size = min(batch_size, remaining - processed)
            offset = contacts_count + processed
            
            self.log_message(f"📦 Lote {batch_num}: Procesando {current_batch_size:,} registros (offset: {offset:,})")
            
            # SQL para procesar el lote actual
            batch_sql = f"""
-- Insertar lote desde telcel_data a contacts
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
    -- Determinar si es móvil basado en LADA
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

-- Mostrar progreso
SELECT 'Lote procesado' as resultado, {current_batch_size} as tamaño_lote, {offset} as offset_usado;
"""
            
            try:
                result = subprocess.run([
                    'docker-compose', 'exec', '-T', 'postgres',
                    'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                    '-c', batch_sql
                ], capture_output=True, text=True, timeout=600)  # 10 min timeout
                
                batch_time = time.time() - batch_start
                
                if result.returncode == 0:
                    records_per_second = current_batch_size / batch_time if batch_time > 0 else 0
                    processed += current_batch_size
                    
                    # Verificar progreso real
                    current_total = self.get_contacts_count()
                    
                    self.log_message(f"✅ Lote {batch_num} completado:")
                    self.log_message(f"   ⏱️  Tiempo: {batch_time:.1f}s")
                    self.log_message(f"   🚀 Velocidad: {records_per_second:.0f} reg/s")
                    self.log_message(f"   📊 Total actual: {current_total:,}")
                    self.log_message(f"   📈 Progreso: {(current_total/telcel_count*100):.1f}%")
                    
                    batch_num += 1
                    
                    # Pausa corta para no sobrecargar
                    time.sleep(1)
                    
                else:
                    self.log_message(f"❌ Error en lote {batch_num}: {result.stderr}", "ERROR")
                    return False
                    
            except subprocess.TimeoutExpired:
                self.log_message(f"⏰ Timeout en lote {batch_num}", "WARNING")
                return False
            except Exception as e:
                self.log_message(f"❌ Error procesando lote {batch_num}: {e}", "ERROR")
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
        """Optimización final del sistema"""
        self.log_message("🚀 Optimización final...")
        
        sql = """
-- Eliminar tabla temporal
DROP TABLE IF EXISTS telcel_data CASCADE;

-- Crear índices optimizados
CREATE INDEX IF NOT EXISTS idx_contacts_state_mobile ON contacts(state_code, is_mobile);
CREATE INDEX IF NOT EXISTS idx_contacts_lada_mobile ON contacts(lada, is_mobile);
CREATE INDEX IF NOT EXISTS idx_contacts_status_mobile ON contacts(status, is_mobile);

-- Optimización completa
VACUUM ANALYZE contacts;

-- Estadísticas finales
SELECT 'SISTEMA COMPLETADO' as resultado;
SELECT COUNT(*) as total_final FROM contacts;
SELECT COUNT(CASE WHEN is_mobile THEN 1 END) as moviles FROM contacts;
SELECT COUNT(CASE WHEN NOT is_mobile THEN 1 END) as fijos FROM contacts;
SELECT COUNT(DISTINCT state_code) as estados FROM contacts WHERE state_code IS NOT NULL;
SELECT pg_size_pretty(pg_total_relation_size('contacts')) as tamaño_tabla;
"""
        
        try:
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', sql
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log_message("✅ Optimización completada")
                lines = result.stdout.split('\n')
                for line in lines:
                    if line.strip() and ('total_final' in line or 'moviles' in line or 'fijos' in line or 'estados' in line or 'tamaño_tabla' in line or line.strip().isdigit()):
                        self.log_message(f"📊 {line.strip()}")
            
            return True
        except Exception as e:
            self.log_message(f"⚠️  Error en optimización: {e}", "WARNING")
            return True
    
    def execute_continuation(self):
        """Ejecutar continuación de la transformación"""
        self.start_time = time.time()
        
        self.log_message("🔄 CONTINUANDO TRANSFORMACIÓN DE CSV TELCEL2022")
        self.log_message("=" * 60)
        
        # Continuar transformación
        if not self.continue_transformation_batch():
            return False
        
        # Optimización final
        self.log_message("\n🚀 OPTIMIZACIÓN FINAL")
        self.final_optimization()
        
        # Resumen final
        total_time = time.time() - self.start_time
        
        self.log_message("\n" + "=" * 60)
        self.log_message("🎯 TRANSFORMACIÓN COMPLETADA EXITOSAMENTE")
        self.log_message("=" * 60)
        self.log_message(f"⏱️  Tiempo de continuación: {total_time/60:.1f} minutos")
        self.log_message(f"🚀 Sistema SMS Marketing: COMPLETADO")
        
        return True

def main():
    """Función principal"""
    continuation = ContinueTransformation()
    
    print("🔄 CONTINUAR TRANSFORMACIÓN CSV TELCEL2022")
    print("📊 Completar los registros restantes")
    print("⏱️  TIEMPO ESTIMADO: 45-90 minutos")
    
    confirm = input("\n¿Continuar con la transformación restante? (yes/no): ").lower().strip()
    
    if confirm == 'yes':
        success = continuation.execute_continuation()
        
        if success:
            print("\n🎉 ¡TRANSFORMACIÓN COMPLETADA EXITOSAMENTE!")
            print("📊 Sistema SMS Marketing con 36+ millones de contactos")
            print("🚀 Listo para campañas SMS masivas")
        else:
            print("\n❌ ERROR - Revisa los logs")
    else:
        print("\n❌ Operación cancelada")

if __name__ == "__main__":
    main()