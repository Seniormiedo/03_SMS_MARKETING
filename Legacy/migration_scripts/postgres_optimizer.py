#!/usr/bin/env python3
"""
Optimizador de PostgreSQL para carga masiva
SMS Marketing Platform - DÍA 4
"""

import asyncio
import logging
from typing import Dict, List, Any

import asyncpg

logger = logging.getLogger(__name__)

class PostgreSQLOptimizer:
    """Optimizador de PostgreSQL para migración masiva"""
    
    def __init__(self, postgres_url: str = "postgresql://sms_user:sms_password@localhost:15432/sms_marketing"):
        self.postgres_url = postgres_url
        
    async def optimize_for_bulk_load(self) -> bool:
        """Optimizar PostgreSQL para carga masiva"""
        
        logger.info("⚙️  Optimizando PostgreSQL para carga masiva...")
        
        conn = await asyncpg.connect(self.postgres_url)
        
        try:
            # Configuraciones para carga masiva
            optimizations = [
                # Deshabilitar autocommit para mejor performance
                "SET autocommit = off",
                
                # Aumentar work_mem para operaciones de ordenamiento
                "SET work_mem = '256MB'",
                
                # Aumentar maintenance_work_mem para operaciones de mantenimiento
                "SET maintenance_work_mem = '1GB'",
                
                # Deshabilitar synchronous_commit para mejor performance (menos durabilidad)
                "SET synchronous_commit = off",
                
                # Aumentar checkpoint_segments para reducir checkpoints
                "SET max_wal_size = '2GB'",
                
                # Reducir random_page_cost para SSD
                "SET random_page_cost = 1.1",
                
                # Aumentar effective_cache_size
                "SET effective_cache_size = '4GB'",
                
                # Configurar parallel workers
                "SET max_parallel_workers_per_gather = 4",
                "SET max_parallel_workers = 8",
                
                # Configurar autovacuum para ser menos agresivo durante carga
                "SET autovacuum = off"
            ]
            
            for sql in optimizations:
                try:
                    await conn.execute(sql)
                    logger.info(f"✅ {sql}")
                except Exception as e:
                    logger.warning(f"⚠️  No se pudo aplicar: {sql} - {e}")
            
            # Verificar configuraciones actuales
            await self._show_current_settings(conn)
            
            logger.info("✅ Optimización completada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error optimizando PostgreSQL: {e}")
            return False
            
        finally:
            await conn.close()
    
    async def restore_normal_settings(self) -> bool:
        """Restaurar configuraciones normales post-migración"""
        
        logger.info("🔄 Restaurando configuraciones normales...")
        
        conn = await asyncpg.connect(self.postgres_url)
        
        try:
            # Restaurar configuraciones normales
            restorations = [
                "SET synchronous_commit = on",
                "SET autovacuum = on",
                "SET work_mem = '4MB'",
                "SET maintenance_work_mem = '64MB'"
            ]
            
            for sql in restorations:
                try:
                    await conn.execute(sql)
                    logger.info(f"✅ {sql}")
                except Exception as e:
                    logger.warning(f"⚠️  No se pudo restaurar: {sql} - {e}")
            
            # Ejecutar VACUUM y ANALYZE después de carga masiva
            logger.info("🧹 Ejecutando VACUUM ANALYZE...")
            await conn.execute("VACUUM ANALYZE contacts")
            
            # Actualizar estadísticas
            logger.info("📊 Actualizando estadísticas...")
            await conn.execute("ANALYZE contacts")
            
            logger.info("✅ Restauración completada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error restaurando configuraciones: {e}")
            return False
            
        finally:
            await conn.close()
    
    async def _show_current_settings(self, conn: asyncpg.Connection):
        """Mostrar configuraciones actuales"""
        
        settings = [
            "work_mem",
            "maintenance_work_mem", 
            "synchronous_commit",
            "max_wal_size",
            "effective_cache_size",
            "autovacuum"
        ]
        
        logger.info("📊 Configuraciones actuales:")
        
        for setting in settings:
            try:
                result = await conn.fetchrow(f"SHOW {setting}")
                if result:
                    logger.info(f"   {setting}: {result[0]}")
            except:
                pass
    
    async def create_performance_indexes(self) -> bool:
        """Crear índices adicionales para performance"""
        
        logger.info("🔍 Creando índices de performance...")
        
        conn = await asyncpg.connect(self.postgres_url)
        
        try:
            # Índices adicionales para consultas frecuentes
            additional_indexes = [
                # Índice compuesto para búsquedas por estado y status
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_state_status_mobile ON contacts(state_code, status, is_mobile) WHERE opt_out_at IS NULL",
                
                # Índice para búsquedas de texto en nombres
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_name_gin ON contacts USING gin(to_tsvector('spanish', full_name)) WHERE full_name IS NOT NULL",
                
                # Índice para rangos de fechas
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_created_range ON contacts(created_at) WHERE created_at >= '2025-01-01'",
                
                # Índice para operadores
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_operator_mobile ON contacts(operator, is_mobile) WHERE operator IS NOT NULL",
                
                # Índice para conteo rápido por LADA
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_lada_status ON contacts(lada, status) WHERE lada IS NOT NULL"
            ]
            
            for sql in additional_indexes:
                try:
                    logger.info(f"🔨 Creando índice...")
                    await conn.execute(sql)
                    logger.info(f"✅ Índice creado")
                except Exception as e:
                    logger.warning(f"⚠️  Error creando índice: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando índices: {e}")
            return False
            
        finally:
            await conn.close()
    
    async def analyze_table_statistics(self) -> Dict[str, Any]:
        """Analizar estadísticas de tabla después de migración"""
        
        logger.info("📊 Analizando estadísticas de tabla...")
        
        conn = await asyncpg.connect(self.postgres_url)
        
        try:
            # Estadísticas básicas
            stats_result = await conn.fetchrow("""
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats 
                WHERE tablename = 'contacts' 
                AND attname IN ('phone_e164', 'state_code', 'lada', 'status')
                ORDER BY attname
            """)
            
            # Tamaño de tabla
            size_result = await conn.fetchrow("""
                SELECT 
                    pg_size_pretty(pg_total_relation_size('contacts')) as total_size,
                    pg_size_pretty(pg_relation_size('contacts')) as table_size,
                    pg_size_pretty(pg_indexes_size('contacts')) as indexes_size
            """)
            
            # Información de índices
            indexes_result = await conn.fetch("""
                SELECT 
                    indexname,
                    indexdef,
                    pg_size_pretty(pg_relation_size(indexname::regclass)) as size
                FROM pg_indexes 
                WHERE tablename = 'contacts'
                ORDER BY pg_relation_size(indexname::regclass) DESC
            """)
            
            statistics = {
                "table_size": size_result['table_size'] if size_result else "Unknown",
                "total_size": size_result['total_size'] if size_result else "Unknown", 
                "indexes_size": size_result['indexes_size'] if size_result else "Unknown",
                "indexes": [
                    {
                        "name": row['indexname'],
                        "size": row['size'],
                        "definition": row['indexdef'][:100] + "..." if len(row['indexdef']) > 100 else row['indexdef']
                    } 
                    for row in indexes_result
                ]
            }
            
            logger.info(f"📊 Tamaño total: {statistics['total_size']}")
            logger.info(f"📊 Tamaño tabla: {statistics['table_size']}")
            logger.info(f"📊 Tamaño índices: {statistics['indexes_size']}")
            logger.info(f"📊 Número de índices: {len(statistics['indexes'])}")
            
            return statistics
            
        except Exception as e:
            logger.error(f"❌ Error analizando estadísticas: {e}")
            return {}
            
        finally:
            await conn.close()

async def main():
    """Función principal de optimización"""
    print("⚙️  Optimizador PostgreSQL - SMS Marketing Platform")
    print("="*60)
    
    optimizer = PostgreSQLOptimizer()
    
    # Optimizar para carga masiva
    if await optimizer.optimize_for_bulk_load():
        print("✅ PostgreSQL optimizado para carga masiva")
    else:
        print("❌ Error optimizando PostgreSQL")
        return
    
    # Simular migración (en uso real, aquí iría la migración)
    print("\n⏳ Simulando migración...")
    await asyncio.sleep(2)
    
    # Restaurar configuraciones normales
    if await optimizer.restore_normal_settings():
        print("✅ Configuraciones restauradas")
    
    # Crear índices de performance
    if await optimizer.create_performance_indexes():
        print("✅ Índices de performance creados")
    
    # Analizar estadísticas
    stats = await optimizer.analyze_table_statistics()
    if stats:
        print("✅ Análisis de estadísticas completado")

if __name__ == "__main__":
    asyncio.run(main())