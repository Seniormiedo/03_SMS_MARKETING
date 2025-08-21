#!/usr/bin/env python3
"""
Script simplificado para integrar datos oficiales del IFT
Versión sin emojis para evitar problemas de encoding
"""

import pandas as pd
import psycopg2
from pathlib import Path
import logging
from datetime import datetime
import time

# Configurar logging simple
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ift_integration.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IFTIntegrator:
    """Integrador de datos oficiales del IFT"""
    
    def __init__(self):
        self.conn = None
        self.df_ift = None
        
    def connect_db(self):
        """Conectar a PostgreSQL"""
        try:
            self.conn = psycopg2.connect(
                host='127.0.0.1',
                port=15432,
                database='sms_marketing',
                user='sms_user',
                password='sms_password'
            )
            self.conn.autocommit = False
            logger.info("Conexion a BD establecida")
            return True
        except Exception as e:
            logger.error(f"Error conectando a BD: {e}")
            return False
    
    def load_ift_data(self):
        """Cargar y limpiar datos del IFT"""
        try:
            logger.info("Cargando archivo Proveedores_05_08_2025.csv...")
            
            # Cargar CSV
            csv_path = Path("data/Proveedores_05_08_2025.csv")
            df = pd.read_csv(csv_path, encoding='utf-8')
            
            logger.info(f"Archivo cargado: {len(df):,} registros")
            
            # Mapear columnas correctamente (están mal etiquetadas)
            df_clean = pd.DataFrame({
                'numero_inicial': df['ZONA'],
                'numero_final': df[' NUMERACION_INICIAL'], 
                'cantidad_numeros': df[' NUMERACION_FINAL'],
                'tipo_servicio': df[' OCUPACION'].str.strip(),
                'operador': df[' MODALIDAD'].str.strip(),
                'fecha_asignacion': df[' RAZON_SOCIAL'].str.strip()
            })
            
            # Limpiar fechas
            df_clean['fecha_asignacion'] = pd.to_datetime(
                df_clean['fecha_asignacion'], 
                format='%d/%m/%Y', 
                errors='coerce'
            )
            
            # Validaciones
            initial_count = len(df_clean)
            
            # Filtrar registros válidos
            df_clean = df_clean[
                (df_clean['numero_inicial'].notna()) &
                (df_clean['numero_final'].notna()) &
                (df_clean['numero_inicial'] < df_clean['numero_final']) &
                (df_clean['tipo_servicio'].isin(['MPP', 'CPP', 'FPP']))
            ]
            
            final_count = len(df_clean)
            removed = initial_count - final_count
            
            logger.info(f"Limpieza completada:")
            logger.info(f"  - Registros validos: {final_count:,}")
            logger.info(f"  - Registros removidos: {removed:,}")
            
            # Estadísticas
            logger.info(f"Distribucion por tipo de servicio:")
            type_counts = df_clean['tipo_servicio'].value_counts()
            for tipo, count in type_counts.items():
                percentage = (count / final_count) * 100
                logger.info(f"  - {tipo}: {count:,} ({percentage:.1f}%)")
            
            logger.info(f"Top 5 operadores:")
            top_operators = df_clean['operador'].value_counts().head(5)
            for op, count in top_operators.items():
                percentage = (count / final_count) * 100
                logger.info(f"  - {op}: {count:,} ({percentage:.1f}%)")
            
            self.df_ift = df_clean
            return True
            
        except Exception as e:
            logger.error(f"Error cargando datos IFT: {e}")
            return False
    
    def create_ift_table(self):
        """Crear tabla para rangos IFT"""
        try:
            logger.info("Creando tabla ift_rangos...")
            
            cursor = self.conn.cursor()
            
            # Crear tabla
            cursor.execute("""
            DROP TABLE IF EXISTS ift_rangos CASCADE;
            
            CREATE TABLE ift_rangos (
                id SERIAL PRIMARY KEY,
                numero_inicial BIGINT NOT NULL,
                numero_final BIGINT NOT NULL,
                cantidad_numeros INTEGER NOT NULL,
                tipo_servicio VARCHAR(10) NOT NULL,
                operador TEXT NOT NULL,
                fecha_asignacion DATE,
                created_at TIMESTAMP DEFAULT NOW(),
                
                CONSTRAINT ck_rango_valido CHECK (numero_final >= numero_inicial),
                CONSTRAINT ck_tipo_servicio CHECK (tipo_servicio IN ('MPP', 'CPP', 'FPP'))
            );
            """)
            
            # Crear índices optimizados
            cursor.execute("""
            -- Índice para búsquedas de rangos
            CREATE INDEX idx_ift_rangos_inicial ON ift_rangos (numero_inicial);
            CREATE INDEX idx_ift_rangos_final ON ift_rangos (numero_final);
            CREATE INDEX idx_ift_rangos_rango ON ift_rangos (numero_inicial, numero_final);
            
            -- Índices para filtros
            CREATE INDEX idx_ift_rangos_tipo ON ift_rangos (tipo_servicio);
            CREATE INDEX idx_ift_rangos_operador ON ift_rangos (operador);
            """)
            
            self.conn.commit()
            logger.info("Tabla ift_rangos creada con indices")
            return True
            
        except Exception as e:
            logger.error(f"Error creando tabla: {e}")
            self.conn.rollback()
            return False
    
    def load_ift_to_db(self):
        """Cargar datos IFT a la base de datos"""
        try:
            logger.info("Cargando datos IFT a la base de datos...")
            
            cursor = self.conn.cursor()
            
            # Preparar datos para inserción
            records = []
            for _, row in self.df_ift.iterrows():
                records.append((
                    int(row['numero_inicial']),
                    int(row['numero_final']),
                    int(row['cantidad_numeros']),
                    row['tipo_servicio'],
                    row['operador'],
                    row['fecha_asignacion'] if pd.notna(row['fecha_asignacion']) else None
                ))
            
            # Inserción por lotes
            batch_size = 1000
            total_batches = (len(records) + batch_size - 1) // batch_size
            
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                current_batch = (i // batch_size) + 1
                
                cursor.executemany("""
                INSERT INTO ift_rangos 
                (numero_inicial, numero_final, cantidad_numeros, tipo_servicio, operador, fecha_asignacion)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, batch)
                
                if current_batch % 10 == 0:
                    logger.info(f"  Lote {current_batch}/{total_batches} procesado")
            
            self.conn.commit()
            
            # Verificar carga
            cursor.execute("SELECT COUNT(*) FROM ift_rangos")
            count = cursor.fetchone()[0]
            
            logger.info(f"Datos IFT cargados: {count:,} rangos")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando datos: {e}")
            self.conn.rollback()
            return False
    
    def create_verification_function(self):
        """Crear función de verificación de números"""
        try:
            logger.info("Creando funcion de verificacion...")
            
            cursor = self.conn.cursor()
            
            cursor.execute("""
            CREATE OR REPLACE FUNCTION verificar_numero_ift(numero_telefono BIGINT)
            RETURNS TABLE(
                es_movil BOOLEAN,
                operador TEXT,
                tipo_servicio VARCHAR(10),
                fecha_asignacion DATE,
                encontrado BOOLEAN
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    CASE WHEN r.tipo_servicio = 'MPP' THEN TRUE ELSE FALSE END as es_movil,
                    r.operador,
                    r.tipo_servicio,
                    r.fecha_asignacion,
                    TRUE as encontrado
                FROM ift_rangos r
                WHERE numero_telefono >= r.numero_inicial 
                  AND numero_telefono <= r.numero_final
                LIMIT 1;
                
                -- Si no se encuentra, devolver valores por defecto
                IF NOT FOUND THEN
                    RETURN QUERY SELECT FALSE, 'DESCONOCIDO'::TEXT, 'UNKNOWN'::VARCHAR(10), NULL::DATE, FALSE;
                END IF;
            END;
            $$ LANGUAGE plpgsql;
            """)
            
            self.conn.commit()
            logger.info("Funcion de verificacion creada")
            
            # Test de la función
            cursor.execute("SELECT * FROM verificar_numero_ift(5551234567)")
            result = cursor.fetchone()
            logger.info(f"Test funcion: {result}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creando funcion: {e}")
            self.conn.rollback()
            return False
    
    def run_sample_validation(self, sample_size=10000):
        """Ejecutar validación en muestra"""
        try:
            logger.info(f"Ejecutando validacion en muestra de {sample_size:,} registros...")
            
            cursor = self.conn.cursor()
            
            # Crear tabla temporal con muestra
            cursor.execute(f"""
            CREATE TEMP TABLE temp_sample AS
            SELECT id, phone_national, status, operator
            FROM contacts 
            WHERE phone_national IS NOT NULL 
              AND phone_national ~ '^[0-9]+$'
            ORDER BY RANDOM()
            LIMIT {sample_size};
            """)
            
            # Ejecutar validación
            cursor.execute("""
            CREATE TEMP TABLE temp_validation_results AS
            SELECT 
                ts.id,
                ts.phone_national,
                ts.status as status_actual,
                ts.operator as operador_actual,
                ift.es_movil,
                ift.operador as operador_ift,
                ift.tipo_servicio,
                ift.encontrado,
                CASE 
                    WHEN ift.es_movil = TRUE THEN 'VERIFIED'
                    WHEN ift.es_movil = FALSE THEN 'NOT_MOBILE'
                    ELSE 'UNKNOWN'
                END as nuevo_status
            FROM temp_sample ts
            CROSS JOIN LATERAL verificar_numero_ift(ts.phone_national::BIGINT) ift;
            """)
            
            # Analizar resultados
            cursor.execute("""
            SELECT 
                status_actual,
                nuevo_status,
                COUNT(*) as cantidad,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje
            FROM temp_validation_results
            GROUP BY status_actual, nuevo_status
            ORDER BY cantidad DESC;
            """)
            
            results = cursor.fetchall()
            
            logger.info("Resultados de validacion en muestra:")
            logger.info("Status Actual -> Nuevo Status | Cantidad | %")
            logger.info("-" * 50)
            
            total_changes = 0
            for row in results:
                status_actual, nuevo_status, cantidad, porcentaje = row
                logger.info(f"{status_actual} -> {nuevo_status} | {cantidad:,} | {porcentaje}%")
                
                if status_actual != nuevo_status:
                    total_changes += cantidad
            
            logger.info(f"")
            logger.info(f"Resumen de muestra:")
            logger.info(f"  - Total validado: {sample_size:,}")
            logger.info(f"  - Cambios necesarios: {total_changes:,}")
            logger.info(f"  - % de cambios: {(total_changes/sample_size)*100:.1f}%")
            
            # Estadísticas de operadores
            cursor.execute("""
            SELECT 
                operador_ift,
                COUNT(*) as cantidad
            FROM temp_validation_results
            WHERE encontrado = TRUE
            GROUP BY operador_ift
            ORDER BY cantidad DESC
            LIMIT 10;
            """)
            
            operators = cursor.fetchall()
            logger.info(f"")
            logger.info(f"Top operadores identificados:")
            for op, count in operators:
                logger.info(f"  - {op}: {count:,}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error en validacion de muestra: {e}")
            return False
    
    def run_integration(self):
        """Ejecutar integración de muestra"""
        logger.info("INICIANDO INTEGRACION IFT - MUESTRA")
        logger.info("="*60)
        
        steps = [
            ("Conectar a BD", self.connect_db),
            ("Cargar datos IFT", self.load_ift_data),
            ("Crear tabla IFT", self.create_ift_table),
            ("Cargar IFT a BD", self.load_ift_to_db),
            ("Crear funcion verificacion", self.create_verification_function),
            ("Validacion muestra", lambda: self.run_sample_validation(10000)),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"")
            logger.info(f"Ejecutando: {step_name}...")
            if not step_func():
                logger.error(f"Fallo: {step_name}")
                return False
            logger.info(f"Completado: {step_name}")
        
        logger.info("")
        logger.info("INTEGRACION IFT COMPLETADA CON EXITO")
        return True

def main():
    """Función principal"""
    integrator = IFTIntegrator()
    
    print("INTEGRADOR DE DATOS IFT")
    print("="*50)
    print("Este script cargara los datos oficiales del IFT")
    print("y ejecutara una validacion de muestra.")
    print()
    
    success = integrator.run_integration()
    
    if success:
        print("")
        print("Integracion completada exitosamente!")
        print("Revisa el archivo 'ift_integration.log' para detalles completos")
    else:
        print("")
        print("La integracion fallo. Revisa los logs para mas detalles.")

if __name__ == "__main__":
    main()