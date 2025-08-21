#!/usr/bin/env python3
"""
MIGRACIÓN REAL DE 36.6 MILLONES DE REGISTROS
Sistema completo de migración masiva con monitoreo en tiempo real
"""

import asyncio
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

from scripts.migration_manager import DataTransformer, MigrationManager

class RealMigrationOrchestrator:
    """Orquestador de migración real de 36.6M registros"""
    
    def __init__(self):
        self.start_time = None
        self.total_records = 0
        self.processed_records = 0
        self.successful_inserts = 0
        self.failed_inserts = 0
        self.current_batch = 0
        self.total_batches = 0
        self.batch_size = 100000  # 100K registros por lote
        
        # Estadísticas de rendimiento
        self.stats = {
            "start_time": None,
            "phases": {},
            "performance": {},
            "errors": [],
            "system_resources": []
        }
        
    def log_message(self, message, level="INFO"):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def check_system_resources(self):
        """Verificar recursos del sistema"""
        self.log_message("🔍 Verificando recursos del sistema...")
        
        # Memoria
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        memory_available_gb = memory.available / (1024**3)
        
        # Disco
        disk = psutil.disk_usage('.')
        disk_free_gb = disk.free / (1024**3)
        
        # CPU
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        self.log_message(f"💾 Memoria: {memory_available_gb:.1f}GB disponible de {memory_gb:.1f}GB total")
        self.log_message(f"💽 Disco: {disk_free_gb:.1f}GB libres")
        self.log_message(f"🖥️  CPU: {cpu_count} cores, {cpu_percent}% uso actual")
        
        # Verificar requisitos mínimos
        if memory_available_gb < 8:
            self.log_message("⚠️  ADVERTENCIA: Menos de 8GB de RAM disponible", "WARNING")
        
        if disk_free_gb < 40:
            self.log_message("❌ ERROR: Menos de 40GB de espacio libre requerido", "ERROR")
            return False
            
        return True
    
    def backup_source_database(self):
        """Crear backup de numeros.db"""
        self.log_message("💾 Creando backup de numeros.db...")
        
        source_path = Path("numeros.db")
        if not source_path.exists():
            self.log_message("❌ ERROR: numeros.db no encontrado", "ERROR")
            return False
        
        backup_name = f"numeros_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = Path("backups") / backup_name
        
        # Crear directorio de backups
        backup_path.parent.mkdir(exist_ok=True)
        
        try:
            import shutil
            shutil.copy2(source_path, backup_path)
            
            # Verificar integridad del backup
            backup_size = backup_path.stat().st_size
            original_size = source_path.stat().st_size
            
            if backup_size == original_size:
                self.log_message(f"✅ Backup creado: {backup_path} ({backup_size/1024**3:.1f}GB)")
                return True
            else:
                self.log_message("❌ ERROR: Backup corrupto", "ERROR")
                return False
                
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
            self.total_batches = (count + self.batch_size - 1) // self.batch_size
            
            self.log_message(f"📱 Total de registros: {count:,}")
            self.log_message(f"📦 Total de lotes: {self.total_batches:,} (tamaño: {self.batch_size:,})")
            
            return count
            
        except Exception as e:
            self.log_message(f"❌ ERROR contando registros: {e}", "ERROR")
            return 0
    
    def optimize_postgresql(self):
        """Optimizar PostgreSQL para inserción masiva"""
        self.log_message("⚡ Optimizando PostgreSQL para inserción masiva...")
        
        optimization_queries = [
            "ALTER SYSTEM SET synchronous_commit = off;",
            "ALTER SYSTEM SET wal_buffers = '64MB';",
            "ALTER SYSTEM SET checkpoint_completion_target = 0.9;",
            "ALTER SYSTEM SET wal_writer_delay = '1s';",
            "ALTER SYSTEM SET commit_delay = 10000;",
            "ALTER SYSTEM SET commit_siblings = 5;",
            "SELECT pg_reload_conf();",
            "SET maintenance_work_mem = '1GB';",
            "SET work_mem = '256MB';"
        ]
        
        for query in optimization_queries:
            try:
                result = subprocess.run([
                    'docker-compose', 'exec', '-T', 'postgres',
                    'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                    '-c', query
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    self.log_message(f"⚠️  Advertencia en optimización: {query[:50]}...", "WARNING")
                    
            except Exception as e:
                self.log_message(f"⚠️  Error en optimización: {e}", "WARNING")
        
        self.log_message("✅ Optimización PostgreSQL completada")
    
    def clear_target_table(self):
        """Limpiar tabla de destino"""
        self.log_message("🧹 Limpiando tabla contacts...")
        
        try:
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', 'TRUNCATE TABLE messages, contacts RESTART IDENTITY CASCADE;'
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
    
    def migrate_batch(self, batch_number, offset, limit):
        """Migrar un lote específico"""
        batch_start = time.time()
        self.log_message(f"🔄 Procesando lote {batch_number}/{self.total_batches} (registros {offset+1:,} - {offset+limit:,})")
        
        try:
            # Obtener datos de SQLite
            conn = sqlite3.connect("numeros.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT * FROM numeros LIMIT {limit} OFFSET {offset}")
            batch_records = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            if not batch_records:
                self.log_message(f"⚠️  Lote {batch_number} vacío", "WARNING")
                return 0
            
            # Transformar registros
            transformer = DataTransformer()
            sql_values = []
            batch_successful = 0
            batch_failed = 0
            
            for record in batch_records:
                result = transformer.transform_record(record)
                
                if result["success"]:
                    data = result["data"]
                    
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
                    
                    # Crear línea de VALUES
                    values_line = f"""(
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
                    )"""
                    
                    sql_values.append(values_line)
                    batch_successful += 1
                else:
                    batch_failed += 1
            
            # Insertar en sub-lotes para evitar timeouts
            sub_batch_size = 5000  # 5K registros por sub-lote
            inserted_count = 0
            
            for i in range(0, len(sql_values), sub_batch_size):
                sub_batch = sql_values[i:i+sub_batch_size]
                
                sql_command = f"""
                INSERT INTO contacts (
                    phone_e164, phone_national, phone_original, full_name, address, neighborhood,
                    lada, state_code, state_name, municipality, city, is_mobile, operator,
                    status, source, created_at, updated_at
                ) VALUES {', '.join(sub_batch)}
                ON CONFLICT (phone_e164) DO NOTHING;
                """
                
                try:
                    result = subprocess.run([
                        'docker-compose', 'exec', '-T', 'postgres',
                        'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                        '-c', sql_command
                    ], capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        inserted_count += len(sub_batch)
                    else:
                        self.log_message(f"⚠️  Error en sub-lote {i//sub_batch_size + 1}: {result.stderr[:100]}", "WARNING")
                        
                except subprocess.TimeoutExpired:
                    self.log_message(f"⚠️  Timeout en sub-lote {i//sub_batch_size + 1}", "WARNING")
                except Exception as e:
                    self.log_message(f"⚠️  Excepción en sub-lote {i//sub_batch_size + 1}: {e}", "WARNING")
            
            # Estadísticas del lote
            batch_time = time.time() - batch_start
            records_per_second = len(batch_records) / batch_time if batch_time > 0 else 0
            
            self.processed_records += len(batch_records)
            self.successful_inserts += inserted_count
            self.failed_inserts += (len(batch_records) - inserted_count)
            
            # Progreso
            progress_percent = (self.processed_records / self.total_records) * 100
            
            self.log_message(f"✅ Lote {batch_number} completado:")
            self.log_message(f"   📊 Procesados: {len(batch_records):,} | Insertados: {inserted_count:,}")
            self.log_message(f"   ⏱️  Tiempo: {batch_time:.1f}s | Velocidad: {records_per_second:.0f} reg/s")
            self.log_message(f"   📈 Progreso total: {progress_percent:.1f}% ({self.processed_records:,}/{self.total_records:,})")
            
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
            ("Registros móviles", "SELECT COUNT(*) FROM contacts WHERE is_mobile = true"),
            ("Registros con nombres", "SELECT COUNT(*) FROM contacts WHERE full_name IS NOT NULL AND full_name != ''")
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
                    self.log_message(f"   ❌ Error en {description}", "ERROR")
                    validation_results[description] = 0
                    
            except Exception as e:
                self.log_message(f"   ❌ Excepción en {description}: {e}", "ERROR")
                validation_results[description] = 0
        
        return validation_results
    
    def restore_postgresql_config(self):
        """Restaurar configuración normal de PostgreSQL"""
        self.log_message("🔧 Restaurando configuración PostgreSQL...")
        
        restore_queries = [
            "ALTER SYSTEM RESET synchronous_commit;",
            "ALTER SYSTEM RESET wal_buffers;",
            "ALTER SYSTEM RESET checkpoint_completion_target;",
            "ALTER SYSTEM RESET wal_writer_delay;",
            "ALTER SYSTEM RESET commit_delay;",
            "ALTER SYSTEM RESET commit_siblings;",
            "SELECT pg_reload_conf();",
            "VACUUM ANALYZE contacts;",
            "REINDEX TABLE contacts;"
        ]
        
        for query in restore_queries:
            try:
                subprocess.run([
                    'docker-compose', 'exec', '-T', 'postgres',
                    'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                    '-c', query
                ], capture_output=True, text=True, timeout=300)  # 5 min timeout para VACUUM/REINDEX
                
            except Exception as e:
                self.log_message(f"⚠️  Error en restauración: {e}", "WARNING")
        
        self.log_message("✅ Configuración PostgreSQL restaurada")
    
    async def execute_real_migration(self):
        """Ejecutar migración completa de 36.6M registros"""
        self.start_time = time.time()
        self.stats["start_time"] = datetime.now().isoformat()
        
        self.log_message("🚀 INICIANDO MIGRACIÓN REAL DE 36.6 MILLONES DE REGISTROS")
        self.log_message("=" * 80)
        
        # FASE 1: Preparación
        self.log_message("📋 FASE 1: PREPARACIÓN PRE-MIGRACIÓN")
        if not self.check_system_resources():
            return False
        
        if not self.backup_source_database():
            return False
        
        if self.get_total_records() == 0:
            return False
        
        self.optimize_postgresql()
        
        if not self.clear_target_table():
            return False
        
        # FASE 2: Migración por lotes
        self.log_message("\n📦 FASE 2: MIGRACIÓN POR LOTES")
        self.log_message(f"Procesando {self.total_batches:,} lotes de {self.batch_size:,} registros cada uno")
        
        for batch_num in range(1, self.total_batches + 1):
            offset = (batch_num - 1) * self.batch_size
            limit = min(self.batch_size, self.total_records - offset)
            
            if limit <= 0:
                break
            
            # Migrar lote
            inserted = self.migrate_batch(batch_num, offset, limit)
            
            # Mostrar progreso cada 10 lotes
            if batch_num % 10 == 0:
                eta = self.estimate_completion_time()
                self.log_message(f"📊 PROGRESO: {batch_num}/{self.total_batches} lotes | ETA: {eta}")
                
                # Mostrar recursos del sistema
                memory = psutil.virtual_memory()
                self.log_message(f"💾 Memoria: {memory.percent}% usado | Disponible: {memory.available/(1024**3):.1f}GB")
        
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
        self.log_message("🎯 MIGRACIÓN REAL COMPLETADA")
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
        
        report_path = f"MIGRACION_REAL_36M_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.log_message(f"📄 Reporte guardado: {report_path}")
            
        except Exception as e:
            self.log_message(f"⚠️  Error guardando reporte: {e}", "WARNING")

async def main():
    """Función principal"""
    orchestrator = RealMigrationOrchestrator()
    
    print("🔥 MIGRACIÓN REAL DE 36.6 MILLONES DE REGISTROS")
    print("⚠️  ADVERTENCIA: Esta operación puede tomar 8-12 horas")
    print("📋 Asegúrate de tener:")
    print("   - Al menos 40GB de espacio libre")
    print("   - Al menos 8GB de RAM disponible") 
    print("   - Conexión estable a internet")
    print("   - PostgreSQL y Redis ejecutándose")
    
    confirm = input("\n¿Continuar con la migración real? (yes/no): ").lower().strip()
    
    if confirm == 'yes':
        success = await orchestrator.execute_real_migration()
        
        if success:
            print("\n🎉 ¡MIGRACIÓN REAL COMPLETADA EXITOSAMENTE!")
            print("📊 Revisa el reporte JSON generado para detalles completos")
        else:
            print("\n❌ MIGRACIÓN FALLÓ - Revisa los logs para detalles")
    else:
        print("\n❌ Migración cancelada por el usuario")

if __name__ == "__main__":
    asyncio.run(main())