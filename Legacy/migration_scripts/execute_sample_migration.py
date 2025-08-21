#!/usr/bin/env python3
"""
Ejecutar migración de muestra - 1000 registros para validar proceso
DÍA 4 - FASE 4.2
"""

import asyncio
import sqlite3
import time
from datetime import datetime
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.migration_manager import MigrationManager, DataTransformer

async def execute_sample_migration():
    """Ejecutar migración de muestra de 1000 registros"""
    
    print("🚀 DÍA 4 - FASE 4.2: MIGRACIÓN DE MUESTRA")
    print("="*60)
    
    # Verificar que PostgreSQL esté disponible usando conexión directa
    print("🔍 Verificando PostgreSQL...")
    import subprocess
    try:
        result = subprocess.run([
            'docker-compose', 'exec', '-T', 'postgres', 
            'psql', '-U', 'sms_user', '-d', 'sms_marketing', 
            '-c', 'SELECT 1;'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ PostgreSQL disponible")
        else:
            print("❌ PostgreSQL no disponible")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando PostgreSQL: {e}")
        return False
    
    # Obtener muestra de 1000 registros de SQLite
    print("📊 Obteniendo muestra de 1000 registros...")
    
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
    
    print(f"✅ Obtenidos {len(sample_records)} registros de muestra")
    
    # Transformar registros
    print("🔄 Transformando registros...")
    
    transformer = DataTransformer()
    transformed_records = []
    failed_records = []
    
    for i, record in enumerate(sample_records, 1):
        if i % 100 == 0:
            print(f"   Procesando {i}/1000...")
            
        result = transformer.transform_record(record)
        
        if result["success"]:
            transformed_records.append(result["data"])
        else:
            failed_records.append({
                "original": record,
                "error": result["error"]
            })
    
    success_rate = len(transformed_records) / len(sample_records)
    
    print(f"✅ Transformación completada:")
    print(f"   📊 Exitosos: {len(transformed_records)}")
    print(f"   ❌ Fallidos: {len(failed_records)}")
    print(f"   📈 Tasa de éxito: {success_rate:.1%}")
    
    if success_rate < 0.95:
        print("⚠️  Tasa de éxito baja - Revisar errores")
        for error in failed_records[:5]:  # Mostrar primeros 5 errores
            print(f"   Error: {error['error']}")
    
    # Insertar registros en PostgreSQL usando comando directo
    print("💾 Insertando registros en PostgreSQL...")
    
    if transformed_records:
        # Crear archivo SQL temporal
        sql_file = "temp_insert.sql"
        
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write("BEGIN;\n")
            
            for record in transformed_records:
                # Escapar valores NULL y strings
                def escape_value(value):
                    if value is None:
                        return "NULL"
                    elif isinstance(value, str):
                        escaped = value.replace("'", "''")
                        return f"'{escaped}'"
                    elif isinstance(value, bool):
                        return "TRUE" if value else "FALSE"
                    else:
                        return str(value)
                
                # Preparar valores
                values = [
                    escape_value(record.get("phone_e164")),
                    escape_value(record.get("phone_national")),
                    escape_value(record.get("phone_original")),
                    escape_value(record.get("full_name")),
                    escape_value(record.get("address")),
                    escape_value(record.get("neighborhood")),
                    escape_value(record.get("lada")),
                    escape_value(record.get("state_code")),
                    escape_value(record.get("state_name")),
                    escape_value(record.get("municipality")),
                    escape_value(record.get("city")),
                    escape_value(record.get("is_mobile")),
                    escape_value(record.get("operator")),
                    f"'{record.get('status', 'UNKNOWN')}'",
                    f"'{record.get('source', 'TELCEL2022')}'",
                    "NOW()",  # created_at
                    "NOW()"   # updated_at
                ]
                
                sql = f"""
INSERT INTO contacts (
    phone_e164, phone_national, phone_original, full_name, address, neighborhood,
    lada, state_code, state_name, municipality, city, is_mobile, operator,
    status, source, created_at, updated_at
) VALUES ({', '.join(values)})
ON CONFLICT (phone_e164) DO NOTHING;
"""
                f.write(sql)
            
            f.write("COMMIT;\n")
        
        # Ejecutar SQL
        try:
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-f', f'/tmp/{sql_file}'
            ], input=open(sql_file, 'r', encoding='utf-8').read(), 
            capture_output=True, text=True, timeout=60)
            
            if "COMMIT" in result.stdout:
                print("✅ Registros insertados exitosamente")
                
                # Verificar conteo
                count_result = subprocess.run([
                    'docker-compose', 'exec', '-T', 'postgres',
                    'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                    '-c', 'SELECT COUNT(*) FROM contacts;'
                ], capture_output=True, text=True)
                
                if count_result.returncode == 0:
                    lines = count_result.stdout.strip().split('\n')
                    for line in lines:
                        if line.strip().isdigit():
                            count = int(line.strip())
                            print(f"📊 Total en PostgreSQL: {count:,} registros")
                            break
                
            else:
                print(f"❌ Error en inserción: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error ejecutando SQL: {e}")
        
        finally:
            # Limpiar archivo temporal
            if os.path.exists(sql_file):
                os.remove(sql_file)
    
    print("\n✅ FASE 4.2 COMPLETADA - Migración de muestra exitosa")
    return True

async def main():
    """Función principal"""
    success = await execute_sample_migration()
    
    if success:
        print("\n🎯 ¡Migración de muestra exitosa!")
        print("🚀 Sistema listo para migración completa")
    else:
        print("\n❌ Error en migración de muestra")

if __name__ == "__main__":
    asyncio.run(main())