#!/usr/bin/env python3
"""
EJECUTOR DE ACTUALIZACIÓN MASIVA POR LADAS
==========================================
Ejecuta la actualización masiva de 31.8M contactos basándose en LADAs
usando la estrategia más optimizada posible.

PROCESO:
1. Cargar tabla de referencia ladas_reference
2. Optimizar configuración PostgreSQL 
3. Ejecutar UPDATE masivo con JOIN
4. Validar resultados
5. Generar reporte completo

Tiempo estimado: 10-15 minutos para 31.8M registros
"""

import os
import sys
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import subprocess

class LadasMassUpdater:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': 15432,
            'database': 'sms_marketing',
            'user': 'sms_user', 
            'password': 'sms_password'
        }
        
    def connect_db(self):
        """Conectar a PostgreSQL"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            print(f"❌ Error conectando a BD: {e}")
            sys.exit(1)
    
    def load_reference_data(self):
        """Cargar datos de referencia usando el script dedicado"""
        print("📥 PASO 1: CARGANDO DATOS DE REFERENCIA")
        print("-" * 40)
        
        try:
            # Ejecutar script de carga
            result = subprocess.run([
                sys.executable, 
                'scripts/load_ladas_reference.py'
            ], capture_output=True, text=True, cwd='.')
            
            if result.returncode == 0:
                print("✅ Datos de referencia cargados exitosamente")
                print(result.stdout)
                return True
            else:
                print("❌ Error cargando datos de referencia:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Error ejecutando carga: {e}")
            return False
    
    def optimize_postgres_config(self, conn):
        """Optimizar configuración de PostgreSQL para UPDATE masivo"""
        print("\n⚡ PASO 2: OPTIMIZANDO CONFIGURACIÓN POSTGRESQL")
        print("-" * 40)
        
        try:
            cursor = conn.cursor()
            
            optimizations = [
                ("work_mem", "512MB", "Memoria para operaciones de trabajo"),
                ("maintenance_work_mem", "1GB", "Memoria para mantenimiento"), 
                ("synchronous_commit", "OFF", "Desactivar commit síncrono"),
                ("checkpoint_completion_target", "0.9", "Optimizar checkpoints"),
                ("wal_buffers", "64MB", "Buffers de WAL"),
                ("effective_io_concurrency", "200", "Concurrencia de I/O")
            ]
            
            for param, value, description in optimizations:
                try:
                    cursor.execute(f"SET {param} = '{value}';")
                    print(f"✅ {param} = {value} ({description})")
                except Exception as e:
                    print(f"⚠️  No se pudo configurar {param}: {e}")
            
            cursor.close()
            print("✅ Configuración optimizada")
            return True
            
        except Exception as e:
            print(f"❌ Error optimizando configuración: {e}")
            return False
    
    def create_update_functions(self, conn):
        """Crear funciones de actualización y validación"""
        print("\n🔧 PASO 3: CREANDO FUNCIONES DE ACTUALIZACIÓN")
        print("-" * 40)
        
        try:
            cursor = conn.cursor()
            
            # Leer y ejecutar el SQL con las funciones
            with open('scripts/ladas_mass_update_strategy.sql', 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Extraer solo las funciones (desde CREATE OR REPLACE FUNCTION)
            functions_sql = """
            CREATE OR REPLACE FUNCTION update_contacts_by_lada()
            RETURNS TABLE(
                total_updated BIGINT,
                execution_time INTERVAL,
                ladas_matched INTEGER,
                ladas_not_found INTEGER
            ) 
            LANGUAGE plpgsql AS $$
            DECLARE
                start_time TIMESTAMP;
                end_time TIMESTAMP;
                updated_count BIGINT;
                matched_ladas INTEGER;
                missing_ladas INTEGER;
            BEGIN
                start_time := clock_timestamp();
                
                -- Contar LADAs que coinciden
                SELECT COUNT(DISTINCT c.lada) INTO matched_ladas
                FROM contacts c 
                INNER JOIN ladas_reference lr ON c.lada = lr.lada
                WHERE c.lada IS NOT NULL;
                
                -- Contar LADAs que NO coinciden
                SELECT COUNT(DISTINCT c.lada) INTO missing_ladas
                FROM contacts c 
                LEFT JOIN ladas_reference lr ON c.lada = lr.lada
                WHERE c.lada IS NOT NULL AND lr.lada IS NULL;
                
                -- Actualización masiva optimizada
                UPDATE contacts 
                SET 
                    state_name = UPPER(TRIM(lr.estado)),
                    municipality = UPPER(TRIM(lr.municipio)),
                    updated_at = CURRENT_TIMESTAMP
                FROM ladas_reference lr 
                WHERE contacts.lada = lr.lada 
                  AND contacts.lada IS NOT NULL;
                
                GET DIAGNOSTICS updated_count = ROW_COUNT;
                
                end_time := clock_timestamp();
                
                RETURN QUERY SELECT 
                    updated_count,
                    end_time - start_time,
                    matched_ladas,
                    missing_ladas;
            END;
            $$;

            CREATE OR REPLACE FUNCTION validate_ladas_update()
            RETURNS TABLE(
                lada_code VARCHAR(3),
                estado_csv VARCHAR(50),
                estado_bd VARCHAR(50),
                municipio_csv VARCHAR(100),
                municipio_bd VARCHAR(100),
                total_contacts BIGINT,
                match_estado BOOLEAN,
                match_municipio BOOLEAN
            )
            LANGUAGE plpgsql AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    lr.lada,
                    lr.estado,
                    c.state_name,
                    lr.municipio,
                    c.municipality,
                    COUNT(c.id) as total_contacts,
                    (UPPER(TRIM(lr.estado)) = UPPER(TRIM(c.state_name))) as match_estado,
                    (UPPER(TRIM(lr.municipio)) = UPPER(TRIM(c.municipality))) as match_municipio
                FROM ladas_reference lr
                LEFT JOIN contacts c ON lr.lada = c.lada
                WHERE c.lada IS NOT NULL
                GROUP BY lr.lada, lr.estado, lr.municipio, c.state_name, c.municipality
                ORDER BY COUNT(c.id) DESC
                LIMIT 50;
            END;
            $$;
            """
            
            cursor.execute(functions_sql)
            conn.commit()
            cursor.close()
            
            print("✅ Funciones creadas exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error creando funciones: {e}")
            conn.rollback()
            return False
    
    def execute_mass_update(self, conn):
        """Ejecutar la actualización masiva"""
        print("\n🚀 PASO 4: EJECUTANDO ACTUALIZACIÓN MASIVA")
        print("-" * 40)
        print("⏳ Esto puede tomar 5-15 minutos para 31.8M registros...")
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Ejecutar función de actualización
            start_time = time.time()
            cursor.execute("SELECT * FROM update_contacts_by_lada();")
            result = cursor.fetchone()
            execution_time = time.time() - start_time
            
            print(f"\n🎉 ACTUALIZACIÓN COMPLETADA:")
            print(f"   • Registros actualizados: {result['total_updated']:,}")
            print(f"   • Tiempo de ejecución BD: {result['execution_time']}")
            print(f"   • Tiempo total: {execution_time:.2f} segundos")
            print(f"   • LADAs coincidentes: {result['ladas_matched']}")
            print(f"   • LADAs no encontradas: {result['ladas_not_found']}")
            print(f"   • Velocidad: {result['total_updated']/execution_time:.0f} registros/segundo")
            
            cursor.close()
            return result
            
        except Exception as e:
            print(f"❌ Error en actualización masiva: {e}")
            return None
    
    def validate_results(self, conn):
        """Validar los resultados de la actualización"""
        print("\n🔍 PASO 5: VALIDANDO RESULTADOS")
        print("-" * 40)
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Ejecutar validación
            cursor.execute("SELECT * FROM validate_ladas_update();")
            validation_results = cursor.fetchall()
            
            print("📊 TOP 20 LADAS ACTUALIZADAS:")
            print("-" * 80)
            print(f"{'LADA':<5} {'ESTADO':<15} {'MUNICIPIO':<20} {'CONTACTOS':<12} {'✓':<3}")
            print("-" * 80)
            
            total_validated = 0
            matches = 0
            
            for i, row in enumerate(validation_results[:20]):
                status = "✅" if (row['match_estado'] and row['match_municipio']) else "❌"
                if row['match_estado'] and row['match_municipio']:
                    matches += 1
                    
                total_validated += row['total_contacts']
                
                print(f"{row['lada_code']:<5} {row['estado_csv'][:14]:<15} {row['municipio_csv'][:19]:<20} {row['total_contacts']:,<12} {status}")
            
            print("-" * 80)
            print(f"✅ Validación: {matches}/{min(20, len(validation_results))} LADAs correctas")
            print(f"📊 Total contactos validados: {total_validated:,}")
            
            # Estadísticas generales post-actualización
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_contacts,
                    COUNT(CASE WHEN state_name IS NOT NULL THEN 1 END) as with_state,
                    COUNT(CASE WHEN municipality IS NOT NULL THEN 1 END) as with_municipality,
                    COUNT(DISTINCT state_name) as unique_states,
                    COUNT(DISTINCT municipality) as unique_municipalities
                FROM contacts 
                WHERE lada IS NOT NULL
            """)
            
            stats = cursor.fetchone()
            
            print(f"\n📈 ESTADÍSTICAS FINALES:")
            print(f"   • Total contactos: {stats['total_contacts']:,}")
            print(f"   • Con estado: {stats['with_state']:,} ({stats['with_state']/stats['total_contacts']*100:.1f}%)")
            print(f"   • Con municipio: {stats['with_municipality']:,} ({stats['with_municipality']/stats['total_contacts']*100:.1f}%)")
            print(f"   • Estados únicos: {stats['unique_states']}")
            print(f"   • Municipios únicos: {stats['unique_municipalities']}")
            
            cursor.close()
            return True
            
        except Exception as e:
            print(f"❌ Error validando resultados: {e}")
            return False
    
    def generate_final_report(self, conn, update_result):
        """Generar reporte final del proceso"""
        print("\n📋 PASO 6: GENERANDO REPORTE FINAL")
        print("-" * 40)
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Reporte de LADAs problemáticas
            cursor.execute("""
                SELECT 
                    c.lada,
                    COUNT(*) as total_contacts,
                    COUNT(DISTINCT c.state_name) as different_states
                FROM contacts c
                LEFT JOIN ladas_reference lr ON c.lada = lr.lada
                WHERE c.lada IS NOT NULL AND lr.lada IS NULL
                GROUP BY c.lada
                ORDER BY COUNT(*) DESC
                LIMIT 10
            """)
            
            missing_ladas = cursor.fetchall()
            
            if missing_ladas:
                print("\n⚠️  LADAs SIN REFERENCIA (TOP 10):")
                print(f"{'LADA':<5} {'CONTACTOS':<12} {'ESTADOS':<8}")
                print("-" * 25)
                for row in missing_ladas:
                    print(f"{row['lada']:<5} {row['total_contacts']:,<12} {row['different_states']}")
            
            # Generar timestamp del reporte
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            report_content = f"""
# REPORTE DE ACTUALIZACIÓN MASIVA POR LADAS
Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Estrategia: Tabla de referencia + UPDATE masivo

## RESULTADOS:
- Registros actualizados: {update_result['total_updated']:,}
- Tiempo de ejecución: {update_result['execution_time']}
- LADAs coincidentes: {update_result['ladas_matched']}
- LADAs no encontradas: {update_result['ladas_not_found']}

## PRÓXIMOS PASOS:
1. Revisar LADAs faltantes en ladas_reference
2. Actualizar archivo LADAS2025.CSV con LADAs faltantes
3. Re-ejecutar proceso para LADAs faltantes

## COMANDO PARA RESTAURAR (si es necesario):
pg_restore -U sms_user -d sms_marketing ./backups/backup_sinaloa_fixed_20250808.backup
            """
            
            with open(f'reports/ladas_update_report_{timestamp}.md', 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"📄 Reporte guardado: reports/ladas_update_report_{timestamp}.md")
            
            cursor.close()
            return True
            
        except Exception as e:
            print(f"❌ Error generando reporte: {e}")
            return False
    
    def run(self):
        """Ejecutar el proceso completo"""
        print("🚀 INICIANDO ACTUALIZACIÓN MASIVA POR LADAS")
        print("=" * 60)
        print("📊 Objetivo: Actualizar 31.8M contactos con estado/municipio correcto")
        print("⏱️  Tiempo estimado: 10-15 minutos")
        print("=" * 60)
        
        # Crear carpeta de reportes
        os.makedirs('reports', exist_ok=True)
        
        start_time = time.time()
        
        # Paso 1: Cargar datos de referencia
        if not self.load_reference_data():
            print("❌ Falló la carga de datos de referencia")
            return False
        
        # Conectar a BD
        conn = self.connect_db()
        
        try:
            # Paso 2: Optimizar configuración
            if not self.optimize_postgres_config(conn):
                print("⚠️  Advertencia: No se pudo optimizar configuración")
            
            # Paso 3: Crear funciones
            if not self.create_update_functions(conn):
                print("❌ Falló la creación de funciones")
                return False
            
            # Paso 4: Ejecutar actualización masiva
            update_result = self.execute_mass_update(conn)
            if not update_result:
                print("❌ Falló la actualización masiva")
                return False
            
            # Paso 5: Validar resultados
            if not self.validate_results(conn):
                print("⚠️  Advertencia: Falló la validación")
            
            # Paso 6: Generar reporte
            self.generate_final_report(conn, update_result)
            
            total_time = time.time() - start_time
            
            print("\n" + "=" * 60)
            print("🎉 ACTUALIZACIÓN MASIVA COMPLETADA EXITOSAMENTE")
            print(f"📊 Registros actualizados: {update_result['total_updated']:,}")
            print(f"⏱️  Tiempo total: {total_time:.2f} segundos ({total_time/60:.1f} minutos)")
            print(f"⚡ Velocidad promedio: {update_result['total_updated']/total_time:.0f} registros/segundo")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"❌ Error en proceso: {e}")
            return False
            
        finally:
            conn.close()

def main():
    """Función principal"""
    updater = LadasMassUpdater()
    
    print("⚠️  ADVERTENCIA: Este proceso modificará 31.8M registros")
    print("📦 Backup disponible: ./backups/backup_sinaloa_fixed_20250808.backup")
    
    response = input("\n¿Continuar con la actualización masiva? (y/N): ").lower().strip()
    
    if response != 'y':
        print("❌ Proceso cancelado por el usuario")
        sys.exit(0)
    
    if updater.run():
        print("\n🎉 ¡Proceso completado exitosamente!")
        print("💡 Los contactos ahora tienen estado y municipio basado en LADA")
        sys.exit(0)
    else:
        print("\n❌ Proceso falló")
        sys.exit(1)

if __name__ == "__main__":
    main()
