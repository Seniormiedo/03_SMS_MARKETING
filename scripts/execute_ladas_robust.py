#!/usr/bin/env python3
"""
EJECUTOR ROBUSTO DE ACTUALIZACIÓN MASIVA POR LADAS
==================================================
Version robusta con manejo adecuado de transacciones
"""

import os
import sys
import time
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from pathlib import Path

class RobustLadasUpdater:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': 15432,
            'database': 'sms_marketing',
            'user': 'sms_user', 
            'password': 'sms_password'
        }
        self.csv_path = Path('backups/LADAS2025.CSV')
        
    def connect_db(self):
        """Conectar a PostgreSQL"""
        try:
            conn = psycopg2.connect(**self.db_config)
            conn.autocommit = False
            return conn
        except Exception as e:
            print(f"ERROR conectando a BD: {e}")
            sys.exit(1)
    
    def load_csv_to_reference_table(self, conn):
        """Cargar CSV directamente a tabla de referencia"""
        print("PASO 1: CARGANDO DATOS DE REFERENCIA")
        print("-" * 40)
        
        try:
            cursor = conn.cursor()
            
            # Crear tabla de referencia
            print("Creando tabla ladas_reference...")
            cursor.execute("""
                DROP TABLE IF EXISTS ladas_reference CASCADE;
                
                CREATE TABLE ladas_reference (
                    lada VARCHAR(3) PRIMARY KEY,
                    estado VARCHAR(50) NOT NULL,
                    municipio VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX idx_ladas_reference_lada ON ladas_reference(lada);
            """)
            
            conn.commit()
            
            # Leer CSV y cargar datos
            print("Cargando datos desde CSV...")
            df = pd.read_csv(self.csv_path)
            
            # Insertar datos en lotes
            insert_data = []
            for _, row in df.iterrows():
                insert_data.append((str(row['LADA']), row['ESTADO'], row['MUNICIPIO']))
            
            cursor.executemany("""
                INSERT INTO ladas_reference (lada, estado, municipio) 
                VALUES (%s, %s, %s)
                ON CONFLICT (lada) DO UPDATE SET
                    estado = EXCLUDED.estado,
                    municipio = EXCLUDED.municipio
            """, insert_data)
            
            conn.commit()
            
            # Verificar carga
            cursor.execute("SELECT COUNT(*) FROM ladas_reference")
            total_loaded = cursor.fetchone()[0]
            
            print(f"OK - Datos cargados: {total_loaded} LADAs")
            cursor.close()
            
            return total_loaded > 0
            
        except Exception as e:
            print(f"ERROR cargando datos: {e}")
            conn.rollback()
            return False
    
    def execute_direct_update(self, conn):
        """Ejecutar actualización directa sin función"""
        print("\nPASO 2: EJECUTANDO ACTUALIZACIÓN MASIVA DIRECTA")
        print("-" * 40)
        print("ADVERTENCIA: Esto puede tomar 10-30 minutos...")
        print("Procesando 31.8M registros...")
        
        try:
            cursor = conn.cursor()
            
            # Primero, obtener estadísticas
            print("Analizando datos...")
            cursor.execute("""
                SELECT COUNT(DISTINCT c.lada) as ladas_en_contacts
                FROM contacts c 
                WHERE c.lada IS NOT NULL
            """)
            ladas_contacts = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(DISTINCT c.lada) as ladas_coincidentes
                FROM contacts c 
                INNER JOIN ladas_reference lr ON c.lada = lr.lada
                WHERE c.lada IS NOT NULL
            """)
            ladas_matched = cursor.fetchone()[0]
            
            print(f"LADAs en contacts: {ladas_contacts}")
            print(f"LADAs que coinciden: {ladas_matched}")
            
            # Ejecutar actualización masiva
            print("Ejecutando UPDATE masivo...")
            start_time = time.time()
            
            cursor.execute("""
                UPDATE contacts 
                SET 
                    state_name = UPPER(TRIM(lr.estado)),
                    municipality = UPPER(TRIM(lr.municipio)),
                    updated_at = CURRENT_TIMESTAMP
                FROM ladas_reference lr 
                WHERE contacts.lada = lr.lada 
                  AND contacts.lada IS NOT NULL
            """)
            
            updated_count = cursor.rowcount
            execution_time = time.time() - start_time
            
            conn.commit()
            
            print(f"\nRESULTADOS:")
            print(f"  Registros actualizados: {updated_count:,}")
            print(f"  Tiempo de ejecución: {execution_time:.2f} segundos ({execution_time/60:.1f} minutos)")
            print(f"  LADAs coincidentes: {ladas_matched}")
            
            if updated_count > 0:
                speed = updated_count / execution_time
                print(f"  Velocidad: {speed:.0f} registros/segundo")
            
            cursor.close()
            
            return {
                'total_updated': updated_count,
                'execution_time': execution_time,
                'ladas_matched': ladas_matched
            }
            
        except Exception as e:
            print(f"ERROR en actualización: {e}")
            conn.rollback()
            return None
    
    def validate_results(self, conn):
        """Validar algunos resultados"""
        print("\nPASO 3: VALIDANDO RESULTADOS")
        print("-" * 40)
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Validar LADAs específicas
            cursor.execute("""
                SELECT 
                    c.lada,
                    c.state_name,
                    c.municipality,
                    COUNT(*) as total_contacts
                FROM contacts c
                WHERE c.lada IN ('667', '669', '687', '694', '555', '999', '311', '322')
                GROUP BY c.lada, c.state_name, c.municipality
                ORDER BY c.lada, COUNT(*) DESC
                LIMIT 20
            """)
            
            results = cursor.fetchall()
            
            print("MUESTRA DE RESULTADOS:")
            print(f"{'LADA':<5} {'ESTADO':<15} {'MUNICIPIO':<15} {'CONTACTOS':<10}")
            print("-" * 55)
            
            for row in results:
                estado = row['state_name'] or 'NULL'
                municipio = row['municipality'] or 'NULL'
                print(f"{row['lada']:<5} {estado[:14]:<15} {municipio[:14]:<15} {row['total_contacts']:,<10}")
            
            # Estadísticas generales
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_contacts,
                    COUNT(CASE WHEN state_name IS NOT NULL THEN 1 END) as with_state,
                    COUNT(CASE WHEN municipality IS NOT NULL THEN 1 END) as with_municipality,
                    COUNT(DISTINCT state_name) as unique_states
                FROM contacts 
                WHERE lada IS NOT NULL
            """)
            
            stats = cursor.fetchone()
            
            print(f"\nESTADISTICAS FINALES:")
            print(f"  Total contactos: {stats['total_contacts']:,}")
            print(f"  Con estado: {stats['with_state']:,} ({stats['with_state']/stats['total_contacts']*100:.1f}%)")
            print(f"  Con municipio: {stats['with_municipality']:,} ({stats['with_municipality']/stats['total_contacts']*100:.1f}%)")
            print(f"  Estados únicos: {stats['unique_states']}")
            
            # Verificar algunas LADAs específicas
            cursor.execute("""
                SELECT 
                    lr.lada,
                    lr.estado as csv_estado,
                    lr.municipio as csv_municipio,
                    c.state_name as bd_estado,
                    c.municipality as bd_municipio,
                    COUNT(*) as contactos
                FROM ladas_reference lr
                LEFT JOIN contacts c ON lr.lada = c.lada
                WHERE lr.lada IN ('667', '669', '687', '694')
                GROUP BY lr.lada, lr.estado, lr.municipio, c.state_name, c.municipality
                ORDER BY lr.lada
            """)
            
            verification = cursor.fetchall()
            
            print(f"\nVERIFICACIÓN SINALOA:")
            for row in verification:
                match = "OK" if row['csv_estado'].upper() == (row['bd_estado'] or '').upper() else "ERROR"
                print(f"  LADA {row['lada']}: {row['csv_estado']} -> {row['bd_estado']} ({row['contactos']:,} contactos) [{match}]")
            
            cursor.close()
            return True
            
        except Exception as e:
            print(f"ERROR validando: {e}")
            return False
    
    def run(self):
        """Ejecutar proceso completo"""
        print("INICIANDO ACTUALIZACIÓN MASIVA POR LADAS")
        print("=" * 50)
        print("Objetivo: Actualizar 31.8M contactos")
        print("Backup disponible: ./backups/backup_sinaloa_fixed_20250808.backup")
        print("=" * 50)
        
        start_time = time.time()
        
        conn = self.connect_db()
        
        try:
            # Paso 1: Cargar datos de referencia
            if not self.load_csv_to_reference_table(conn):
                print("FALLO: No se pudieron cargar datos de referencia")
                return False
            
            # Paso 2: Ejecutar actualización directa
            result = self.execute_direct_update(conn)
            if not result:
                print("FALLO: Actualización masiva falló")
                return False
            
            # Paso 3: Validar
            self.validate_results(conn)
            
            total_time = time.time() - start_time
            
            print("\n" + "=" * 50)
            print("ACTUALIZACIÓN COMPLETADA EXITOSAMENTE")
            print(f"Registros actualizados: {result['total_updated']:,}")
            print(f"Tiempo total: {total_time:.2f} segundos ({total_time/60:.1f} minutos)")
            if result['total_updated'] > 0:
                print(f"Velocidad promedio: {result['total_updated']/total_time:.0f} registros/segundo")
            print("=" * 50)
            
            return True
            
        except Exception as e:
            print(f"ERROR en proceso: {e}")
            return False
            
        finally:
            conn.close()

def main():
    """Función principal"""
    updater = RobustLadasUpdater()
    
    print("ADVERTENCIA: Este proceso modificará 31.8M registros")
    print("Backup disponible: ./backups/backup_sinaloa_fixed_20250808.backup")
    
    response = input("\n¿Continuar con la actualización masiva? (y/N): ").lower().strip()
    
    if response != 'y':
        print("Proceso cancelado")
        sys.exit(0)
    
    if updater.run():
        print("\nPROCESO COMPLETADO EXITOSAMENTE!")
        print("Los contactos ahora tienen estado y municipio basado en LADA")
    else:
        print("\nPROCESO FALLÓ")
        sys.exit(1)

if __name__ == "__main__":
    main()
