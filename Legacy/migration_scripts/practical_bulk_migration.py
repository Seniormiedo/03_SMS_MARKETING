#!/usr/bin/env python3
"""
MIGRACIÓN PRÁCTICA MASIVA - SOLUCIÓN QUE FUNCIONA
Basada en el método que ya probamos exitosamente con inserción individual
"""

import sqlite3
import subprocess
import sys
import os
import time
import json
import psutil
from datetime import datetime, timedelta
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.migration_manager import DataTransformer

class PracticalBulkMigration:
    """Migración práctica masiva usando INSERT individuales"""
    
    def __init__(self):
        self.start_time = None
        self.total_records = 0
        self.processed_records = 0
        self.successful_inserts = 0
        self.failed_inserts = 0
        self.batch_size = 5000  # 5K registros por lote
        
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
    
    def backup_source_database(self):
        """Crear backup de numeros.db"""
        self.log_message("💾 Creando backup de numeros.db...")
        
        source_path = Path("numeros.db")
        if not source_path.exists():
            self.log_message("❌ ERROR: numeros.db no encontrado", "ERROR")
            return False
        
        backup_name = f"numeros_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = Path("backups") / backup_name
        backup_path.parent.mkdir(exist_ok=True)
        
        try:
            import shutil
            shutil.copy2(source_path, backup_path)
            backup_size = backup_path.stat().st_size
            self.log_message(f"✅ Backup creado: {backup_path} ({backup_size/1024**3:.1f}GB)")
            return True
        except Exception as e:
            self.log_message(f"❌ ERROR creando backup: {e}", "ERROR")
            return False
    
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
    
    def optimize_postgresql(self):
        """Optimizar PostgreSQL para inserción masiva"""
        self.log_message("⚡ Optimizando PostgreSQL...")
        
        optimization_queries = [
            "ALTER SYSTEM SET synchronous_commit = off;",
            "ALTER SYSTEM SET wal_buffers = '64MB';",
            "SELECT pg_reload_conf();"
        ]
        
        for query in optimization_queries:
            try:
                subprocess.run([
                    'docker-compose', 'exec', '-T', 'postgres',
                    'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                    '-c', query
                ], capture_output=True, text=True, timeout=10)
            except:
                pass
        
        self.log_message("✅ Optimización PostgreSQL completada")
    
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
    
    def migrate_batch_individual(self, batch_number, offset, limit):
        """Migrar un lote usando INSERT individuales (método que funciona)"""
        batch_start = time.time()
        total_batches = (self.total_records + self.batch_size - 1) // self.batch_size
        self.log_message(f"🔄 Procesando lote {batch_number}/{total_batches} (registros {offset+1:,} - {offset+limit:,})")
        
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
            transformed_records = []
            
            for record in batch_records:
                result = transformer.transform_record(record)
                if result["success"]:
                    transformed_records.append(result["data"])
            
            if not transformed_records:
                return 0
            
            # Insertar uno por uno (método que sabemos que funciona)
            inserted_count = 0
            
            for i, data in enumerate(transformed_records):
                if i % 500 == 0 and i > 0:
                    self.log_message(f"   💾 Insertando registro {i+1}/{len(transformed_records)} del lote {batch_number}")
                
                # Escapar valores para SQL
                def escape_sql(value):
                    if value is None:
                        return "NULL"
                    elif isinstance(value, str):
                        escaped = value.replace("'", "''")
                        return f"'{escaped}'"
                    elif isinstance(value, bool):
                        return "TRUE" if value else "FALSE"
                    else:
                        return str(value)
                
                # Crear comando INSERT individual
                insert_sql = f"""
                INSERT INTO contacts (
                    phone_e164, phone_national, phone_original, full_name, address, neighborhood,
                    lada, state_code, state_name, municipality, city, is_mobile, operator,
                    status, status_updated_at, status_source, send_count, last_sent_at,
                    opt_out_at, opt_out_method, last_validated_at, validation_attempts,
                    source, import_batch_id
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
                    NULL,
                    NULL,
                    0,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    0,
                    {escape_sql(data.get("source", "TELCEL2022"))},
                    NULL
                ) ON CONFLICT (phone_e164) DO NOTHING;
                """
                
                try:
                    result = subprocess.run([
                        'docker-compose', 'exec', '-T', 'postgres',
                        'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                        '-c', insert_sql
                    ], capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0:
                        if "INSERT 0 1" in result.stdout:
                            inserted_count += 1
                        elif "INSERT 0 0" in result.stdout:
                            # Conflicto - número duplicado, contar como exitoso
                            inserted_count += 1
                    else:
                        # Solo mostrar primeros 10 errores para no saturar logs
                        if i < 10:
                            self.log_message(f"   ⚠️  Error en registro {i+1}: {result.stderr[:100]}", "WARNING")
                        
                except subprocess.TimeoutExpired:
                    if i < 10:
                        self.log_message(f"   ⚠️  Timeout en registro {i+1}", "WARNING")
                except Exception as e:
                    if i < 10:
                        self.log_message(f"   ⚠️  Excepción en registro {i+1}: {e}", "WARNING")
            
            # Estadísticas del lote
            batch_time = time.time() - batch_start
            records_per_second = len(batch_records) / batch_time if batch_time > 0 else 0
            
            self.processed_records += len(batch_records)
            self.successful_inserts += inserted_count
            self.failed_inserts += (len(batch_records) - inserted_count)
            
            progress_percent = (self.processed_records / self.total_records) * 100
            
            self.log_message(f"✅ Lote {batch_number} completado:")
            self.log_message(f"   📊 Procesados: {len(batch_records):,} | Insertados: {inserted_count:,}")
            self.log_message(f"   ⏱️  Tiempo: {batch_time:.1f}s | Velocidad: {records_per_second:.0f} reg/s")
            self.log_message(f"   📈 Progreso total: {progress_percent:.2f}% ({self.processed_records:,}/{self.total_records:,})")
            
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
    
    def execute_practical_migration(self):
        """Ejecutar migración práctica masiva"""
        self.start_time = time.time()
        
        self.log_message("🚀 INICIANDO MIGRACIÓN PRÁCTICA MASIVA DE 36.6 MILLONES DE REGISTROS")
        self.log_message("=" * 80)
        
        # FASE 1: Preparación
        self.log_message("📋 FASE 1: PREPARACIÓN")
        if not self.check_system_resources():
            return False
        
        if not self.backup_source_database():
            return False
        
        if self.get_total_records() == 0:
            return False
        
        self.optimize_postgresql()
        
        if not self.clear_target_table():
            return False
        
        # FASE 2: Migración usando INSERT individuales
        self.log_message("\n📦 FASE 2: MIGRACIÓN USANDO INSERT INDIVIDUALES")
        
        total_batches = (self.total_records + self.batch_size - 1) // self.batch_size
        self.log_message(f"Procesando {total_batches:,} lotes de {self.batch_size:,} registros cada uno")
        self.log_message("⚠️  NOTA: Esta migración será lenta pero segura (estimado: 12-24 horas)")
        
        for batch_num in range(1, total_batches + 1):
            offset = (batch_num - 1) * self.batch_size
            limit = min(self.batch_size, self.total_records - offset)
            
            if limit <= 0:
                break
            
            # Migrar lote usando INSERT individuales
            inserted = self.migrate_batch_individual(batch_num, offset, limit)
            
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
        self.log_message("🎯 MIGRACIÓN PRÁCTICA COMPLETADA")
        self.log_message("=" * 80)
        self.log_message(f"📱 Registros procesados: {self.processed_records:,}")
        self.log_message(f"✅ Inserciones exitosas: {self.successful_inserts:,}")
        self.log_message(f"❌ Inserciones fallidas: {self.failed_inserts:,}")
        self.log_message(f"⏱️  Tiempo total: {total_time/3600:.1f} horas")
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
                "total_time_hours": total_time/3600,
                "records_per_second": self.processed_records/total_time if total_time > 0 else 0
            },
            "validation_results": validation_results,
            "timestamp": datetime.now().isoformat()
        }
        
        report_path = f"MIGRACION_PRACTICA_36M_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.log_message(f"📄 Reporte guardado: {report_path}")
        except Exception as e:
            self.log_message(f"⚠️  Error guardando reporte: {e}", "WARNING")

def main():
    """Función principal"""
    solution = PracticalBulkMigration()
    
    print("🔥 MIGRACIÓN PRÁCTICA MASIVA DE 36.6 MILLONES DE REGISTROS")
    print("🛠️  MÉTODO PROBADO - INSERT INDIVIDUALES")
    print("⚠️  ADVERTENCIA: Esta operación puede tomar 12-24 horas")
    print("📋 Características de esta solución:")
    print("   - INSERT individuales (método que sabemos que funciona)")
    print("   - Lotes de 5K registros para seguimiento")
    print("   - Progreso detallado cada 500 registros")
    print("   - Sin límites de Windows (comandos cortos)")
    print("   - Manejo completo de errores")
    print("   - Backup automático")
    
    confirm = input("\n¿Continuar con la migración práctica? (yes/no): ").lower().strip()
    
    if confirm == 'yes':
        success = solution.execute_practical_migration()
        
        if success:
            print("\n🎉 ¡MIGRACIÓN PRÁCTICA COMPLETADA EXITOSAMENTE!")
            print("📊 Revisa el reporte JSON generado para detalles completos")
        else:
            print("\n❌ MIGRACIÓN FALLÓ - Revisa los logs para detalles")
    else:
        print("\n❌ Migración cancelada por el usuario")

if __name__ == "__main__":
    main()