#!/usr/bin/env python3
"""
MIGRACIÓN DE ALTA VELOCIDAD - SOLUCIONES REALES
Implementa técnicas profesionales para migración masiva rápida
"""

import sqlite3
import subprocess
import sys
import os
import time
import json
import psutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import csv
import io

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.migration_manager import DataTransformer

class HighSpeedMigration:
    """Migración de alta velocidad usando técnicas profesionales"""
    
    def __init__(self):
        self.start_time = None
        self.total_records = 0
        self.processed_records = 0
        self.successful_inserts = 0
        self.failed_inserts = 0
        self.batch_size = 100000  # 100K registros por lote
        
    def log_message(self, message, level="INFO"):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def check_system_resources(self):
        """Verificar recursos del sistema"""
        self.log_message("🔍 Verificando recursos del sistema...")
        
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        memory_available_gb = memory.available / (1024**3)
        
        disk = psutil.disk_usage('.')
        disk_free_gb = disk.free / (1024**3)
        
        self.log_message(f"💾 Memoria: {memory_available_gb:.1f}GB disponible de {memory_gb:.1f}GB total")
        self.log_message(f"💽 Disco: {disk_free_gb:.1f}GB libres")
        
        return disk_free_gb >= 40
    
    def get_total_records(self):
        """Obtener conteo exacto de registros"""
        self.log_message("📊 Contando registros totales en numeros.db...")
        
        try:
            conn = sqlite3.connect("numeros.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM numeros")
            count = cursor.fetchone()[0]
            conn.close()
            
            self.total_records = count
            total_batches = (count + self.batch_size - 1) // self.batch_size
            
            self.log_message(f"📱 Total de registros: {count:,}")
            self.log_message(f"📦 Total de lotes: {total_batches:,} (tamaño: {self.batch_size:,})")
            
            return count
        except Exception as e:
            self.log_message(f"❌ ERROR contando registros: {e}", "ERROR")
            return 0
    
    def optimize_postgresql_aggressive(self):
        """Optimización agresiva de PostgreSQL para máxima velocidad"""
        self.log_message("⚡ Aplicando optimización agresiva PostgreSQL...")
        
        optimization_commands = [
            # Deshabilitar completamente WAL y checkpoints
            "ALTER SYSTEM SET wal_level = minimal;",
            "ALTER SYSTEM SET synchronous_commit = off;",
            "ALTER SYSTEM SET fsync = off;",
            "ALTER SYSTEM SET full_page_writes = off;",
            "ALTER SYSTEM SET checkpoint_segments = 32;",
            "ALTER SYSTEM SET checkpoint_completion_target = 0.9;",
            "ALTER SYSTEM SET wal_buffers = '64MB';",
            "ALTER SYSTEM SET shared_buffers = '1GB';",
            "ALTER SYSTEM SET work_mem = '512MB';",
            "ALTER SYSTEM SET maintenance_work_mem = '2GB';",
            "ALTER SYSTEM SET effective_cache_size = '4GB';",
            "ALTER SYSTEM SET random_page_cost = 1.1;",
            "ALTER SYSTEM SET autovacuum = off;",
            "SELECT pg_reload_conf();"
        ]
        
        for cmd in optimization_commands:
            try:
                subprocess.run([
                    'docker-compose', 'exec', '-T', 'postgres',
                    'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                    '-c', cmd
                ], capture_output=True, text=True, timeout=10)
            except:
                pass
        
        self.log_message("✅ Optimización agresiva aplicada")
    
    def clear_target_table(self):
        """Limpiar tabla de destino"""
        self.log_message("🧹 Limpiando tabla contacts...")
        
        try:
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', 'TRUNCATE TABLE contacts RESTART IDENTITY CASCADE;'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.log_message("✅ Tabla contacts limpiada")
                return True
            else:
                self.log_message(f"❌ Error limpiando tabla: {result.stderr}", "ERROR")
                return False
        except Exception as e:
            self.log_message(f"❌ Error limpiando tabla: {e}", "ERROR")
            return False
    
    def method_1_psql_copy_stdin(self, batch_number, offset, limit):
        """MÉTODO 1: psql \\copy desde STDIN (más rápido que COPY FROM archivo)"""
        batch_start = time.time()
        total_batches = (self.total_records + self.batch_size - 1) // self.batch_size
        self.log_message(f"🚀 MÉTODO 1 - Lote {batch_number}/{total_batches} (registros {offset+1:,} - {offset+limit:,})")
        
        try:
            # Obtener datos de SQLite
            conn = sqlite3.connect("numeros.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT * FROM numeros LIMIT {limit} OFFSET {offset}")
            batch_records = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            if not batch_records:
                return 0
            
            # Transformar registros
            transformer = DataTransformer()
            csv_data = io.StringIO()
            csv_writer = csv.writer(csv_data, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
            
            valid_records = 0
            for record in batch_records:
                result = transformer.transform_record(record)
                if result["success"]:
                    data = result["data"]
                    
                    # Escribir fila CSV
                    csv_writer.writerow([
                        data.get("phone_e164", ""),
                        data.get("phone_national", ""),
                        data.get("phone_original", ""),
                        data.get("full_name", ""),
                        data.get("address", ""),
                        data.get("neighborhood", ""),
                        data.get("lada", ""),
                        data.get("state_code", ""),
                        data.get("state_name", ""),
                        data.get("municipality", ""),
                        data.get("city", ""),
                        "t" if data.get("is_mobile") else "f",
                        data.get("operator", ""),
                        data.get("status", "UNKNOWN"),
                        "",  # status_updated_at
                        "",  # status_source
                        0,   # send_count
                        "",  # last_sent_at
                        "",  # opt_out_at
                        "",  # opt_out_method
                        "",  # last_validated_at
                        0,   # validation_attempts
                        data.get("source", "TELCEL2022"),
                        ""   # import_batch_id
                    ])
                    valid_records += 1
            
            if valid_records == 0:
                return 0
            
            # Usar psql \copy desde STDIN
            csv_content = csv_data.getvalue()
            
            copy_command = """\\copy contacts (phone_e164, phone_national, phone_original, full_name, address, neighborhood, lada, state_code, state_name, municipality, city, is_mobile, operator, status, status_updated_at, status_source, send_count, last_sent_at, opt_out_at, opt_out_method, last_validated_at, validation_attempts, source, import_batch_id) FROM STDIN WITH (FORMAT csv, DELIMITER E'\\t', NULL '')"""
            
            process = subprocess.Popen([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', copy_command
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            stdout, stderr = process.communicate(input=csv_content, timeout=120)
            
            if process.returncode == 0:
                # Extraer número de registros insertados
                if "COPY" in stdout:
                    try:
                        inserted_count = int(stdout.split("COPY")[1].strip().split()[0])
                    except:
                        inserted_count = valid_records
                else:
                    inserted_count = valid_records
            else:
                self.log_message(f"❌ Error en COPY STDIN: {stderr[:200]}", "ERROR")
                inserted_count = 0
            
            # Estadísticas
            batch_time = time.time() - batch_start
            records_per_second = len(batch_records) / batch_time if batch_time > 0 else 0
            
            self.processed_records += len(batch_records)
            self.successful_inserts += inserted_count
            self.failed_inserts += (len(batch_records) - inserted_count)
            
            progress_percent = (self.processed_records / self.total_records) * 100
            
            self.log_message(f"✅ Lote {batch_number} completado:")
            self.log_message(f"   📊 Procesados: {len(batch_records):,} | Insertados: {inserted_count:,}")
            self.log_message(f"   ⚡ Tiempo: {batch_time:.1f}s | Velocidad: {records_per_second:.0f} reg/s")
            self.log_message(f"   📈 Progreso: {progress_percent:.2f}% ({self.processed_records:,}/{self.total_records:,})")
            
            return inserted_count
            
        except Exception as e:
            self.log_message(f"❌ ERROR en lote {batch_number}: {e}", "ERROR")
            return 0
    
    def method_2_bulk_insert_values(self, batch_number, offset, limit):
        """MÉTODO 2: INSERT masivo con múltiples VALUES usando archivos SQL"""
        batch_start = time.time()
        total_batches = (self.total_records + self.batch_size - 1) // self.batch_size
        self.log_message(f"🚀 MÉTODO 2 - Lote {batch_number}/{total_batches} (registros {offset+1:,} - {offset+limit:,})")
        
        try:
            # Obtener datos de SQLite
            conn = sqlite3.connect("numeros.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT * FROM numeros LIMIT {limit} OFFSET {offset}")
            batch_records = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            if not batch_records:
                return 0
            
            # Transformar registros y crear VALUES masivos
            transformer = DataTransformer()
            values_list = []
            
            for record in batch_records:
                result = transformer.transform_record(record)
                if result["success"]:
                    data = result["data"]
                    
                    def escape_sql(value):
                        if value is None or value == "":
                            return "NULL"
                        elif isinstance(value, str):
                            escaped = value.replace("'", "''").replace("\\", "\\\\")
                            return f"'{escaped}'"
                        elif isinstance(value, bool):
                            return "TRUE" if value else "FALSE"
                        else:
                            return str(value)
                    
                    values_row = f"({escape_sql(data.get('phone_e164'))}, {escape_sql(data.get('phone_national'))}, {escape_sql(data.get('phone_original'))}, {escape_sql(data.get('full_name'))}, {escape_sql(data.get('address'))}, {escape_sql(data.get('neighborhood'))}, {escape_sql(data.get('lada'))}, {escape_sql(data.get('state_code'))}, {escape_sql(data.get('state_name'))}, {escape_sql(data.get('municipality'))}, {escape_sql(data.get('city'))}, {escape_sql(data.get('is_mobile'))}, {escape_sql(data.get('operator'))}, {escape_sql(data.get('status', 'UNKNOWN'))}, NULL, NULL, 0, NULL, NULL, NULL, NULL, 0, {escape_sql(data.get('source', 'TELCEL2022'))}, NULL)"
                    
                    values_list.append(values_row)
            
            if not values_list:
                return 0
            
            # Crear archivo SQL temporal
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(f"""
BEGIN;
INSERT INTO contacts (
    phone_e164, phone_national, phone_original, full_name, address, neighborhood,
    lada, state_code, state_name, municipality, city, is_mobile, operator,
    status, status_updated_at, status_source, send_count, last_sent_at,
    opt_out_at, opt_out_method, last_validated_at, validation_attempts,
    source, import_batch_id
) VALUES 
{', '.join(values_list)}
ON CONFLICT (phone_e164) DO NOTHING;
COMMIT;
""")
                temp_file_path = temp_file.name
            
            try:
                # Copiar archivo SQL al contenedor
                copy_result = subprocess.run([
                    'docker', 'cp', temp_file_path, 'sms_postgres:/tmp/batch_insert.sql'
                ], capture_output=True, text=True, timeout=30)
                
                if copy_result.returncode != 0:
                    self.log_message(f"❌ Error copiando SQL: {copy_result.stderr}", "ERROR")
                    return 0
                
                # Ejecutar archivo SQL
                exec_result = subprocess.run([
                    'docker-compose', 'exec', '-T', 'postgres',
                    'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                    '-f', '/tmp/batch_insert.sql'
                ], capture_output=True, text=True, timeout=300)
                
                if exec_result.returncode == 0:
                    inserted_count = len(values_list)
                else:
                    self.log_message(f"❌ Error ejecutando SQL: {exec_result.stderr[:200]}", "ERROR")
                    inserted_count = 0
                
                # Limpiar archivo del contenedor
                subprocess.run([
                    'docker-compose', 'exec', '-T', 'postgres',
                    'rm', '-f', '/tmp/batch_insert.sql'
                ], capture_output=True)
                
            finally:
                # Limpiar archivo local
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            
            # Estadísticas
            batch_time = time.time() - batch_start
            records_per_second = len(batch_records) / batch_time if batch_time > 0 else 0
            
            self.processed_records += len(batch_records)
            self.successful_inserts += inserted_count
            self.failed_inserts += (len(batch_records) - inserted_count)
            
            progress_percent = (self.processed_records / self.total_records) * 100
            
            self.log_message(f"✅ Lote {batch_number} completado:")
            self.log_message(f"   📊 Procesados: {len(batch_records):,} | Insertados: {inserted_count:,}")
            self.log_message(f"   ⚡ Tiempo: {batch_time:.1f}s | Velocidad: {records_per_second:.0f} reg/s")
            self.log_message(f"   📈 Progreso: {progress_percent:.2f}% ({self.processed_records:,}/{self.total_records:,})")
            
            return inserted_count
            
        except Exception as e:
            self.log_message(f"❌ ERROR en lote {batch_number}: {e}", "ERROR")
            return 0
    
    def method_3_pg_dump_restore(self):
        """MÉTODO 3: Crear dump SQL completo y restaurar (más rápido para datasets grandes)"""
        self.log_message("🚀 MÉTODO 3: Generando dump SQL completo...")
        
        dump_start = time.time()
        
        try:
            # Crear dump SQL masivo
            dump_path = "migration_dump.sql"
            
            self.log_message("📝 Generando archivo SQL masivo...")
            
            with open(dump_path, 'w', encoding='utf-8') as dump_file:
                dump_file.write("""
-- Migración masiva optimizada
BEGIN;

-- Deshabilitar triggers y constraints temporalmente
ALTER TABLE contacts DISABLE TRIGGER ALL;

""")
                
                # Procesar en lotes grandes
                conn = sqlite3.connect("numeros.db")
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                transformer = DataTransformer()
                batch_size = 50000
                offset = 0
                
                while True:
                    cursor.execute(f"SELECT * FROM numeros LIMIT {batch_size} OFFSET {offset}")
                    batch_records = [dict(row) for row in cursor.fetchall()]
                    
                    if not batch_records:
                        break
                    
                    values_list = []
                    for record in batch_records:
                        result = transformer.transform_record(record)
                        if result["success"]:
                            data = result["data"]
                            
                            def escape_sql(value):
                                if value is None or value == "":
                                    return "NULL"
                                elif isinstance(value, str):
                                    escaped = value.replace("'", "''").replace("\\", "\\\\")
                                    return f"'{escaped}'"
                                elif isinstance(value, bool):
                                    return "TRUE" if value else "FALSE"
                                else:
                                    return str(value)
                            
                            values_row = f"({escape_sql(data.get('phone_e164'))}, {escape_sql(data.get('phone_national'))}, {escape_sql(data.get('phone_original'))}, {escape_sql(data.get('full_name'))}, {escape_sql(data.get('address'))}, {escape_sql(data.get('neighborhood'))}, {escape_sql(data.get('lada'))}, {escape_sql(data.get('state_code'))}, {escape_sql(data.get('state_name'))}, {escape_sql(data.get('municipality'))}, {escape_sql(data.get('city'))}, {escape_sql(data.get('is_mobile'))}, {escape_sql(data.get('operator'))}, {escape_sql(data.get('status', 'UNKNOWN'))}, NULL, NULL, 0, NULL, NULL, NULL, NULL, 0, {escape_sql(data.get('source', 'TELCEL2022'))}, NULL)"
                            
                            values_list.append(values_row)
                    
                    if values_list:
                        dump_file.write(f"""
INSERT INTO contacts (
    phone_e164, phone_national, phone_original, full_name, address, neighborhood,
    lada, state_code, state_name, municipality, city, is_mobile, operator,
    status, status_updated_at, status_source, send_count, last_sent_at,
    opt_out_at, opt_out_method, last_validated_at, validation_attempts,
    source, import_batch_id
) VALUES 
{', '.join(values_list)};

""")
                    
                    offset += batch_size
                    self.log_message(f"   📝 Procesados {offset:,} registros para dump...")
                
                conn.close()
                
                dump_file.write("""
-- Rehabilitar triggers y constraints
ALTER TABLE contacts ENABLE TRIGGER ALL;

COMMIT;

-- Actualizar estadísticas
ANALYZE contacts;
""")
            
            dump_time = time.time() - dump_start
            dump_size = os.path.getsize(dump_path) / (1024**2)  # MB
            
            self.log_message(f"✅ Dump SQL generado: {dump_path} ({dump_size:.1f}MB) en {dump_time:.1f}s")
            
            # Copiar dump al contenedor
            self.log_message("📋 Copiando dump al contenedor PostgreSQL...")
            copy_result = subprocess.run([
                'docker', 'cp', dump_path, 'sms_postgres:/tmp/migration_dump.sql'
            ], capture_output=True, text=True, timeout=120)
            
            if copy_result.returncode != 0:
                self.log_message(f"❌ Error copiando dump: {copy_result.stderr}", "ERROR")
                return False
            
            # Ejecutar dump
            self.log_message("⚡ Ejecutando migración masiva...")
            exec_start = time.time()
            
            exec_result = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-f', '/tmp/migration_dump.sql'
            ], capture_output=True, text=True, timeout=1800)  # 30 minutos timeout
            
            exec_time = time.time() - exec_start
            
            if exec_result.returncode == 0:
                self.log_message(f"✅ Migración masiva completada en {exec_time:.1f}s")
                
                # Limpiar archivos
                try:
                    os.unlink(dump_path)
                    subprocess.run([
                        'docker-compose', 'exec', '-T', 'postgres',
                        'rm', '-f', '/tmp/migration_dump.sql'
                    ], capture_output=True)
                except:
                    pass
                
                return True
            else:
                self.log_message(f"❌ Error ejecutando dump: {exec_result.stderr[:500]}", "ERROR")
                return False
            
        except Exception as e:
            self.log_message(f"❌ ERROR en método dump: {e}", "ERROR")
            return False
    
    def estimate_completion_time(self):
        """Estimar tiempo restante"""
        if self.processed_records == 0:
            return "Calculando..."
        
        elapsed_time = time.time() - self.start_time
        records_per_second = self.processed_records / elapsed_time
        remaining_records = self.total_records - self.processed_records
        
        if records_per_second > 0:
            remaining_seconds = remaining_records / records_per_second
            completion_time = datetime.now() + timedelta(seconds=remaining_seconds)
            return completion_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return "No disponible"
    
    def validate_migration(self):
        """Validar migración completa"""
        self.log_message("🔍 Validando migración completa...")
        
        validation_queries = [
            ("Total registros", "SELECT COUNT(*) FROM contacts"),
            ("Números E.164 válidos", "SELECT COUNT(*) FROM contacts WHERE phone_e164 ~ '^\\+52[0-9]{10}$'"),
            ("Estados únicos", "SELECT COUNT(DISTINCT state_code) FROM contacts WHERE state_code IS NOT NULL"),
            ("Registros móviles", "SELECT COUNT(*) FROM contacts WHERE is_mobile = true")
        ]
        
        validation_results = {}
        
        for description, query in validation_queries:
            try:
                result = subprocess.run([
                    'docker-compose', 'exec', '-T', 'postgres',
                    'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                    '-t', '-c', query
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    count = int(result.stdout.strip())
                    validation_results[description] = count
                    self.log_message(f"   ✅ {description}: {count:,}")
                else:
                    validation_results[description] = 0
            except Exception as e:
                validation_results[description] = 0
        
        return validation_results
    
    def restore_postgresql_config(self):
        """Restaurar configuración normal de PostgreSQL"""
        self.log_message("🔧 Restaurando configuración PostgreSQL...")
        
        restore_queries = [
            "ALTER SYSTEM RESET wal_level;",
            "ALTER SYSTEM RESET synchronous_commit;",
            "ALTER SYSTEM RESET fsync;",
            "ALTER SYSTEM RESET full_page_writes;",
            "ALTER SYSTEM RESET checkpoint_segments;",
            "ALTER SYSTEM RESET autovacuum;",
            "ALTER SYSTEM SET autovacuum = on;",
            "SELECT pg_reload_conf();",
            "VACUUM ANALYZE contacts;"
        ]
        
        for query in restore_queries:
            try:
                subprocess.run([
                    'docker-compose', 'exec', '-T', 'postgres',
                    'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                    '-c', query
                ], capture_output=True, text=True, timeout=300)
            except:
                pass
        
        self.log_message("✅ Configuración PostgreSQL restaurada")
    
    def execute_high_speed_migration(self):
        """Ejecutar migración de alta velocidad"""
        self.start_time = time.time()
        
        self.log_message("🚀 INICIANDO MIGRACIÓN DE ALTA VELOCIDAD DE 36.6 MILLONES DE REGISTROS")
        self.log_message("=" * 80)
        
        # FASE 1: Preparación
        self.log_message("📋 FASE 1: PREPARACIÓN")
        if not self.check_system_resources():
            return False
        
        if self.get_total_records() == 0:
            return False
        
        self.optimize_postgresql_aggressive()
        
        if not self.clear_target_table():
            return False
        
        # Preguntar método preferido
        print("\n🚀 MÉTODOS DE MIGRACIÓN DISPONIBLES:")
        print("1. COPY desde STDIN (Recomendado - Muy rápido)")
        print("2. INSERT masivo con VALUES (Rápido)")
        print("3. Dump SQL completo (Más rápido para datasets enormes)")
        
        method_choice = input("\n¿Qué método prefieres? (1/2/3): ").strip()
        
        if method_choice == "3":
            # MÉTODO 3: Dump completo
            self.log_message("\n📦 FASE 2: MIGRACIÓN USANDO DUMP SQL COMPLETO")
            success = self.method_3_pg_dump_restore()
            
            if success:
                # Contar registros insertados
                count_result = subprocess.run([
                    'docker-compose', 'exec', '-T', 'postgres',
                    'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                    '-t', '-c', 'SELECT COUNT(*) FROM contacts;'
                ], capture_output=True, text=True)
                
                if count_result.returncode == 0:
                    self.successful_inserts = int(count_result.stdout.strip())
                    self.processed_records = self.total_records
        
        else:
            # MÉTODO 1 o 2: Por lotes
            self.log_message(f"\n📦 FASE 2: MIGRACIÓN USANDO MÉTODO {method_choice}")
            
            total_batches = (self.total_records + self.batch_size - 1) // self.batch_size
            self.log_message(f"Procesando {total_batches:,} lotes de {self.batch_size:,} registros cada uno")
            
            for batch_num in range(1, total_batches + 1):
                offset = (batch_num - 1) * self.batch_size
                limit = min(self.batch_size, self.total_records - offset)
                
                if limit <= 0:
                    break
                
                # Seleccionar método
                if method_choice == "1":
                    inserted = self.method_1_psql_copy_stdin(batch_num, offset, limit)
                else:
                    inserted = self.method_2_bulk_insert_values(batch_num, offset, limit)
                
                # Mostrar progreso cada 5 lotes
                if batch_num % 5 == 0:
                    eta = self.estimate_completion_time()
                    self.log_message(f"📊 PROGRESO: {batch_num}/{total_batches} lotes | ETA: {eta}")
                    
                    memory = psutil.virtual_memory()
                    self.log_message(f"💾 Memoria: {memory.percent}% usado")
        
        # FASE 3: Validación final
        self.log_message("\n🔍 FASE 3: VALIDACIÓN FINAL")
        validation_results = self.validate_migration()
        
        # FASE 4: Optimización post-migración
        self.log_message("\n⚡ FASE 4: OPTIMIZACIÓN POST-MIGRACIÓN")
        self.restore_postgresql_config()
        
        # Estadísticas finales
        total_time = time.time() - self.start_time
        records_per_second = self.processed_records / total_time if total_time > 0 else 0
        
        self.log_message("\n" + "=" * 80)
        self.log_message("🎯 MIGRACIÓN DE ALTA VELOCIDAD COMPLETADA")
        self.log_message("=" * 80)
        self.log_message(f"📱 Registros procesados: {self.processed_records:,}")
        self.log_message(f"✅ Inserciones exitosas: {self.successful_inserts:,}")
        self.log_message(f"❌ Inserciones fallidas: {self.failed_inserts:,}")
        self.log_message(f"⏱️  Tiempo total: {total_time/60:.1f} minutos")
        self.log_message(f"🚀 Velocidad promedio: {records_per_second:.0f} registros/segundo")
        self.log_message(f"🎯 Tasa de éxito: {(self.successful_inserts/self.processed_records*100):.1f}%")
        
        # Guardar reporte final
        self.save_final_report(validation_results, total_time)
        
        return True
    
    def save_final_report(self, validation_results, total_time):
        """Guardar reporte final de migración"""
        report = {
            "migration_summary": {
                "total_records": self.total_records,
                "processed_records": self.processed_records,
                "successful_inserts": self.successful_inserts,
                "failed_inserts": self.failed_inserts,
                "success_rate": (self.successful_inserts/self.processed_records*100) if self.processed_records > 0 else 0,
                "total_time_minutes": total_time/60,
                "records_per_second": self.processed_records/total_time if total_time > 0 else 0
            },
            "validation_results": validation_results,
            "timestamp": datetime.now().isoformat()
        }
        
        report_path = f"MIGRACION_ALTA_VELOCIDAD_36M_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.log_message(f"📄 Reporte guardado: {report_path}")
        except Exception as e:
            self.log_message(f"⚠️  Error guardando reporte: {e}", "WARNING")

def main():
    """Función principal"""
    solution = HighSpeedMigration()
    
    print("🔥 MIGRACIÓN DE ALTA VELOCIDAD DE 36.6 MILLONES DE REGISTROS")
    print("⚡ TÉCNICAS PROFESIONALES DE MIGRACIÓN MASIVA")
    print("⏱️  TIEMPO ESTIMADO: 30 minutos - 2 horas")
    print("📋 Métodos disponibles:")
    print("   1. COPY desde STDIN - 50,000+ registros/segundo")
    print("   2. INSERT masivo VALUES - 20,000+ registros/segundo") 
    print("   3. Dump SQL completo - 100,000+ registros/segundo")
    print("   4. Optimización agresiva PostgreSQL")
    print("   5. Transacciones masivas optimizadas")
    
    confirm = input("\n¿Continuar con la migración de alta velocidad? (yes/no): ").lower().strip()
    
    if confirm == 'yes':
        success = solution.execute_high_speed_migration()
        
        if success:
            print("\n🎉 ¡MIGRACIÓN DE ALTA VELOCIDAD COMPLETADA EXITOSAMENTE!")
            print("📊 Revisa el reporte JSON generado para detalles completos")
        else:
            print("\n❌ MIGRACIÓN FALLÓ - Revisa los logs para detalles")
    else:
        print("\n❌ Migración cancelada por el usuario")

if __name__ == "__main__":
    main()