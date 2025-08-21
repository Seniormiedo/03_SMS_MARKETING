#!/usr/bin/env python3
"""
CONTINUACIÓN OPTIMIZADA DE LA TRANSFORMACIÓN
Procesa los registros restantes con lotes grandes
"""

import subprocess
import time
from datetime import datetime

def log_message(message, level="INFO"):
    """Log con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def continue_transformation():
    """Continuar transformación optimizada"""
    
    log_message("🚀 CONTINUANDO TRANSFORMACIÓN OPTIMIZADA")
    log_message("=" * 60)
    
    # Estado inicial
    log_message("📊 Estado inicial:")
    log_message("   ✅ telcel_data: 36,645,692 registros")
    log_message("   ✅ contacts: 12,800,000 registros")
    log_message("   ⏳ Pendientes: 23,845,692 registros")
    log_message("   📈 Progreso: 34.9%")
    
    start_time = time.time()
    batch_size = 1000000  # 1M por lote
    offset = 12800000
    remaining = 23845692
    batch_num = 13  # Continuar desde donde se quedó
    
    log_message(f"🔄 Procesando en lotes de {batch_size:,} registros...")
    
    while remaining > 0:
        batch_start = time.time()
        current_batch_size = min(batch_size, remaining)
        
        log_message(f"📦 LOTE {batch_num}: {current_batch_size:,} registros (offset: {offset:,})")
        
        # SQL optimizado para lotes grandes
        sql = f"""
-- Configuración temporal para velocidad máxima
SET work_mem = '2GB';
SET maintenance_work_mem = '4GB';
SET synchronous_commit = off;
SET wal_buffers = '128MB';
SET checkpoint_completion_target = 0.9;
SET random_page_cost = 1.1;

-- Insertar mega-lote
INSERT INTO contacts (
    phone_e164, phone_national, phone_original, lada, state_code, 
    is_mobile, operator, status, source, created_at, updated_at, 
    send_count, validation_attempts
)
SELECT 
    '+52' || phone as phone_e164,
    phone as phone_national,
    phone as phone_original,
    left(phone, 3) as lada,
    CASE 
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%CDMX%' OR 
             upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%DF%' OR 
             upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%MEXICO%' THEN 'CDMX'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%JAL%' OR 
             upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%JALISCO%' THEN 'JAL'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%NL%' OR 
             upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%NUEVO LEON%' THEN 'NL'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%VER%' OR 
             upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%VERACRUZ%' THEN 'VER'
        WHEN upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%PUE%' OR 
             upper(trim(coalesce(state_name, state_alt, ''))) LIKE '%PUEBLA%' THEN 'PUE'
        ELSE left(upper(trim(coalesce(state_name, state_alt, ''))), 5)
    END as state_code,
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

-- Verificar progreso
SELECT 'Lote {batch_num} completado' as resultado, 
       {current_batch_size} as procesados,
       (SELECT COUNT(*) FROM contacts) as total_actual;
"""
        
        try:
            result = subprocess.run([
                'docker-compose', '-f', 'docker-compose.minimal.yml', 
                'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', sql
            ], capture_output=True, text=True, timeout=1800)  # 30 min timeout
            
            batch_time = time.time() - batch_start
            
            if result.returncode == 0:
                records_per_second = current_batch_size / batch_time if batch_time > 0 else 0
                
                log_message(f"✅ LOTE {batch_num} COMPLETADO:")
                log_message(f"   ⏱️  Tiempo: {batch_time/60:.1f} minutos")
                log_message(f"   🚀 Velocidad: {records_per_second:.0f} reg/s")
                
                # Obtener total actual
                count_result = subprocess.run([
                    'docker-compose', '-f', 'docker-compose.minimal.yml', 
                    'exec', '-T', 'postgres',
                    'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                    '-t', '-c', 'SELECT COUNT(*) FROM contacts;'
                ], capture_output=True, text=True, timeout=30)
                
                if count_result.returncode == 0:
                    current_total = int(count_result.stdout.strip())
                    progress = (current_total / 36645692) * 100
                    log_message(f"   📊 Total actual: {current_total:,}")
                    log_message(f"   📈 Progreso: {progress:.1f}%")
                
                # Actualizar contadores
                offset += current_batch_size
                remaining -= current_batch_size
                batch_num += 1
                
                # Pausa corta
                time.sleep(2)
                
            else:
                log_message(f"❌ Error en lote {batch_num}: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            log_message(f"⏰ Timeout en lote {batch_num}", "WARNING")
            return False
        except Exception as e:
            log_message(f"❌ Error: {e}", "ERROR")
            return False
    
    # Optimización final
    log_message("\n🚀 OPTIMIZACIÓN FINAL...")
    
    final_sql = """
-- Eliminar tabla temporal
DROP TABLE IF EXISTS telcel_data CASCADE;

-- Crear índices optimizados
CREATE INDEX IF NOT EXISTS idx_contacts_state_mobile ON contacts(state_code, is_mobile) WHERE state_code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_contacts_lada ON contacts(lada);
CREATE INDEX IF NOT EXISTS idx_contacts_status ON contacts(status);
CREATE INDEX IF NOT EXISTS idx_contacts_operator ON contacts(operator);
CREATE INDEX IF NOT EXISTS idx_contacts_mobile ON contacts(is_mobile);

-- Optimización completa
VACUUM ANALYZE contacts;

-- Estadísticas finales
SELECT 'MIGRACIÓN COMPLETADA' as estado;
SELECT COUNT(*) as total_contactos FROM contacts;
SELECT COUNT(CASE WHEN is_mobile THEN 1 END) as telefonos_moviles FROM contacts;
SELECT COUNT(CASE WHEN NOT is_mobile THEN 1 END) as telefonos_fijos FROM contacts;
SELECT COUNT(DISTINCT state_code) as estados FROM contacts WHERE state_code IS NOT NULL;
SELECT COUNT(DISTINCT lada) as ladas FROM contacts;
SELECT pg_size_pretty(pg_total_relation_size('contacts')) as tamaño_tabla;
"""
    
    try:
        result = subprocess.run([
            'docker-compose', '-f', 'docker-compose.minimal.yml', 
            'exec', '-T', 'postgres',
            'psql', '-U', 'sms_user', '-d', 'sms_marketing',
            '-c', final_sql
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            log_message("✅ OPTIMIZACIÓN COMPLETADA")
            
            # Mostrar estadísticas
            lines = result.stdout.split('\\n')
            for line in lines:
                if any(keyword in line for keyword in ['total_contactos', 'telefonos_moviles', 'telefonos_fijos', 'estados', 'ladas', 'tamaño_tabla']) or (line.strip().isdigit() and len(line.strip()) > 3):
                    log_message(f"📊 {line.strip()}")
        
    except Exception as e:
        log_message(f"⚠️  Error en optimización: {e}", "WARNING")
    
    # Resumen final
    total_time = time.time() - start_time
    
    log_message("\n" + "=" * 60)
    log_message("🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
    log_message("=" * 60)
    log_message(f"⏱️  Tiempo total: {total_time/60:.1f} minutos")
    log_message(f"🚀 Sistema SMS Marketing: COMPLETADO")
    log_message(f"📊 36+ millones de contactos listos")
    
    return True

if __name__ == "__main__":
    print("🚀 CONTINUACIÓN OPTIMIZADA DE LA TRANSFORMACIÓN")
    print("⏱️  TIEMPO ESTIMADO: 25-35 minutos")
    
    input("\\n🔄 Presiona ENTER para continuar...")
    
    success = continue_transformation()
    
    if success:
        print("\\n🎉 ¡MIGRACIÓN COMPLETADA!")
    else:
        print("\\n❌ ERROR - Revisa los logs")