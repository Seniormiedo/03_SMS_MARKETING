#!/usr/bin/env python3
"""
SOLUCIÓN DEFINITIVA DE MIGRACIÓN
Usa conexión directa a PostgreSQL con asyncpg para evitar límites de Windows completamente
"""

import asyncio
import sqlite3
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

class UltimateMigrationSolution:
    """Solución definitiva usando conexión directa asyncpg"""
    
    def __init__(self):
        self.start_time = None
        self.total_records = 0
        self.processed_records = 0
        self.successful_inserts = 0
        self.failed_inserts = 0
        self.batch_size = 10000  # 10K registros por lote
        self.insert_batch_size = 100  # 100 registros por transacción
        
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
    
    async def get_postgres_connection(self):
        """Obtener conexión directa a PostgreSQL usando asyncpg"""
        try:
            import asyncpg
            
            # Configuración de conexión
            connection = await asyncpg.connect(
                host='localhost',
                port=15432,  # Puerto mapeado de Docker
                user='sms_user',
                password='sms_password',
                database='sms_marketing'
            )
            
            self.log_message("✅ Conexión directa a PostgreSQL establecida")
            return connection
            
        except ImportError:
            self.log_message("❌ ERROR: asyncpg no está instalado. Instalando...", "ERROR")
            import subprocess
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'asyncpg'], check=True)
            
            import asyncpg
            connection = await asyncpg.connect(
                host='localhost',
                port=15432,
                user='sms_user',
                password='sms_password',
                database='sms_marketing'
            )
            
            self.log_message("✅ Conexión directa a PostgreSQL establecida (asyncpg instalado)")
            return connection
            
        except Exception as e:
            self.log_message(f"❌ ERROR conectando a PostgreSQL: {e}", "ERROR")
            return None
    
    async def clear_target_table(self, connection):
        """Limpiar tabla de destino"""
        self.log_message("🧹 Limpiando tabla contacts...")
        
        try:
            await connection.execute("TRUNCATE TABLE messages, contacts RESTART IDENTITY CASCADE;")
            self.log_message("✅ Tabla contacts limpiada")
            return True
        except Exception as e:
            self.log_message(f"❌ Error limpiando tabla: {e}", "ERROR")
            return False
    
    async def optimize_postgresql(self, connection):
        """Optimizar PostgreSQL para inserción masiva"""
        self.log_message("⚡ Optimizando PostgreSQL...")
        
        optimization_queries = [
            "SET synchronous_commit = off;",
            "SET wal_buffers = '64MB';",
            "SET checkpoint_completion_target = 0.9;",
            "SET maintenance_work_mem = '1GB';",
            "SET work_mem = '256MB';"
        ]
        
        for query in optimization_queries:
            try:
                await connection.execute(query)
            except Exception as e:
                self.log_message(f"⚠️  Error en optimización: {e}", "WARNING")
        
        self.log_message("✅ Optimización PostgreSQL completada")
    
    async def migrate_batch_direct(self, connection, batch_number, offset, limit):
        """Migrar un lote usando conexión directa asyncpg"""
        batch_start = time.time()
        total_batches = (self.total_records + self.batch_size - 1) // self.batch_size
        self.log_message(f"🔄 Procesando lote {batch_number}/{total_batches} (registros {offset+1:,} - {offset+limit:,})")
        
        try:
            # Obtener datos de SQLite
            sqlite_conn = sqlite3.connect("numeros.db")
            sqlite_conn.row_factory = sqlite3.Row
            cursor = sqlite_conn.cursor()
            
            cursor.execute(f"SELECT * FROM numeros LIMIT {limit} OFFSET {offset}")
            batch_records = [dict(row) for row in cursor.fetchall()]
            sqlite_conn.close()
            
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
            
            # Insertar usando transacciones por lotes
            inserted_count = 0
            
            # Preparar consulta INSERT
            insert_query = """
            INSERT INTO contacts (
                phone_e164, phone_national, phone_original, full_name, address, neighborhood,
                lada, state_code, state_name, municipality, city, is_mobile, operator,
                status, status_updated_at, status_source, send_count, last_sent_at,
                opt_out_at, opt_out_method, last_validated_at, validation_attempts,
                source, import_batch_id
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24)
            ON CONFLICT (phone_e164) DO NOTHING
            """
            
            # Insertar en sub-lotes usando transacciones
            for i in range(0, len(transformed_records), self.insert_batch_size):
                sub_batch = transformed_records[i:i+self.insert_batch_size]
                
                try:
                    async with connection.transaction():
                        for data in sub_batch:
                            await connection.execute(
                                insert_query,
                                data.get("phone_e164"),
                                data.get("phone_national"),
                                data.get("phone_original"),
                                data.get("full_name"),
                                data.get("address"),
                                data.get("neighborhood"),
                                data.get("lada"),
                                data.get("state_code"),
                                data.get("state_name"),
                                data.get("municipality"),
                                data.get("city"),
                                data.get("is_mobile"),
                                data.get("operator"),
                                data.get("status", "UNKNOWN"),
                                None,  # status_updated_at
                                None,  # status_source
                                0,     # send_count
                                None,  # last_sent_at
                                None,  # opt_out_at
                                None,  # opt_out_method
                                None,  # last_validated_at
                                0,     # validation_attempts
                                data.get("source", "TELCEL2022"),
                                None   # import_batch_id
                            )
                        
                        inserted_count += len(sub_batch)
                        
                except Exception as e:
                    self.log_message(f"⚠️  Error en sub-lote: {e}", "WARNING")
            
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
    
    async def validate_migration(self, connection):
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
                result = await connection.fetchval(query)
                validation_results[description] = result
                self.log_message(f"   ✅ {description}: {result:,}")
            except Exception as e:
                self.log_message(f"   ❌ Excepción en {description}: {e}", "ERROR")
                validation_results[description] = 0
        
        return validation_results
    
    async def restore_postgresql_config(self, connection):
        """Restaurar configuración normal de PostgreSQL"""
        self.log_message("🔧 Restaurando configuración PostgreSQL...")
        
        restore_queries = [
            "RESET synchronous_commit;",
            "RESET wal_buffers;",
            "RESET checkpoint_completion_target;",
            "RESET maintenance_work_mem;",
            "RESET work_mem;",
            "VACUUM ANALYZE contacts;"
        ]
        
        for query in restore_queries:
            try:
                await connection.execute(query)
            except Exception as e:
                self.log_message(f"⚠️  Error en restauración: {e}", "WARNING")
        
        self.log_message("✅ Configuración PostgreSQL restaurada")
    
    async def execute_ultimate_migration(self):
        """Ejecutar migración completa usando conexión directa"""
        self.start_time = time.time()
        
        self.log_message("🚀 INICIANDO MIGRACIÓN DEFINITIVA DE 36.6 MILLONES DE REGISTROS")
        self.log_message("=" * 80)
        
        # FASE 1: Preparación
        self.log_message("📋 FASE 1: PREPARACIÓN")
        if not self.check_system_resources():
            return False
        
        if not self.backup_source_database():
            return False
        
        if self.get_total_records() == 0:
            return False
        
        # Obtener conexión directa
        connection = await self.get_postgres_connection()
        if not connection:
            return False
        
        try:
            await self.optimize_postgresql(connection)
            
            if not await self.clear_target_table(connection):
                return False
            
            # FASE 2: Migración usando conexión directa
            self.log_message("\n📦 FASE 2: MIGRACIÓN USANDO CONEXIÓN DIRECTA ASYNCPG")
            
            total_batches = (self.total_records + self.batch_size - 1) // self.batch_size
            self.log_message(f"Procesando {total_batches:,} lotes de {self.batch_size:,} registros cada uno")
            
            for batch_num in range(1, total_batches + 1):
                offset = (batch_num - 1) * self.batch_size
                limit = min(self.batch_size, self.total_records - offset)
                
                if limit <= 0:
                    break
                
                # Migrar lote usando conexión directa
                inserted = await self.migrate_batch_direct(connection, batch_num, offset, limit)
                
                # Mostrar progreso cada 10 lotes
                if batch_num % 10 == 0:
                    eta = self.estimate_completion_time()
                    self.log_message(f"📊 PROGRESO: {batch_num}/{total_batches} lotes | ETA: {eta}")
                    
                    memory = psutil.virtual_memory()
                    self.log_message(f"💾 Memoria: {memory.percent}% usado")
            
            # FASE 3: Validación final
            self.log_message("\n🔍 FASE 3: VALIDACIÓN FINAL")
            validation_results = await self.validate_migration(connection)
            
            # FASE 4: Optimización post-migración
            self.log_message("\n⚡ FASE 4: OPTIMIZACIÓN POST-MIGRACIÓN")
            await self.restore_postgresql_config(connection)
            
        finally:
            # Cerrar conexión
            await connection.close()
            self.log_message("🔌 Conexión PostgreSQL cerrada")
        
        # Estadísticas finales
        total_time = time.time() - self.start_time
        records_per_second = self.processed_records / total_time if total_time > 0 else 0
        
        self.log_message("\n" + "=" * 80)
        self.log_message("🎯 MIGRACIÓN DEFINITIVA COMPLETADA")
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
        
        report_path = f"MIGRACION_DEFINITIVA_36M_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.log_message(f"📄 Reporte guardado: {report_path}")
        except Exception as e:
            self.log_message(f"⚠️  Error guardando reporte: {e}", "WARNING")

async def main():
    """Función principal"""
    solution = UltimateMigrationSolution()
    
    print("🔥 MIGRACIÓN DEFINITIVA DE 36.6 MILLONES DE REGISTROS")
    print("🚀 CONEXIÓN DIRECTA ASYNCPG - SIN LÍMITES DE WINDOWS")
    print("⚠️  ADVERTENCIA: Esta operación puede tomar 4-8 horas")
    print("📋 Características de esta solución:")
    print("   - Conexión directa a PostgreSQL con asyncpg")
    print("   - Sin límites de línea de comandos de Windows")
    print("   - Transacciones por lotes de 100 registros")
    print("   - Lotes principales de 10K registros")
    print("   - Rendimiento optimizado")
    
    confirm = input("\n¿Continuar con la migración definitiva? (yes/no): ").lower().strip()
    
    if confirm == 'yes':
        success = await solution.execute_ultimate_migration()
        
        if success:
            print("\n🎉 ¡MIGRACIÓN DEFINITIVA COMPLETADA EXITOSAMENTE!")
            print("📊 Revisa el reporte JSON generado para detalles completos")
        else:
            print("\n❌ MIGRACIÓN FALLÓ - Revisa los logs para detalles")
    else:
        print("\n❌ Migración cancelada por el usuario")

if __name__ == "__main__":
    asyncio.run(main())