#!/usr/bin/env python3
"""
PRUEBA DE CONCEPTO - ACTUALIZACIÓN POR LADAS
============================================
Prueba la estrategia de actualización con una muestra pequeña
para validar el enfoque antes de ejecutar en los 31.8M registros.

Prueba con ~1000 contactos de LADAs específicas
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import time

class LadasConceptTest:
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
            return None
    
    def create_test_reference(self, conn):
        """Crear tabla de referencia de prueba con algunas LADAs"""
        try:
            cursor = conn.cursor()
            
            print("🧪 Creando tabla de referencia de prueba...")
            
            cursor.execute("""
                DROP TABLE IF EXISTS ladas_reference_test CASCADE;
                
                CREATE TABLE ladas_reference_test (
                    lada VARCHAR(3) PRIMARY KEY,
                    estado VARCHAR(50) NOT NULL,
                    municipio VARCHAR(100) NOT NULL
                );
                
                -- Insertar algunas LADAs de prueba del CSV
                INSERT INTO ladas_reference_test (lada, estado, municipio) VALUES
                ('667', 'SINALOA', 'CULIACAN'),
                ('669', 'SINALOA', 'MAZATLAN'),
                ('687', 'SINALOA', 'LOS MOCHIS'),
                ('694', 'SINALOA', 'GUASAVE'),
                ('555', 'DISTRITO FEDERAL', 'MEXICO'),
                ('999', 'YUCATAN', 'MERIDA'),
                ('311', 'NAYARIT', 'TEPIC'),
                ('322', 'JALISCO', 'GUADALAJARA');
            """)
            
            conn.commit()
            cursor.close()
            
            print("✅ Tabla de referencia de prueba creada")
            return True
            
        except Exception as e:
            print(f"❌ Error creando tabla de prueba: {e}")
            conn.rollback()
            return False
    
    def analyze_current_state(self, conn):
        """Analizar el estado actual de las LADAs de prueba"""
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            print("\n📊 ESTADO ACTUAL (ANTES DE ACTUALIZAR):")
            print("-" * 70)
            
            cursor.execute("""
                SELECT 
                    c.lada,
                    c.state_name as estado_actual,
                    c.municipality as municipio_actual,
                    lr.estado as estado_correcto,
                    lr.municipio as municipio_correcto,
                    COUNT(*) as total_contactos,
                    CASE 
                        WHEN UPPER(TRIM(c.state_name)) = UPPER(TRIM(lr.estado)) THEN 'CORRECTO'
                        ELSE 'INCORRECTO'
                    END as estado_match
                FROM contacts c
                INNER JOIN ladas_reference_test lr ON c.lada = lr.lada
                WHERE c.lada IN ('667', '669', '687', '694', '555', '999', '311', '322')
                GROUP BY c.lada, c.state_name, c.municipality, lr.estado, lr.municipio
                ORDER BY c.lada, COUNT(*) DESC
            """)
            
            results = cursor.fetchall()
            
            print(f"{'LADA':<5} {'ACTUAL':<15} {'CORRECTO':<15} {'CONTACTOS':<10} {'STATUS':<10}")
            print("-" * 70)
            
            for row in results:
                print(f"{row['lada']:<5} {row['estado_actual'][:14]:<15} {row['estado_correcto'][:14]:<15} {row['total_contactos']:,<10} {row['estado_match']}")
            
            cursor.close()
            return results
            
        except Exception as e:
            print(f"❌ Error analizando estado actual: {e}")
            return []
    
    def execute_test_update(self, conn):
        """Ejecutar actualización de prueba"""
        try:
            cursor = conn.cursor()
            
            print("\n🚀 EJECUTANDO ACTUALIZACIÓN DE PRUEBA...")
            
            start_time = time.time()
            
            # Actualización usando JOIN (misma lógica que la función completa)
            cursor.execute("""
                UPDATE contacts 
                SET 
                    state_name = UPPER(TRIM(lr.estado)),
                    municipality = UPPER(TRIM(lr.municipio)),
                    updated_at = CURRENT_TIMESTAMP
                FROM ladas_reference_test lr 
                WHERE contacts.lada = lr.lada 
                  AND contacts.lada IN ('667', '669', '687', '694', '555', '999', '311', '322');
            """)
            
            updated_count = cursor.rowcount
            execution_time = time.time() - start_time
            
            conn.commit()
            cursor.close()
            
            print(f"✅ Actualización completada:")
            print(f"   • Registros actualizados: {updated_count:,}")
            print(f"   • Tiempo: {execution_time:.3f} segundos")
            print(f"   • Velocidad: {updated_count/execution_time:.0f} registros/segundo")
            
            return updated_count
            
        except Exception as e:
            print(f"❌ Error en actualización de prueba: {e}")
            conn.rollback()
            return 0
    
    def validate_test_results(self, conn):
        """Validar resultados de la prueba"""
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            print("\n🔍 VALIDANDO RESULTADOS (DESPUÉS DE ACTUALIZAR):")
            print("-" * 70)
            
            cursor.execute("""
                SELECT 
                    c.lada,
                    c.state_name as estado_actual,
                    c.municipality as municipio_actual,
                    lr.estado as estado_correcto,
                    lr.municipio as municipio_correcto,
                    COUNT(*) as total_contactos,
                    CASE 
                        WHEN UPPER(TRIM(c.state_name)) = UPPER(TRIM(lr.estado)) THEN '✅'
                        ELSE '❌'
                    END as estado_match,
                    CASE 
                        WHEN UPPER(TRIM(c.municipality)) = UPPER(TRIM(lr.municipio)) THEN '✅'
                        ELSE '❌'
                    END as municipio_match
                FROM contacts c
                INNER JOIN ladas_reference_test lr ON c.lada = lr.lada
                WHERE c.lada IN ('667', '669', '687', '694', '555', '999', '311', '322')
                GROUP BY c.lada, c.state_name, c.municipality, lr.estado, lr.municipio
                ORDER BY c.lada, COUNT(*) DESC
            """)
            
            results = cursor.fetchall()
            
            print(f"{'LADA':<5} {'ESTADO':<15} {'MUNICIPIO':<15} {'CONTACTOS':<10} {'EST':<3} {'MUN':<3}")
            print("-" * 70)
            
            total_correct = 0
            total_contacts = 0
            
            for row in results:
                total_contacts += row['total_contactos']
                if row['estado_match'] == '✅' and row['municipio_match'] == '✅':
                    total_correct += row['total_contactos']
                    
                print(f"{row['lada']:<5} {row['estado_actual'][:14]:<15} {row['municipio_actual'][:14]:<15} {row['total_contactos']:,<10} {row['estado_match']:<3} {row['municipio_match']}")
            
            success_rate = (total_correct / total_contacts * 100) if total_contacts > 0 else 0
            
            print("-" * 70)
            print(f"📊 RESULTADOS: {total_correct:,}/{total_contacts:,} contactos correctos ({success_rate:.1f}%)")
            
            cursor.close()
            return success_rate >= 95  # Consideramos éxito si >= 95% están correctos
            
        except Exception as e:
            print(f"❌ Error validando resultados: {e}")
            return False
    
    def cleanup_test(self, conn):
        """Limpiar tabla de prueba"""
        try:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS ladas_reference_test CASCADE;")
            conn.commit()
            cursor.close()
            print("🧹 Limpieza completada")
        except:
            pass
    
    def run(self):
        """Ejecutar prueba de concepto completa"""
        print("🧪 INICIANDO PRUEBA DE CONCEPTO - ACTUALIZACIÓN POR LADAS")
        print("=" * 60)
        
        conn = self.connect_db()
        if not conn:
            return False
        
        try:
            # Crear tabla de referencia de prueba
            if not self.create_test_reference(conn):
                return False
            
            # Analizar estado actual
            current_results = self.analyze_current_state(conn)
            if not current_results:
                print("⚠️  No se encontraron datos para analizar")
            
            # Ejecutar actualización
            updated_count = self.execute_test_update(conn)
            if updated_count == 0:
                print("❌ No se actualizaron registros")
                return False
            
            # Validar resultados
            success = self.validate_test_results(conn)
            
            # Limpiar
            self.cleanup_test(conn)
            
            print("\n" + "=" * 60)
            if success:
                print("🎉 PRUEBA DE CONCEPTO EXITOSA")
                print("✅ La estrategia funciona correctamente")
                print("💡 Listo para ejecutar actualización masiva completa")
            else:
                print("⚠️  PRUEBA DE CONCEPTO CON PROBLEMAS")
                print("❌ Revisar estrategia antes de ejecutar masivamente")
            print("=" * 60)
            
            return success
            
        except Exception as e:
            print(f"❌ Error en prueba de concepto: {e}")
            return False
            
        finally:
            conn.close()

def main():
    """Función principal"""
    test = LadasConceptTest()
    
    if test.run():
        print("\n🚀 ¿Proceder con actualización masiva completa?")
        print("   Ejecutar: python scripts/execute_ladas_mass_update.py")
    else:
        print("\n❌ Revisar problemas antes de continuar")

if __name__ == "__main__":
    main()
