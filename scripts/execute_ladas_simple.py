#!/usr/bin/env python3
"""
EJECUTOR SIMPLE DE ACTUALIZACIÓN MASIVA POR LADAS
=================================================
Version simplificada sin emojis para compatibilidad con Windows
"""

import os
import sys
import time
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from pathlib import Path

class SimpleladasUpdater:
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
            
            # Leer CSV y cargar datos
            print("Cargando datos desde CSV...")
            df = pd.read_csv(self.csv_path)
            
            # Insertar datos
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO ladas_reference (lada, estado, municipio) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT (lada) DO UPDATE SET
                        estado = EXCLUDED.estado,
                        municipio = EXCLUDED.municipio
                """, (str(row['LADA']), row['ESTADO'], row['MUNICIPIO']))
            
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
    
    def create_update_function(self, conn):
        """Crear función de actualización"""
        print("\nPASO 2: CREANDO FUNCIÓN DE ACTUALIZACIÓN")
        print("-" * 40)
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE OR REPLACE FUNCTION update_contacts_by_lada_simple()
                RETURNS TABLE(
                    total_updated BIGINT,
                    execution_time_seconds NUMERIC,
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
                    exec_seconds NUMERIC;
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
                    exec_seconds := EXTRACT(EPOCH FROM (end_time - start_time));
                    
                    RETURN QUERY SELECT 
                        updated_count,
                        exec_seconds,
                        matched_ladas,
                        missing_ladas;
                END;
                $$;
            """)
            
            conn.commit()
            cursor.close()
            
            print("OK - Función de actualización creada")
            return True
            
        except Exception as e:
            print(f"ERROR creando función: {e}")
            conn.rollback()
            return False
    
    def optimize_postgres(self, conn):
        """Optimizar PostgreSQL para UPDATE masivo"""
        print("\nPASO 3: OPTIMIZANDO POSTGRESQL")
        print("-" * 40)
        
        try:
            cursor = conn.cursor()
            
            optimizations = [
                "SET work_mem = '512MB';",
                "SET maintenance_work_mem = '1GB';",
                "SET synchronous_commit = OFF;",
                "SET checkpoint_completion_target = 0.9;"
            ]
            
            for opt in optimizations:
                try:
                    cursor.execute(opt)
                    print(f"OK - {opt}")
                except Exception as e:
                    print(f"WARN - {opt}: {e}")
            
            cursor.close()
            return True
            
        except Exception as e:
            print(f"ERROR optimizando: {e}")
            return False
    
    def execute_mass_update(self, conn):
        """Ejecutar actualización masiva"""
        print("\nPASO 4: EJECUTANDO ACTUALIZACIÓN MASIVA")
        print("-" * 40)
        print("ADVERTENCIA: Esto puede tomar 10-30 minutos...")
        print("Procesando 31.8M registros...")
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            start_time = time.time()
            cursor.execute("SELECT * FROM update_contacts_by_lada_simple();")
            result = cursor.fetchone()
            total_time = time.time() - start_time
            
            print(f"\nRESULTADOS:")
            print(f"  Registros actualizados: {result['total_updated']:,}")
            print(f"  Tiempo PostgreSQL: {result['execution_time_seconds']:.2f} segundos")
            print(f"  Tiempo total: {total_time:.2f} segundos ({total_time/60:.1f} minutos)")
            print(f"  LADAs coincidentes: {result['ladas_matched']}")
            print(f"  LADAs no encontradas: {result['ladas_not_found']}")
            
            if result['total_updated'] > 0:
                speed = result['total_updated'] / result['execution_time_seconds']
                print(f"  Velocidad: {speed:.0f} registros/segundo")
            
            cursor.close()
            return result
            
        except Exception as e:
            print(f"ERROR en actualización: {e}")
            return None
    
    def validate_results(self, conn):
        """Validar algunos resultados"""
        print("\nPASO 5: VALIDANDO RESULTADOS")
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
                WHERE c.lada IN ('667', '669', '687', '694', '555', '999')
                GROUP BY c.lada, c.state_name, c.municipality
                ORDER BY c.lada, COUNT(*) DESC
                LIMIT 20
            """)
            
            results = cursor.fetchall()
            
            print("MUESTRA DE RESULTADOS:")
            print(f"{'LADA':<5} {'ESTADO':<15} {'MUNICIPIO':<15} {'CONTACTOS':<10}")
            print("-" * 55)
            
            for row in results:
                print(f"{row['lada']:<5} {row['state_name'][:14]:<15} {row['municipality'][:14]:<15} {row['total_contacts']:,<10}")
            
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
            
            # Paso 2: Crear función
            if not self.create_update_function(conn):
                print("FALLO: No se pudo crear función de actualización")
                return False
            
            # Paso 3: Optimizar
            self.optimize_postgres(conn)
            
            # Paso 4: Ejecutar actualización
            result = self.execute_mass_update(conn)
            if not result:
                print("FALLO: Actualización masiva falló")
                return False
            
            # Paso 5: Validar
            self.validate_results(conn)
            
            total_time = time.time() - start_time
            
            print("\n" + "=" * 50)
            print("ACTUALIZACIÓN COMPLETADA EXITOSAMENTE")
            print(f"Registros actualizados: {result['total_updated']:,}")
            print(f"Tiempo total: {total_time:.2f} segundos ({total_time/60:.1f} minutos)")
            print("=" * 50)
            
            return True
            
        except Exception as e:
            print(f"ERROR en proceso: {e}")
            return False
            
        finally:
            conn.close()

def main():
    """Función principal"""
    updater = SimpleladasUpdater()
    
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
