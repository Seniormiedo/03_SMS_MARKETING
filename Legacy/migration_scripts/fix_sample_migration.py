#!/usr/bin/env python3
"""
Corrección: Migración real de 1000 registros usando conexión directa
"""

import asyncio
import sqlite3
import subprocess
import sys
import os
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.migration_manager import DataTransformer

async def execute_real_migration():
    """Ejecutar migración real de 1000 registros"""
    
    print("🔧 CORRECCIÓN - MIGRACIÓN REAL DE 1000 REGISTROS")
    print("="*60)
    
    # Limpiar tabla para empezar limpio
    print("🧹 Limpiando tabla contacts...")
    result = subprocess.run([
        'docker-compose', 'exec', '-T', 'postgres',
        'psql', '-U', 'sms_user', '-d', 'sms_marketing',
        '-c', 'TRUNCATE TABLE contacts RESTART IDENTITY;'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Tabla limpiada")
    else:
        print(f"❌ Error limpiando tabla: {result.stderr}")
        return False
    
    # Obtener muestra de 1000 registros de SQLite
    print("📊 Obteniendo 1000 registros aleatorios de SQLite...")
    
    sqlite_conn = sqlite3.connect("numeros.db")
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()
    
    cursor.execute("""
        SELECT * FROM numeros 
        ORDER BY RANDOM() 
        LIMIT 1000
    """)
    
    sample_records = [dict(row) for row in cursor.fetchall()]
    sqlite_conn.close()
    
    print(f"✅ Obtenidos {len(sample_records)} registros de SQLite")
    
    # Transformar registros
    print("🔄 Transformando registros...")
    
    transformer = DataTransformer()
    successful_inserts = 0
    failed_inserts = 0
    
    # Insertar uno por uno para evitar problemas de archivo
    for i, record in enumerate(sample_records, 1):
        if i % 100 == 0:
            print(f"   Procesando {i}/1000...")
        
        # Transformar registro
        result = transformer.transform_record(record)
        
        if not result["success"]:
            failed_inserts += 1
            continue
        
        data = result["data"]
        
        # Escapar valores para SQL
        def escape_sql(value):
            if value is None:
                return "NULL"
            elif isinstance(value, str):
                return f"'{value.replace(chr(39), chr(39)+chr(39))}'"
            elif isinstance(value, bool):
                return "TRUE" if value else "FALSE"
            else:
                return str(value)
        
        # Crear comando SQL
        sql_command = f"""
INSERT INTO contacts (
    phone_e164, phone_national, phone_original, full_name, address, neighborhood,
    lada, state_code, state_name, municipality, city, is_mobile, operator,
    status, source, created_at, updated_at
) VALUES (
    {escape_sql(data.get("phone_e164"))},
    {escape_sql(data.get("phone_national"))},
    {escape_sql(data.get("phone_original"))},
    {escape_sql(data.get("full_name"))},
    {escape_sql(data.get("address"))},
    {escape_sql(data.get("neighborhood"))},
    {escape_sql(data.get("lada"))},
    {escape_sql(data.get("state_code"))},
    {escape_sql(data.get("state_name"))},
    {escape_sql(data.get("municipality"))},
    {escape_sql(data.get("city"))},
    {escape_sql(data.get("is_mobile"))},
    {escape_sql(data.get("operator"))},
    {escape_sql(data.get("status", "UNKNOWN"))},
    {escape_sql(data.get("source", "TELCEL2022"))},
    NOW(),
    NOW()
) ON CONFLICT (phone_e164) DO NOTHING;
"""
        
        # Ejecutar inserción
        try:
            insert_result = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', sql_command
            ], capture_output=True, text=True, timeout=5)
            
            if insert_result.returncode == 0 and "INSERT 0 1" in insert_result.stdout:
                successful_inserts += 1
            elif "INSERT 0 0" in insert_result.stdout:
                # Conflicto - número duplicado
                successful_inserts += 1  # Contar como exitoso aunque no se insertó
            else:
                failed_inserts += 1
                if i <= 5:  # Mostrar primeros 5 errores
                    print(f"   Error en registro {i}: {insert_result.stderr[:100]}")
                
        except subprocess.TimeoutExpired:
            failed_inserts += 1
            if i <= 5:
                print(f"   Timeout en registro {i}")
        except Exception as e:
            failed_inserts += 1
            if i <= 5:
                print(f"   Excepción en registro {i}: {e}")
    
    # Verificar resultado final
    print("\n📊 Verificando resultado final...")
    
    count_result = subprocess.run([
        'docker-compose', 'exec', '-T', 'postgres',
        'psql', '-U', 'sms_user', '-d', 'sms_marketing',
        '-c', 'SELECT COUNT(*) FROM contacts;'
    ], capture_output=True, text=True)
    
    if count_result.returncode == 0:
        lines = count_result.stdout.strip().split('\n')
        for line in lines:
            if line.strip().isdigit():
                final_count = int(line.strip())
                break
        else:
            final_count = 0
    else:
        final_count = 0
    
    # Mostrar estadísticas finales
    print("\n" + "="*60)
    print("📊 RESULTADO FINAL DE MIGRACIÓN CORREGIDA")
    print("="*60)
    print(f"📱 Registros procesados: {len(sample_records):,}")
    print(f"✅ Inserciones exitosas: {successful_inserts:,}")
    print(f"❌ Inserciones fallidas: {failed_inserts:,}")
    print(f"📊 Total en PostgreSQL: {final_count:,}")
    print(f"🎯 Tasa de éxito: {(successful_inserts/len(sample_records)*100):.1f}%")
    
    if final_count >= 900:  # 90% o más
        print("✅ MIGRACIÓN EXITOSA - Objetivo cumplido")
        return True
    else:
        print("⚠️  MIGRACIÓN PARCIAL - Revisar errores")
        return False

async def main():
    """Función principal"""
    success = await execute_real_migration()
    
    if success:
        print("\n🎯 ¡Migración real completada exitosamente!")
    else:
        print("\n🔧 Migración completada con advertencias")

if __name__ == "__main__":
    asyncio.run(main())