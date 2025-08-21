#!/usr/bin/env python3
"""
CARGADOR OPTIMIZADO DE LADAS DE REFERENCIA
==========================================
Carga el archivo LADAS2025.CSV a PostgreSQL de manera ultra-eficiente
usando COPY FROM para máximo rendimiento.

Rendimiento estimado: 397 registros en <1 segundo
"""

import os
import sys
import time
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from pathlib import Path

class LadasReferenceLoader:
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
            print(f"❌ Error conectando a BD: {e}")
            sys.exit(1)
    
    def validate_csv(self):
        """Validar que el CSV existe y tiene el formato correcto"""
        if not self.csv_path.exists():
            print(f"❌ Archivo no encontrado: {self.csv_path}")
            return False
            
        try:
            df = pd.read_csv(self.csv_path)
            print(f"📊 CSV cargado: {len(df)} registros")
            print(f"📋 Columnas: {list(df.columns)}")
            
            # Validar columnas requeridas
            required_cols = ['LADA', 'ESTADO', 'MUNICIPIO']
            if not all(col in df.columns for col in required_cols):
                print(f"❌ Columnas faltantes. Requeridas: {required_cols}")
                return False
                
            # Mostrar muestra de datos
            print("\n📋 MUESTRA DE DATOS:")
            print(df.head(10).to_string(index=False))
            
            # Estadísticas
            print(f"\n📈 ESTADÍSTICAS:")
            print(f"   • Total LADAs: {len(df)}")
            print(f"   • Estados únicos: {df['ESTADO'].nunique()}")
            print(f"   • Municipios únicos: {df['MUNICIPIO'].nunique()}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error validando CSV: {e}")
            return False
    
    def create_reference_table(self, conn):
        """Crear tabla de referencia ladas_reference"""
        try:
            cursor = conn.cursor()
            
            print("🔧 Creando tabla ladas_reference...")
            
            # Ejecutar el SQL de creación
            with open('scripts/ladas_mass_update_strategy.sql', 'r', encoding='utf-8') as f:
                sql_content = f.read()
                
            # Extraer solo la parte de creación de tabla
            create_table_sql = """
            DROP TABLE IF EXISTS ladas_reference CASCADE;

            CREATE TABLE ladas_reference (
                lada VARCHAR(3) PRIMARY KEY,
                estado VARCHAR(50) NOT NULL,
                municipio VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX idx_ladas_reference_lada ON ladas_reference(lada);
            """
            
            cursor.execute(create_table_sql)
            conn.commit()
            
            print("✅ Tabla ladas_reference creada exitosamente")
            cursor.close()
            
        except Exception as e:
            print(f"❌ Error creando tabla: {e}")
            conn.rollback()
            raise
    
    def load_csv_data(self, conn):
        """Cargar datos del CSV usando COPY FROM (ultra-rápido)"""
        try:
            cursor = conn.cursor()
            
            print("📥 Cargando datos desde CSV...")
            start_time = time.time()
            
            # Usar COPY FROM para máximo rendimiento
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                # Saltar header
                next(f)
                cursor.copy_expert(
                    "COPY ladas_reference(lada, estado, municipio) FROM STDIN WITH CSV",
                    f
                )
            
            conn.commit()
            
            # Obtener estadísticas
            cursor.execute("SELECT COUNT(*) FROM ladas_reference")
            total_loaded = cursor.fetchone()[0]
            
            load_time = time.time() - start_time
            
            print(f"✅ Datos cargados exitosamente:")
            print(f"   • Registros cargados: {total_loaded:,}")
            print(f"   • Tiempo de carga: {load_time:.2f} segundos")
            print(f"   • Velocidad: {total_loaded/load_time:.0f} registros/segundo")
            
            cursor.close()
            return total_loaded
            
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            conn.rollback()
            raise
    
    def validate_loaded_data(self, conn):
        """Validar que los datos se cargaron correctamente"""
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            print("\n🔍 VALIDANDO DATOS CARGADOS:")
            
            # Estadísticas generales
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_ladas,
                    COUNT(DISTINCT estado) as total_estados,
                    COUNT(DISTINCT municipio) as total_municipios
                FROM ladas_reference
            """)
            stats = cursor.fetchone()
            
            print(f"   • Total LADAs: {stats['total_ladas']:,}")
            print(f"   • Estados únicos: {stats['total_estados']}")
            print(f"   • Municipios únicos: {stats['total_municipios']}")
            
            # Muestra de datos
            cursor.execute("""
                SELECT lada, estado, municipio 
                FROM ladas_reference 
                ORDER BY lada 
                LIMIT 10
            """)
            sample_data = cursor.fetchall()
            
            print("\n📋 MUESTRA DE DATOS CARGADOS:")
            for row in sample_data:
                print(f"   LADA {row['lada']}: {row['estado']} - {row['municipio']}")
            
            # Verificar LADAs específicas importantes
            cursor.execute("""
                SELECT lada, estado, municipio 
                FROM ladas_reference 
                WHERE lada IN ('667', '669', '687', '694', '555', '999')
                ORDER BY lada
            """)
            important_ladas = cursor.fetchall()
            
            if important_ladas:
                print("\n🎯 LADAS IMPORTANTES VERIFICADAS:")
                for row in important_ladas:
                    print(f"   LADA {row['lada']}: {row['estado']} - {row['municipio']}")
            
            cursor.close()
            return True
            
        except Exception as e:
            print(f"❌ Error validando datos: {e}")
            return False
    
    def run(self):
        """Ejecutar el proceso completo de carga"""
        print("🚀 INICIANDO CARGA DE LADAS DE REFERENCIA")
        print("=" * 50)
        
        # Validar CSV
        if not self.validate_csv():
            return False
        
        # Conectar a BD
        conn = self.connect_db()
        
        try:
            # Crear tabla
            self.create_reference_table(conn)
            
            # Cargar datos
            total_loaded = self.load_csv_data(conn)
            
            # Validar datos cargados
            self.validate_loaded_data(conn)
            
            print("\n" + "=" * 50)
            print(f"✅ CARGA COMPLETADA EXITOSAMENTE")
            print(f"📊 Total registros: {total_loaded:,}")
            print("🎯 Listo para actualización masiva de contactos")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en proceso de carga: {e}")
            return False
            
        finally:
            conn.close()

def main():
    """Función principal"""
    loader = LadasReferenceLoader()
    
    if loader.run():
        print("\n🎉 ¡Proceso completado exitosamente!")
        print("💡 Siguiente paso: Ejecutar actualización masiva con update_contacts_by_lada()")
        sys.exit(0)
    else:
        print("\n❌ Proceso falló")
        sys.exit(1)

if __name__ == "__main__":
    main()
