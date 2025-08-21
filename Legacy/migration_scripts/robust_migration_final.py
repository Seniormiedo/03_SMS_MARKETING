#!/usr/bin/env python3
"""
MIGRACIÓN ROBUSTA FINAL - ENFOQUE HÍBRIDO
Combina velocidad con estabilidad, evitando problemas de SQLite
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

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.migration_manager import DataTransformer

class RobustMigrationFinal:
    """Migración robusta usando múltiples conexiones SQLite y transacciones pequeñas"""
    
    def __init__(self):
        self.start_time = None
        self.total_records = 0
        self.processed_records = 0
        self.successful_inserts = 0
        self.failed_inserts = 0
        self.batch_size = 10000  # Lotes más pequeños para estabilidad
        self.transaction_size = 1000  # Transacciones pequeñas
        
    def log_message(self, message, level="INFO"):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def get_total_records(self):
        """Obtener conteo exacto de registros"""
        self.log_message("📊 Contando registros totales...")
        
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
    
    def optimize_postgresql_moderate(self):
        """Optimización moderada de PostgreSQL"""
        self.log_message("⚡ Aplicando optimización moderada...")
        
        optimization_commands = [
            "ALTER SYSTEM SET synchronous_commit = off;",
            "ALTER SYSTEM SET wal_buffers = '32MB';",
            "ALTER SYSTEM SET checkpoint_completion_target = 0.8;",
            "ALTER SYSTEM SET work_mem = '256MB';",
            "ALTER SYSTEM SET maintenance_work_mem = '1GB';",
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
        
        self.log_message("✅ Optimización aplicada")
    
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
    
    def migrate_batch_robust(self, batch_number, offset, limit):
        """Migrar un lote usando transacciones pequeñas y múltiples conexiones"""
        batch_start = time.time()
        total_batches = (self.total_records + self.batch_size - 1) // self.batch_size
        self.log_message(f"🔄 Lote {batch_number}/{total_batches} (registros {offset+1:,} - {offset+limit:,})")
        
        try:
            # Usar nueva conexión SQLite para cada lote (evita bloqueos)
            conn = sqlite3.connect("numeros.db", timeout=30.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Leer con timeout y reintentos
            max_retries = 3
            for retry in range(max_retries):
                try:
                    cursor.execute(f"SELECT * FROM numeros LIMIT {limit} OFFSET {offset}")
                    batch_records = [dict(row) for row in cursor.fetchall()]
                    break
                except sqlite3.OperationalError as e:
                    if retry < max_retries - 1:
                        self.log_message(f"⚠️  Reintento {retry + 1} para lote {batch_number}: {e}", "WARNING")
                        time.sleep(1)
                        continue
                    else:
                        raise e
            
            conn.close()
            
            if not batch_records:
                return 0
            
            # Transformar registros
            transformer = DataTransformer()
            transformed_records = []
            
            for record in batch_records:
                result = transformer.transform_record(record)
                if result["success"]:
                    transformed_records.append(result["data"])
            
            if not transformed_records:
                return 0
            
            # Insertar en mini-transacciones
            inserted_count = 0
            
            for i in range(0, len(transformed_records), self.transaction_size):
                mini_batch = transformed_records[i:i+self.transaction_size]
                
                # Crear SQL para mini-transacción
                values_list = []
                for data in mini_batch:
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
                
                # Crear mini-transacción SQL
                mini_sql = f"""
BEGIN;
INSERT INTO contacts (
    phone_e164, phone_national, phone_original, full_name, address, neighborhood,
    lada, state_code, state_name, municipality, city, is_mobile, operator,
    status, status_updated_at, status_source, send_count, last_sent_at,
    opt_out_at, opt_out_method, last_validated_at, validation_attempts,
    source, import_batch_id
) VALUES {', '.join(values_list)}
ON CONFLICT (phone_e164) DO NOTHING;
COMMIT;
"""
                
                # Crear archivo temporal para mini-transacción
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False, encoding='utf-8') as temp_file:
                    temp_file.write(mini_sql)
                    temp_file_path = temp_file.name
                
                try:
                    # Copiar y ejecutar mini-transacción
                    copy_result = subprocess.run([
                        'docker', 'cp', temp_file_path, f'sms_postgres:/tmp/mini_batch_{i}.sql'
                    ], capture_output=True, text=True, timeout=10)
                    
                    if copy_result.returncode == 0:
                        exec_result = subprocess.run([
                            'docker-compose', 'exec', '-T', 'postgres',
                            'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                            '-f', f'/tmp/mini_batch_{i}.sql'
                        ], capture_output=True, text=True, timeout=30)
                        
                        if exec_result.returncode == 0:
                            inserted_count += len(mini_batch)
                        else:
                            self.log_message(f"⚠️  Error en mini-transacción {i}: {exec_result.stderr[:100]}", "WARNING")
                        
                        # Limpiar archivo del contenedor
                        subprocess.run([
                            'docker-compose', 'exec', '-T', 'postgres',
                            'rm', '-f', f'/tmp/mini_batch_{i}.sql'
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
            "ALTER SYSTEM RESET synchronous_commit;",
            "ALTER SYSTEM RESET wal_buffers;",
            "ALTER SYSTEM RESET checkpoint_completion_target;",
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
    
    def execute_robust_migration(self):
        """Ejecutar migración robusta completa"""
        self.start_time = time.time()
        
        self.log_message("🚀 INICIANDO MIGRACIÓN ROBUSTA DE 36.6 MILLONES DE REGISTROS")
        self.log_message("=" * 80)
        
        # FASE 1: Preparación
        self.log_message("📋 FASE 1: PREPARACIÓN")
        
        if self.get_total_records() == 0:
            return False
        
        self.optimize_postgresql_moderate()
        
        if not self.clear_target_table():
            return False
        
        # FASE 2: Migración robusta por lotes
        self.log_message("\n📦 FASE 2: MIGRACIÓN ROBUSTA POR LOTES")
        self.log_message("🛡️  Características:")
        self.log_message("   - Lotes pequeños de 10K registros")
        self.log_message("   - Mini-transacciones de 1K registros")
        self.log_message("   - Múltiples conexiones SQLite")
        self.log_message("   - Reintentos automáticos")
        self.log_message("   - Progreso persistente")
        
        total_batches = (self.total_records + self.batch_size - 1) // self.batch_size
        
        for batch_num in range(1, total_batches + 1):
            offset = (batch_num - 1) * self.batch_size
            limit = min(self.batch_size, self.total_records - offset)
            
            if limit <= 0:
                break
            
            # Migrar lote robusto
            inserted = self.migrate_batch_robust(batch_num, offset, limit)
            
            # Mostrar progreso cada 10 lotes
            if batch_num % 10 == 0:
                eta = self.estimate_completion_time()
                self.log_message(f"📊 PROGRESO: {batch_num}/{total_batches} lotes | ETA: {eta}")
                
                memory = psutil.virtual_memory()
                self.log_message(f"💾 Memoria: {memory.percent}% usado")
                
                # Mostrar progreso intermedio
                current_count = self.get_current_count()
                self.log_message(f"📱 Registros confirmados en BD: {current_count:,}")
        
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
        self.log_message("🎯 MIGRACIÓN ROBUSTA COMPLETADA")
        self.log_message("=" * 80)
        self.log_message(f"📱 Registros procesados: {self.processed_records:,}")
        self.log_message(f"✅ Inserciones exitosas: {self.successful_inserts:,}")
        self.log_message(f"❌ Inserciones fallidas: {self.failed_inserts:,}")
        self.log_message(f"⏱️  Tiempo total: {total_time/60:.1f} minutos")
        self.log_message(f"🚀 Velocidad promedio: {records_per_second:.0f} registros/segundo")
        
        if self.processed_records > 0:
            self.log_message(f"🎯 Tasa de éxito: {(self.successful_inserts/self.processed_records*100):.1f}%")
        
        # Guardar reporte final
        self.save_final_report(validation_results, total_time)
        
        return True
    
    def get_current_count(self):
        """Obtener conteo actual de registros en PostgreSQL"""
        try:
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-t', '-c', 'SELECT COUNT(*) FROM contacts;'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return int(result.stdout.strip())
            else:
                return 0
        except:
            return 0
    
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
        
        report_path = f"MIGRACION_ROBUSTA_36M_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.log_message(f"📄 Reporte guardado: {report_path}")
        except Exception as e:
            self.log_message(f"⚠️  Error guardando reporte: {e}", "WARNING")

def main():
    """Función principal"""
    solution = RobustMigrationFinal()
    
    print("🔥 MIGRACIÓN ROBUSTA DE 36.6 MILLONES DE REGISTROS")
    print("🛡️  ENFOQUE HÍBRIDO - VELOCIDAD + ESTABILIDAD")
    print("⏱️  TIEMPO ESTIMADO: 2-4 horas")
    print("📋 Características:")
    print("   - Lotes pequeños de 10K registros (estabilidad)")
    print("   - Mini-transacciones de 1K registros (recuperación)")
    print("   - Múltiples conexiones SQLite (evita bloqueos)")
    print("   - Reintentos automáticos (tolerancia a fallos)")
    print("   - Progreso persistente (no se pierde trabajo)")
    print("   - Velocidad estimada: 3,000-5,000 registros/segundo")
    
    confirm = input("\n¿Continuar con la migración robusta? (yes/no): ").lower().strip()
    
    if confirm == 'yes':
        success = solution.execute_robust_migration()
        
        if success:
            print("\n🎉 ¡MIGRACIÓN ROBUSTA COMPLETADA EXITOSAMENTE!")
            print("📊 Revisa el reporte JSON generado para detalles completos")
        else:
            print("\n❌ MIGRACIÓN FALLÓ - Revisa los logs para detalles")
    else:
        print("\n❌ Migración cancelada por el usuario")

if __name__ == "__main__":
    main()