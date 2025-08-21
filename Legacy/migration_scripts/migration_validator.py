#!/usr/bin/env python3
"""
Validador de Migración - Verificación de integridad post-migración
SMS Marketing Platform
"""

import asyncio
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple
import logging

import asyncpg

logger = logging.getLogger(__name__)

class MigrationValidator:
    """Validador completo de migración de datos"""
    
    def __init__(self, 
                 sqlite_path: str = "numeros.db",
                 postgres_url: str = "postgresql://sms_user:sms_password@localhost:15432/sms_marketing"):
        self.sqlite_path = sqlite_path
        self.postgres_url = postgres_url
        self.validation_results = {}
        
    async def validate_complete_migration(self) -> Dict[str, Any]:
        """Ejecutar validación completa de migración"""
        
        logger.info("🔍 Iniciando validación completa de migración")
        
        # Conectar a ambas bases de datos
        pg_conn = await asyncpg.connect(self.postgres_url)
        sqlite_conn = sqlite3.connect(self.sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        
        try:
            results = {
                "validation_timestamp": datetime.now().isoformat(),
                "tests": {}
            }
            
            # Test 1: Conteo de registros
            results["tests"]["record_count"] = await self._test_record_count(pg_conn, sqlite_conn)
            
            # Test 2: Integridad de números telefónicos
            results["tests"]["phone_integrity"] = await self._test_phone_integrity(pg_conn, sqlite_conn)
            
            # Test 3: Distribución geográfica
            results["tests"]["geographic_distribution"] = await self._test_geographic_distribution(pg_conn, sqlite_conn)
            
            # Test 4: Calidad de datos
            results["tests"]["data_quality"] = await self._test_data_quality(pg_conn)
            
            # Test 5: Normalización de status
            results["tests"]["status_distribution"] = await self._test_status_distribution(pg_conn)
            
            # Test 6: Integridad referencial
            results["tests"]["referential_integrity"] = await self._test_referential_integrity(pg_conn)
            
            # Test 7: Performance de consultas
            results["tests"]["query_performance"] = await self._test_query_performance(pg_conn)
            
            # Calcular score general
            results["overall_score"] = self._calculate_overall_score(results["tests"])
            results["validation_passed"] = results["overall_score"] >= 0.95
            
            self.validation_results = results
            
            # Generar reporte
            await self._generate_validation_report(results)
            
            return results
            
        finally:
            await pg_conn.close()
            sqlite_conn.close()
    
    async def _test_record_count(self, pg_conn: asyncpg.Connection, sqlite_conn: sqlite3.Connection) -> Dict[str, Any]:
        """Test 1: Validar conteo de registros"""
        logger.info("📊 Test 1: Validando conteo de registros")
        
        # Contar en PostgreSQL
        pg_result = await pg_conn.fetchrow("SELECT COUNT(*) FROM contacts")
        pg_count = pg_result[0]
        
        # Contar en SQLite
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM numeros")
        sqlite_count = cursor.fetchone()[0]
        
        difference = abs(pg_count - sqlite_count)
        success_rate = 1 - (difference / sqlite_count) if sqlite_count > 0 else 0
        
        result = {
            "sqlite_count": sqlite_count,
            "postgresql_count": pg_count,
            "difference": difference,
            "success_rate": success_rate,
            "passed": difference <= (sqlite_count * 0.01)  # Permitir 1% de diferencia
        }
        
        logger.info(f"   SQLite: {sqlite_count:,} | PostgreSQL: {pg_count:,} | Diferencia: {difference:,}")
        
        return result
    
    async def _test_phone_integrity(self, pg_conn: asyncpg.Connection, sqlite_conn: sqlite3.Connection) -> Dict[str, Any]:
        """Test 2: Validar integridad de números telefónicos"""
        logger.info("📞 Test 2: Validando integridad de números telefónicos")
        
        # Validar formato E.164
        e164_result = await pg_conn.fetchrow("""
            SELECT COUNT(*) FROM contacts 
            WHERE phone_e164 IS NOT NULL 
            AND phone_e164 ~ '^\\+52[0-9]{10}$'
        """)
        valid_e164 = e164_result[0]
        
        # Validar formato nacional
        national_result = await pg_conn.fetchrow("""
            SELECT COUNT(*) FROM contacts 
            WHERE phone_national IS NOT NULL 
            AND phone_national ~ '^[0-9]{10}$'
        """)
        valid_national = national_result[0]
        
        # Total de registros
        total_result = await pg_conn.fetchrow("SELECT COUNT(*) FROM contacts")
        total_count = total_result[0]
        
        # Verificar muestra aleatoria de números
        sample_result = await pg_conn.fetch("""
            SELECT phone_e164, phone_national, phone_original 
            FROM contacts 
            WHERE phone_e164 IS NOT NULL 
            ORDER BY RANDOM() 
            LIMIT 100
        """)
        
        valid_sample = 0
        for row in sample_result:
            if row['phone_e164'] and row['phone_national']:
                # Verificar consistencia E.164 vs Nacional
                expected_e164 = f"+52{row['phone_national']}"
                if row['phone_e164'] == expected_e164:
                    valid_sample += 1
        
        sample_consistency = valid_sample / len(sample_result) if sample_result else 0
        
        result = {
            "total_records": total_count,
            "valid_e164_count": valid_e164,
            "valid_national_count": valid_national,
            "e164_success_rate": valid_e164 / total_count if total_count > 0 else 0,
            "national_success_rate": valid_national / total_count if total_count > 0 else 0,
            "sample_consistency": sample_consistency,
            "passed": (valid_e164 / total_count >= 0.95) and (sample_consistency >= 0.98)
        }
        
        logger.info(f"   E.164 válidos: {valid_e164:,} ({result['e164_success_rate']:.1%})")
        logger.info(f"   Nacional válidos: {valid_national:,} ({result['national_success_rate']:.1%})")
        
        return result
    
    async def _test_geographic_distribution(self, pg_conn: asyncpg.Connection, sqlite_conn: sqlite3.Connection) -> Dict[str, Any]:
        """Test 3: Validar distribución geográfica"""
        logger.info("🗺️  Test 3: Validando distribución geográfica")
        
        # Distribución por estado en PostgreSQL
        pg_states = await pg_conn.fetch("""
            SELECT state_code, COUNT(*) as count 
            FROM contacts 
            WHERE state_code IS NOT NULL 
            GROUP BY state_code 
            ORDER BY count DESC
        """)
        
        # Distribución por LADA en PostgreSQL
        pg_ladas = await pg_conn.fetch("""
            SELECT lada, COUNT(*) as count 
            FROM contacts 
            WHERE lada IS NOT NULL 
            GROUP BY lada 
            ORDER BY count DESC 
            LIMIT 20
        """)
        
        # Comparar con SQLite (muestra)
        cursor = sqlite_conn.cursor()
        cursor.execute("""
            SELECT estado_cof, COUNT(*) as count 
            FROM numeros 
            WHERE estado_cof IS NOT NULL 
            GROUP BY estado_cof 
            ORDER BY count DESC 
            LIMIT 10
        """)
        sqlite_states = cursor.fetchall()
        
        result = {
            "postgresql_states": [{"state": row['state_code'], "count": row['count']} for row in pg_states[:10]],
            "postgresql_ladas": [{"lada": row['lada'], "count": row['count']} for row in pg_ladas],
            "sqlite_states_sample": [{"state": row[0], "count": row[1]} for row in sqlite_states],
            "total_states": len(pg_states),
            "total_ladas": len([row for row in pg_ladas]),
            "passed": len(pg_states) >= 20 and len(pg_ladas) >= 50  # Esperamos buena distribución
        }
        
        logger.info(f"   Estados únicos: {len(pg_states)}")
        logger.info(f"   LADAs únicas: {len(pg_ladas)}")
        
        return result
    
    async def _test_data_quality(self, pg_conn: asyncpg.Connection) -> Dict[str, Any]:
        """Test 4: Validar calidad de datos"""
        logger.info("✨ Test 4: Validando calidad de datos")
        
        # Porcentaje de campos no nulos
        quality_result = await pg_conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(full_name) as has_name,
                COUNT(address) as has_address,
                COUNT(neighborhood) as has_neighborhood,
                COUNT(municipality) as has_municipality,
                COUNT(city) as has_city,
                COUNT(lada) as has_lada,
                COUNT(state_code) as has_state
            FROM contacts
        """)
        
        total = quality_result['total']
        
        # Calcular porcentajes de completitud
        completeness = {
            "full_name": quality_result['has_name'] / total,
            "address": quality_result['has_address'] / total,
            "neighborhood": quality_result['has_neighborhood'] / total,
            "municipality": quality_result['has_municipality'] / total,
            "city": quality_result['has_city'] / total,
            "lada": quality_result['has_lada'] / total,
            "state_code": quality_result['has_state'] / total
        }
        
        # Detectar duplicados por teléfono
        duplicates_result = await pg_conn.fetchrow("""
            SELECT COUNT(*) - COUNT(DISTINCT phone_e164) as duplicates
            FROM contacts
            WHERE phone_e164 IS NOT NULL
        """)
        duplicates = duplicates_result['duplicates']
        
        # Score de calidad general
        avg_completeness = sum(completeness.values()) / len(completeness)
        duplicate_rate = duplicates / total if total > 0 else 0
        quality_score = avg_completeness * (1 - duplicate_rate)
        
        result = {
            "total_records": total,
            "completeness": completeness,
            "duplicates": duplicates,
            "duplicate_rate": duplicate_rate,
            "average_completeness": avg_completeness,
            "quality_score": quality_score,
            "passed": quality_score >= 0.8
        }
        
        logger.info(f"   Completitud promedio: {avg_completeness:.1%}")
        logger.info(f"   Duplicados: {duplicates:,} ({duplicate_rate:.2%})")
        
        return result
    
    async def _test_status_distribution(self, pg_conn: asyncpg.Connection) -> Dict[str, Any]:
        """Test 5: Validar distribución de status"""
        logger.info("📊 Test 5: Validando distribución de status")
        
        status_result = await pg_conn.fetch("""
            SELECT status, COUNT(*) as count 
            FROM contacts 
            GROUP BY status 
            ORDER BY count DESC
        """)
        
        total_result = await pg_conn.fetchrow("SELECT COUNT(*) FROM contacts")
        total = total_result[0]
        
        distribution = {}
        for row in status_result:
            distribution[row['status']] = {
                "count": row['count'],
                "percentage": row['count'] / total
            }
        
        # Verificar que no hay demasiados UNKNOWN
        unknown_rate = distribution.get('UNKNOWN', {}).get('percentage', 0)
        verified_rate = distribution.get('VERIFIED', {}).get('percentage', 0) + distribution.get('NOT_MOBILE', {}).get('percentage', 0)
        
        result = {
            "distribution": distribution,
            "unknown_rate": unknown_rate,
            "verified_rate": verified_rate,
            "total_statuses": len(distribution),
            "passed": unknown_rate < 0.5 and verified_rate > 0.4
        }
        
        logger.info("   Distribución de status:")
        for status, data in distribution.items():
            logger.info(f"     {status}: {data['count']:,} ({data['percentage']:.1%})")
        
        return result
    
    async def _test_referential_integrity(self, pg_conn: asyncpg.Connection) -> Dict[str, Any]:
        """Test 6: Validar integridad referencial"""
        logger.info("🔗 Test 6: Validando integridad referencial")
        
        # Verificar constraints
        constraints_result = await pg_conn.fetch("""
            SELECT conname, contype 
            FROM pg_constraint 
            WHERE conrelid = 'contacts'::regclass
        """)
        
        # Verificar índices
        indexes_result = await pg_conn.fetch("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'contacts'
        """)
        
        # Verificar unicidad de phone_e164
        unique_result = await pg_conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT phone_e164) as unique_phones
            FROM contacts
            WHERE phone_e164 IS NOT NULL
        """)
        
        uniqueness_rate = unique_result['unique_phones'] / unique_result['total'] if unique_result['total'] > 0 else 0
        
        result = {
            "constraints_count": len(constraints_result),
            "indexes_count": len(indexes_result),
            "phone_uniqueness_rate": uniqueness_rate,
            "constraints": [{"name": row['conname'], "type": row['contype']} for row in constraints_result],
            "passed": len(constraints_result) >= 5 and uniqueness_rate >= 0.99
        }
        
        logger.info(f"   Constraints: {len(constraints_result)}")
        logger.info(f"   Índices: {len(indexes_result)}")
        logger.info(f"   Unicidad teléfonos: {uniqueness_rate:.2%}")
        
        return result
    
    async def _test_query_performance(self, pg_conn: asyncpg.Connection) -> Dict[str, Any]:
        """Test 7: Validar performance de consultas"""
        logger.info("⚡ Test 7: Validando performance de consultas")
        
        import time
        
        performance_tests = []
        
        # Test 1: Búsqueda por teléfono
        start_time = time.time()
        await pg_conn.fetchrow("SELECT * FROM contacts WHERE phone_e164 = '+525512345678' LIMIT 1")
        phone_search_time = time.time() - start_time
        performance_tests.append({"query": "phone_search", "time": phone_search_time})
        
        # Test 2: Filtro por estado
        start_time = time.time()
        await pg_conn.fetch("SELECT COUNT(*) FROM contacts WHERE state_code = 'CDMX'")
        state_filter_time = time.time() - start_time
        performance_tests.append({"query": "state_filter", "time": state_filter_time})
        
        # Test 3: Agregación por LADA
        start_time = time.time()
        await pg_conn.fetch("SELECT lada, COUNT(*) FROM contacts GROUP BY lada ORDER BY COUNT(*) DESC LIMIT 10")
        lada_aggregation_time = time.time() - start_time
        performance_tests.append({"query": "lada_aggregation", "time": lada_aggregation_time})
        
        # Test 4: Búsqueda de texto
        start_time = time.time()
        await pg_conn.fetch("SELECT * FROM contacts WHERE full_name ILIKE '%MARIA%' LIMIT 10")
        text_search_time = time.time() - start_time
        performance_tests.append({"query": "text_search", "time": text_search_time})
        
        avg_time = sum(test["time"] for test in performance_tests) / len(performance_tests)
        
        result = {
            "performance_tests": performance_tests,
            "average_query_time": avg_time,
            "passed": avg_time < 1.0  # Todas las consultas deben ser < 1 segundo
        }
        
        logger.info(f"   Tiempo promedio de consulta: {avg_time:.3f}s")
        
        return result
    
    def _calculate_overall_score(self, tests: Dict[str, Any]) -> float:
        """Calcular score general de validación"""
        
        weights = {
            "record_count": 0.25,
            "phone_integrity": 0.20,
            "geographic_distribution": 0.15,
            "data_quality": 0.15,
            "status_distribution": 0.10,
            "referential_integrity": 0.10,
            "query_performance": 0.05
        }
        
        total_score = 0
        for test_name, weight in weights.items():
            if test_name in tests and tests[test_name].get("passed", False):
                total_score += weight
        
        return total_score
    
    async def _generate_validation_report(self, results: Dict[str, Any]):
        """Generar reporte de validación"""
        
        report_path = f"migration_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📋 Reporte de validación generado: {report_path}")
        
        # Log resumen
        logger.info("\n" + "="*60)
        logger.info("📊 RESUMEN DE VALIDACIÓN")
        logger.info("="*60)
        
        for test_name, test_result in results["tests"].items():
            status = "✅ PASS" if test_result.get("passed", False) else "❌ FAIL"
            logger.info(f"{status} {test_name.replace('_', ' ').title()}")
        
        logger.info(f"\n🎯 Score General: {results['overall_score']:.1%}")
        logger.info(f"📋 Validación: {'✅ EXITOSA' if results['validation_passed'] else '❌ FALLIDA'}")
        logger.info("="*60)

async def main():
    """Función principal de validación"""
    print("🔍 Validador de Migración - SMS Marketing Platform")
    print("="*60)
    
    validator = MigrationValidator()
    
    results = await validator.validate_complete_migration()
    
    if results["validation_passed"]:
        print("\n✅ VALIDACIÓN EXITOSA!")
        print(f"🎯 Score: {results['overall_score']:.1%}")
    else:
        print("\n❌ VALIDACIÓN FALLIDA")
        print("🔧 Revisar reporte para detalles")

if __name__ == "__main__":
    asyncio.run(main())