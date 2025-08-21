#!/usr/bin/env python3
"""
CONTINUACIÓN SIMPLE DE LA TRANSFORMACIÓN
Sin parámetros que requieren reinicio de PostgreSQL
"""

import subprocess
import time
from datetime import datetime

def log_message(message, level="INFO"):
    """Log con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def continue_transformation():
    """Continuar transformación simple y rápida"""
    
    log_message("🚀 CONTINUANDO TRANSFORMACIÓN SIMPLE")
    log_message("=" * 60)
    
    start_time = time.time()
    batch_size = 500000  # 500K por lote (probado y funcional)
    offset = 12800000
    total_source = 36645692
    batch_num = 13
    
    log_message(f"🔄 Procesando desde offset {offset:,} en lotes de {batch_size:,}...")
    
    while offset < total_source:
        batch_start = time.time()
        current_batch_size = min(batch_size, total_source - offset)
        
        log_message(f"📦 LOTE {batch_num}: {current_batch_size:,} registros (offset: {offset:,})")
        
        # SQL simplificado y probado
        sql = f"""
INSERT INTO contacts (
    phone_e164, phone_national, phone_original, lada, 
    is_mobile, operator, status, source, created_at, updated_at, 
    send_count, validation_attempts
)
SELECT 
    '+52' || phone as phone_e164,
    phone as phone_national,
    phone as phone_original,
    left(phone, 3) as lada,
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
    SELECT phone FROM telcel_data 
    WHERE phone IS NOT NULL AND phone ~ '^[0-9]{{10}}$'
    ORDER BY phone
    LIMIT {current_batch_size} OFFSET {offset}
) t
ON CONFLICT (phone_e164) DO NOTHING;
"""
        
        try:
            result = subprocess.run([
                'docker-compose', '-f', 'docker-compose.minimal.yml', 
                'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', sql
            ], capture_output=True, text=True, timeout=900)  # 15 min timeout
            
            batch_time = time.time() - batch_start
            
            if result.returncode == 0:
                records_per_second = current_batch_size / batch_time if batch_time > 0 else 0
                
                log_message(f"✅ LOTE {batch_num} COMPLETADO:")
                log_message(f"   ⏱️  Tiempo: {batch_time:.1f}s")
                log_message(f"   🚀 Velocidad: {records_per_second:.0f} reg/s")
                
                # Obtener total actual cada 5 lotes
                if batch_num % 5 == 0:
                    count_result = subprocess.run([
                        'docker-compose', '-f', 'docker-compose.minimal.yml', 
                        'exec', '-T', 'postgres',
                        'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                        '-t', '-c', 'SELECT COUNT(*) FROM contacts;'
                    ], capture_output=True, text=True, timeout=30)
                    
                    if count_result.returncode == 0:
                        current_total = int(count_result.stdout.strip())
                        progress = (current_total / total_source) * 100
                        log_message(f"   📊 Total actual: {current_total:,}")
                        log_message(f"   📈 Progreso: {progress:.1f}%")
                
                # Actualizar contadores
                offset += current_batch_size
                batch_num += 1
                
                # Pausa corta
                time.sleep(1)
                
            else:
                log_message(f"❌ Error en lote {batch_num}: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            log_message(f"⏰ Timeout en lote {batch_num}", "WARNING")
            return False
        except Exception as e:
            log_message(f"❌ Error: {e}", "ERROR")
            return False
    
    # Verificación final
    log_message("\n📊 VERIFICACIÓN FINAL...")
    
    try:
        count_result = subprocess.run([
            'docker-compose', '-f', 'docker-compose.minimal.yml', 
            'exec', '-T', 'postgres',
            'psql', '-U', 'sms_user', '-d', 'sms_marketing',
            '-c', """
SELECT 'MIGRACIÓN COMPLETADA' as estado;
SELECT COUNT(*) as total_contactos FROM contacts;
SELECT COUNT(CASE WHEN is_mobile THEN 1 END) as telefonos_moviles FROM contacts;
SELECT COUNT(CASE WHEN NOT is_mobile THEN 1 END) as telefonos_fijos FROM contacts;
SELECT COUNT(DISTINCT lada) as ladas_unicas FROM contacts;
"""
        ], capture_output=True, text=True, timeout=60)
        
        if count_result.returncode == 0:
            log_message("✅ ESTADÍSTICAS FINALES:")
            lines = count_result.stdout.split('\\n')
            for line in lines:
                if line.strip() and ('total_contactos' in line or 'telefonos_' in line or 'ladas_' in line or line.strip().isdigit()):
                    log_message(f"   📊 {line.strip()}")
    
    except Exception as e:
        log_message(f"⚠️  Error en verificación: {e}", "WARNING")
    
    # Resumen final
    total_time = time.time() - start_time
    
    log_message("\n" + "=" * 60)
    log_message("🎉 TRANSFORMACIÓN COMPLETADA")
    log_message("=" * 60)
    log_message(f"⏱️  Tiempo total: {total_time/60:.1f} minutos")
    log_message(f"🚀 Sistema SMS Marketing: LISTO")
    
    return True

if __name__ == "__main__":
    print("🚀 CONTINUACIÓN SIMPLE DE LA TRANSFORMACIÓN")
    print("📊 Desde 12.8M hasta 36.6M registros")
    print("⏱️  TIEMPO ESTIMADO: 30-40 minutos")
    
    input("\\n🔄 Presiona ENTER para continuar...")
    
    success = continue_transformation()
    
    if success:
        print("\\n🎉 ¡MIGRACIÓN COMPLETADA!")
    else:
        print("\\n❌ ERROR - Revisa los logs")