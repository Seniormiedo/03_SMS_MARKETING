#!/usr/bin/env python3
"""
COMPLETAR ACTUALIZACIÓN DE LADAS FALTANTES
==========================================
Agregar las LADAs faltantes con la clasificación correcta y 
actualizar los 12.2M contactos restantes.

Clasificación:
- 55x (551,552,553,554,558,559) -> CDMX, CDMX
- 81x (811,812,813,818) -> NUEVO LEON, MONTERREY  
- 33x (331) -> JALISCO, GUADALAJARA
"""

import os
import sys
import time
import psycopg2
from psycopg2.extras import RealDictCursor

class CompleteLadasUpdater:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': 15432,
            'database': 'sms_marketing',
            'user': 'sms_user', 
            'password': 'sms_password'
        }
        
        # Definir las LADAs faltantes con su clasificación
        self.missing_ladas = {
            # LADAs 55x - CDMX
            '551': {'estado': 'CDMX', 'municipio': 'CDMX'},
            '552': {'estado': 'CDMX', 'municipio': 'CDMX'},
            '553': {'estado': 'CDMX', 'municipio': 'CDMX'},
            '554': {'estado': 'CDMX', 'municipio': 'CDMX'},
            '558': {'estado': 'CDMX', 'municipio': 'CDMX'},
            '559': {'estado': 'CDMX', 'municipio': 'CDMX'},
            
            # LADAs 81x - Nuevo León
            '811': {'estado': 'NUEVO LEON', 'municipio': 'MONTERREY'},
            '812': {'estado': 'NUEVO LEON', 'municipio': 'MONTERREY'},
            '813': {'estado': 'NUEVO LEON', 'municipio': 'MONTERREY'},
            '818': {'estado': 'NUEVO LEON', 'municipio': 'MONTERREY'},
            
            # LADAs 33x - Jalisco
            '331': {'estado': 'JALISCO', 'municipio': 'GUADALAJARA'}
        }
        
    def connect_db(self):
        """Conectar a PostgreSQL"""
        try:
            conn = psycopg2.connect(**self.db_config)
            conn.autocommit = False
            return conn
        except Exception as e:
            print(f"ERROR conectando a BD: {e}")
            sys.exit(1)
    
    def add_missing_ladas_to_reference(self, conn):
        """Agregar las LADAs faltantes a la tabla de referencia"""
        print("PASO 1: AGREGANDO LADAS FALTANTES A TABLA DE REFERENCIA")
        print("-" * 60)
        
        try:
            cursor = conn.cursor()
            
            # Insertar las LADAs faltantes
            for lada, info in self.missing_ladas.items():
                cursor.execute("""
                    INSERT INTO ladas_reference (lada, estado, municipio) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT (lada) DO UPDATE SET
                        estado = EXCLUDED.estado,
                        municipio = EXCLUDED.municipio
                """, (lada, info['estado'], info['municipio']))
                
                print(f"  + LADA {lada}: {info['estado']} - {info['municipio']}")
            
            conn.commit()
            
            # Verificar que se agregaron correctamente
            cursor.execute("SELECT COUNT(*) FROM ladas_reference")
            total_ladas = cursor.fetchone()[0]
            
            print(f"\nOK - Total LADAs en referencia: {total_ladas}")
            cursor.close()
            
            return True
            
        except Exception as e:
            print(f"ERROR agregando LADAs: {e}")
            conn.rollback()
            return False
    
    def count_contacts_to_update(self, conn):
        """Contar cuántos contactos se van a actualizar"""
        print("\nPASO 2: CONTANDO CONTACTOS A ACTUALIZAR")
        print("-" * 60)
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Contar contactos por LADA faltante
            ladas_str = "','".join(self.missing_ladas.keys())
            
            cursor.execute(f"""
                SELECT 
                    c.lada,
                    COUNT(*) as total_contactos
                FROM contacts c
                WHERE c.lada IN ('{ladas_str}')
                  AND c.lada IS NOT NULL
                GROUP BY c.lada
                ORDER BY COUNT(*) DESC
            """)
            
            results = cursor.fetchall()
            total_to_update = 0
            
            print("LADAs a actualizar:")
            print(f"{'LADA':<6} {'CONTACTOS':<12} {'ESTADO':<15} {'MUNICIPIO'}")
            print("-" * 60)
            
            for row in results:
                lada = row['lada']
                count = row['total_contactos']
                info = self.missing_ladas[lada]
                total_to_update += count
                
                print(f"{lada:<6} {count:,<12} {info['estado']:<15} {info['municipio']}")
            
            print("-" * 60)
            print(f"TOTAL A ACTUALIZAR: {total_to_update:,} contactos")
            
            cursor.close()
            return total_to_update
            
        except Exception as e:
            print(f"ERROR contando contactos: {e}")
            return 0
    
    def execute_final_update(self, conn):
        """Ejecutar la actualización final para las LADAs faltantes"""
        print("\nPASO 3: EJECUTANDO ACTUALIZACIÓN FINAL")
        print("-" * 60)
        print("ADVERTENCIA: Actualizando contactos restantes...")
        
        try:
            cursor = conn.cursor()
            
            start_time = time.time()
            
            # Ejecutar UPDATE para las LADAs faltantes específicamente
            ladas_str = "','".join(self.missing_ladas.keys())
            
            cursor.execute(f"""
                UPDATE contacts 
                SET 
                    state_name = UPPER(TRIM(lr.estado)),
                    municipality = UPPER(TRIM(lr.municipio)),
                    updated_at = CURRENT_TIMESTAMP
                FROM ladas_reference lr 
                WHERE contacts.lada = lr.lada 
                  AND contacts.lada IN ('{ladas_str}')
                  AND contacts.lada IS NOT NULL
            """)
            
            updated_count = cursor.rowcount
            execution_time = time.time() - start_time
            
            conn.commit()
            
            print(f"\nRESULTADOS ACTUALIZACIÓN FINAL:")
            print(f"  Registros actualizados: {updated_count:,}")
            print(f"  Tiempo de ejecución: {execution_time:.2f} segundos ({execution_time/60:.1f} minutos)")
            
            if updated_count > 0:
                speed = updated_count / execution_time
                print(f"  Velocidad: {speed:.0f} registros/segundo")
            
            cursor.close()
            
            return {
                'total_updated': updated_count,
                'execution_time': execution_time
            }
            
        except Exception as e:
            print(f"ERROR en actualización final: {e}")
            conn.rollback()
            return None
    
    def validate_final_results(self, conn):
        """Validar que no quede ningún contacto sin estado/municipio"""
        print("\nPASO 4: VALIDACIÓN FINAL COMPLETA")
        print("-" * 60)
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Contar contactos sin estado o municipio
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_contacts,
                    COUNT(CASE WHEN state_name IS NULL THEN 1 END) as sin_estado,
                    COUNT(CASE WHEN municipality IS NULL THEN 1 END) as sin_municipio,
                    COUNT(CASE WHEN state_name IS NULL OR municipality IS NULL THEN 1 END) as sin_datos,
                    COUNT(CASE WHEN state_name IS NOT NULL AND municipality IS NOT NULL THEN 1 END) as con_datos_completos
                FROM contacts 
                WHERE lada IS NOT NULL
            """)
            
            stats = cursor.fetchone()
            
            print("ESTADÍSTICAS FINALES COMPLETAS:")
            print(f"  Total contactos: {stats['total_contacts']:,}")
            print(f"  Sin estado: {stats['sin_estado']:,} ({stats['sin_estado']/stats['total_contacts']*100:.2f}%)")
            print(f"  Sin municipio: {stats['sin_municipio']:,} ({stats['sin_municipio']/stats['total_contacts']*100:.2f}%)")
            print(f"  Sin datos completos: {stats['sin_datos']:,} ({stats['sin_datos']/stats['total_contacts']*100:.2f}%)")
            print(f"  Con datos completos: {stats['con_datos_completos']:,} ({stats['con_datos_completos']/stats['total_contacts']*100:.2f}%)")
            
            # Mostrar muestra de LADAs actualizadas
            cursor.execute("""
                SELECT 
                    c.lada,
                    c.state_name,
                    c.municipality,
                    COUNT(*) as total_contactos
                FROM contacts c
                WHERE c.lada IN ('551', '552', '553', '554', '558', '559', '811', '812', '813', '818', '331')
                GROUP BY c.lada, c.state_name, c.municipality
                ORDER BY c.lada, COUNT(*) DESC
                LIMIT 20
            """)
            
            sample_results = cursor.fetchall()
            
            print(f"\nMUESTRA DE LADAS ACTUALIZADAS:")
            print(f"{'LADA':<6} {'ESTADO':<15} {'MUNICIPIO':<15} {'CONTACTOS':<12}")
            print("-" * 60)
            
            for row in sample_results:
                estado = row['state_name'] or 'NULL'
                municipio = row['municipality'] or 'NULL'
                print(f"{row['lada']:<6} {estado[:14]:<15} {municipio[:14]:<15} {row['total_contactos']:,<12}")
            
            # Verificar si quedan contactos sin datos
            success = stats['sin_datos'] == 0
            
            if success:
                print(f"\n✅ ÉXITO TOTAL: Todos los contactos tienen estado y municipio!")
            else:
                print(f"\n⚠️  ADVERTENCIA: Aún quedan {stats['sin_datos']:,} contactos sin datos completos")
                
                # Mostrar cuáles LADAs aún tienen problemas
                cursor.execute("""
                    SELECT 
                        c.lada,
                        COUNT(*) as contactos_sin_datos
                    FROM contacts c
                    WHERE c.lada IS NOT NULL 
                      AND (c.state_name IS NULL OR c.municipality IS NULL)
                    GROUP BY c.lada
                    ORDER BY COUNT(*) DESC
                    LIMIT 10
                """)
                
                problem_ladas = cursor.fetchall()
                
                if problem_ladas:
                    print(f"\nLADAs con problemas restantes:")
                    for row in problem_ladas:
                        print(f"  LADA {row['lada']}: {row['contactos_sin_datos']:,} contactos sin datos")
            
            cursor.close()
            return success
            
        except Exception as e:
            print(f"ERROR en validación: {e}")
            return False
    
    def run(self):
        """Ejecutar proceso completo de finalización"""
        print("COMPLETANDO ACTUALIZACIÓN DE LADAS FALTANTES")
        print("=" * 60)
        print("Objetivo: Actualizar 12.2M contactos restantes")
        print("Clasificación:")
        print("  55x -> CDMX, CDMX")
        print("  81x -> NUEVO LEON, MONTERREY")
        print("  33x -> JALISCO, GUADALAJARA")
        print("=" * 60)
        
        start_time = time.time()
        
        conn = self.connect_db()
        
        try:
            # Paso 1: Agregar LADAs faltantes
            if not self.add_missing_ladas_to_reference(conn):
                print("FALLO: No se pudieron agregar LADAs faltantes")
                return False
            
            # Paso 2: Contar contactos a actualizar
            total_to_update = self.count_contacts_to_update(conn)
            if total_to_update == 0:
                print("ADVERTENCIA: No hay contactos para actualizar")
                return True
            
            # Paso 3: Ejecutar actualización final
            result = self.execute_final_update(conn)
            if not result:
                print("FALLO: Actualización final falló")
                return False
            
            # Paso 4: Validar resultados finales
            success = self.validate_final_results(conn)
            
            total_time = time.time() - start_time
            
            print("\n" + "=" * 60)
            print("ACTUALIZACIÓN COMPLETA FINALIZADA")
            print(f"Registros actualizados en esta fase: {result['total_updated']:,}")
            print(f"Tiempo total: {total_time:.2f} segundos ({total_time/60:.1f} minutos)")
            if result['total_updated'] > 0:
                print(f"Velocidad promedio: {result['total_updated']/total_time:.0f} registros/segundo")
            
            if success:
                print("✅ MISIÓN COMPLETADA: Todos los contactos tienen estado y municipio!")
            else:
                print("⚠️  REVISAR: Algunos contactos aún necesitan atención")
                
            print("=" * 60)
            
            return success
            
        except Exception as e:
            print(f"ERROR en proceso: {e}")
            return False
            
        finally:
            conn.close()

def main():
    """Función principal"""
    updater = CompleteLadasUpdater()
    
    print("ADVERTENCIA: Este proceso completará la actualización de LADAs")
    print("Se actualizarán ~12.2M contactos restantes")
    
    response = input("\n¿Continuar con la actualización final? (y/N): ").lower().strip()
    
    if response != 'y':
        print("Proceso cancelado")
        sys.exit(0)
    
    if updater.run():
        print("\n🎉 PROCESO COMPLETADO EXITOSAMENTE!")
        print("Todos los contactos ahora tienen estado y municipio asignado")
    else:
        print("\n❌ PROCESO COMPLETADO CON ADVERTENCIAS")
        print("Revisar resultados y contactos restantes")

if __name__ == "__main__":
    main()
