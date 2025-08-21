#!/usr/bin/env python3
"""
Test de migración COPY corregido con todas las columnas
"""

import sqlite3
import subprocess
import tempfile
import os
import sys

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.migration_manager import DataTransformer

def test_copy_migration():
    """Test de migración usando COPY con todas las columnas"""
    
    print("🧪 TEST DE MIGRACIÓN COPY CORREGIDO")
    print("="*50)
    
    # Limpiar tabla
    print("🧹 Limpiando tabla...")
    subprocess.run([
        'docker-compose', 'exec', '-T', 'postgres',
        'psql', '-U', 'sms_user', '-d', 'sms_marketing',
        '-c', 'TRUNCATE TABLE contacts RESTART IDENTITY CASCADE;'
    ], capture_output=True)
    
    # Obtener 100 registros de prueba
    print("📊 Obteniendo registros de prueba...")
    conn = sqlite3.connect("numeros.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM numeros LIMIT 100")
    test_records = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    print(f"✅ Obtenidos {len(test_records)} registros")
    
    # Transformar registros
    print("🔄 Transformando registros...")
    transformer = DataTransformer()
    csv_lines = []
    
    for record in test_records:
        result = transformer.transform_record(record)
        
        if result["success"]:
            data = result["data"]
            
            def format_csv_value(value):
                if value is None:
                    return "\\N"
                elif isinstance(value, str):
                    escaped = value.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")
                    return escaped
                elif isinstance(value, bool):
                    return "t" if value else "f"
                else:
                    return str(value)
            
            # TODAS las columnas en el orden correcto según la tabla
            csv_line = "\t".join([
                # Columnas automáticas (id, created_at, updated_at se manejan por PostgreSQL)
                format_csv_value(data.get("phone_e164")),           # phone_e164
                format_csv_value(data.get("phone_national")),       # phone_national  
                format_csv_value(data.get("phone_original")),       # phone_original
                format_csv_value(data.get("full_name")),            # full_name
                format_csv_value(data.get("address")),              # address
                format_csv_value(data.get("neighborhood")),         # neighborhood
                format_csv_value(data.get("lada")),                 # lada
                format_csv_value(data.get("state_code")),           # state_code
                format_csv_value(data.get("state_name")),           # state_name
                format_csv_value(data.get("municipality")),         # municipality
                format_csv_value(data.get("city")),                 # city
                format_csv_value(data.get("is_mobile")),            # is_mobile
                format_csv_value(data.get("operator")),             # operator
                format_csv_value(data.get("status", "UNKNOWN")),    # status
                format_csv_value(None),                             # status_updated_at
                format_csv_value(None),                             # status_source
                "0",                                                # send_count
                format_csv_value(None),                             # last_sent_at
                format_csv_value(None),                             # opt_out_at
                format_csv_value(None),                             # opt_out_method
                format_csv_value(None),                             # last_validated_at
                "0",                                                # validation_attempts
                format_csv_value(data.get("source", "TELCEL2022")), # source
                format_csv_value(None)                              # import_batch_id
            ])
            
            csv_lines.append(csv_line)
    
    print(f"✅ Transformados: {len(csv_lines)} registros")
    
    if not csv_lines:
        print("❌ No hay datos para insertar")
        return
    
    # Crear archivo temporal
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
        temp_file.write('\n'.join(csv_lines))
        temp_file_path = temp_file.name
    
    print(f"📄 Archivo temporal creado: {temp_file_path}")
    
    try:
        # Copiar al contenedor
        print("📋 Copiando archivo al contenedor...")
        copy_result = subprocess.run([
            'docker', 'cp', temp_file_path, 'sms_postgres:/tmp/test_batch.csv'
        ], capture_output=True, text=True)
        
        if copy_result.returncode != 0:
            print(f"❌ Error copiando: {copy_result.stderr}")
            return
        
        print("✅ Archivo copiado al contenedor")
        
        # Ejecutar COPY FROM con TODAS las columnas
        copy_sql = """
        COPY contacts (
            phone_e164, phone_national, phone_original, full_name, address, neighborhood,
            lada, state_code, state_name, municipality, city, is_mobile, operator,
            status, status_updated_at, status_source, send_count, last_sent_at,
            opt_out_at, opt_out_method, last_validated_at, validation_attempts,
            source, import_batch_id
        ) FROM '/tmp/test_batch.csv' 
        WITH (FORMAT csv, DELIMITER E'\\t', NULL '\\N')
        ON CONFLICT (phone_e164) DO NOTHING;
        """
        
        print("💾 Ejecutando COPY FROM...")
        copy_result = subprocess.run([
            'docker-compose', 'exec', '-T', 'postgres',
            'psql', '-U', 'sms_user', '-d', 'sms_marketing',
            '-c', copy_sql
        ], capture_output=True, text=True)
        
        print(f"📤 Resultado COPY: {copy_result.stdout}")
        
        if copy_result.returncode != 0:
            print(f"❌ Error en COPY: {copy_result.stderr}")
        else:
            print("✅ COPY ejecutado exitosamente")
        
        # Verificar resultado
        count_result = subprocess.run([
            'docker-compose', 'exec', '-T', 'postgres',
            'psql', '-U', 'sms_user', '-d', 'sms_marketing',
            '-t', '-c', 'SELECT COUNT(*) FROM contacts;'
        ], capture_output=True, text=True)
        
        if count_result.returncode == 0:
            final_count = int(count_result.stdout.strip())
            print(f"📊 RESULTADO FINAL: {final_count} registros insertados")
            
            if final_count > 0:
                print("🎉 ¡TEST EXITOSO! El problema está corregido")
                
                # Mostrar muestra
                sample_result = subprocess.run([
                    'docker-compose', 'exec', '-T', 'postgres',
                    'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                    '-c', 'SELECT phone_e164, full_name, state_code, status FROM contacts LIMIT 3;'
                ], capture_output=True, text=True)
                
                print("📋 Muestra de registros insertados:")
                print(sample_result.stdout)
            else:
                print("❌ Aún no se insertaron registros")
        
        # Limpiar archivo del contenedor
        subprocess.run([
            'docker-compose', 'exec', '-T', 'postgres',
            'rm', '-f', '/tmp/test_batch.csv'
        ], capture_output=True)
        
    finally:
        # Limpiar archivo temporal local
        try:
            os.unlink(temp_file_path)
        except:
            pass

if __name__ == "__main__":
    test_copy_migration()