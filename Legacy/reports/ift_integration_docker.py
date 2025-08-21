#!/usr/bin/env python3
"""
Integración IFT usando comandos Docker directos
Para evitar problemas de conexión Python-PostgreSQL
"""

import pandas as pd
import subprocess
import json
from pathlib import Path
import logging
from datetime import datetime
import time
import tempfile
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ift_integration.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IFTIntegratorDocker:
    """Integrador IFT usando Docker"""
    
    def __init__(self):
        self.df_ift = None
        
    def execute_sql(self, sql_command, description="SQL command"):
        """Ejecutar comando SQL via Docker"""
        try:
            cmd = [
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', sql_command
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                logger.info(f"✅ {description} ejecutado exitosamente")
                return result.stdout
            else:
                logger.error(f"❌ Error en {description}: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando {description}: {e}")
            return None
    
    def execute_sql_file(self, sql_file_path, description="SQL file"):
        """Ejecutar archivo SQL via Docker"""
        try:
            cmd = [
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-f', f'/tmp/{sql_file_path.name}'
            ]
            
            # Copiar archivo al contenedor
            copy_cmd = [
                'docker', 'cp', str(sql_file_path),
                f'sms_postgres:/tmp/{sql_file_path.name}'
            ]
            
            copy_result = subprocess.run(copy_cmd, capture_output=True, text=True)
            if copy_result.returncode != 0:
                logger.error(f"❌ Error copiando archivo: {copy_result.stderr}")
                return None
            
            # Ejecutar archivo
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ {description} ejecutado exitosamente")
                return result.stdout
            else:
                logger.error(f"❌ Error en {description}: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando {description}: {e}")
            return None
    
    def test_connection(self):
        """Test de conexión"""
        logger.info("🔍 Testing database connection...")
        
        result = self.execute_sql(
            "SELECT 'Connection OK' as status, COUNT(*) as contacts FROM contacts;",
            "Test de conexión"
        )
        
        if result:
            logger.info("✅ Conexión a BD establecida")
            logger.info(f"📊 Resultado: {result.strip()}")
            return True
        else:
            logger.error("❌ Fallo conexión a BD")
            return False
    
    def load_ift_data(self):
        """Cargar y limpiar datos del IFT"""
        try:
            logger.info("📂 Cargando archivo Proveedores_05_08_2025.csv...")
            
            csv_path = Path("data/Proveedores_05_08_2025.csv")
            df = pd.read_csv(csv_path, encoding='utf-8')
            
            logger.info(f"📋 Archivo cargado: {len(df):,} registros")
            
            # Mapear columnas correctamente
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
            
            df_clean = df_clean[
                (df_clean['numero_inicial'].notna()) &
                (df_clean['numero_final'].notna()) &
                (df_clean['numero_inicial'] < df_clean['numero_final']) &
                (df_clean['tipo_servicio'].isin(['MPP', 'CPP', 'FPP']))
            ]
            
            final_count = len(df_clean)
            removed = initial_count - final_count
            
            logger.info(f"🧹 Limpieza completada:")
            logger.info(f"   - Registros válidos: {final_count:,}")
            logger.info(f"   - Registros removidos: {removed:,}")
            
            # Estadísticas
            type_counts = df_clean['tipo_servicio'].value_counts()
            logger.info(f"📊 Distribución por tipo:")
            for tipo, count in type_counts.items():
                percentage = (count / final_count) * 100
                logger.info(f"   - {tipo}: {count:,} ({percentage:.1f}%)")
            
            self.df_ift = df_clean
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cargando datos IFT: {e}")
            return False
    
    def create_ift_table(self):
        """Crear tabla para rangos IFT"""
        logger.info("🏗️ Creando tabla ift_rangos...")
        
        sql = """
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
        
        -- Índices optimizados
        CREATE INDEX idx_ift_rangos_inicial ON ift_rangos (numero_inicial);
        CREATE INDEX idx_ift_rangos_final ON ift_rangos (numero_final);
        CREATE INDEX idx_ift_rangos_rango ON ift_rangos (numero_inicial, numero_final);
        CREATE INDEX idx_ift_rangos_tipo ON ift_rangos (tipo_servicio);
        CREATE INDEX idx_ift_rangos_operador ON ift_rangos (operador);
        """
        
        result = self.execute_sql(sql, "Creación tabla ift_rangos")
        return result is not None
    
    def load_ift_to_db(self):
        """Cargar datos IFT usando COPY"""
        try:
            logger.info("📥 Preparando datos para carga masiva...")
            
            # Crear archivo CSV temporal para COPY
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
                temp_file = f.name
                
                # Escribir header
                f.write("numero_inicial,numero_final,cantidad_numeros,tipo_servicio,operador,fecha_asignacion\n")
                
                # Escribir datos
                for _, row in self.df_ift.iterrows():
                    fecha = row['fecha_asignacion'].strftime('%Y-%m-%d') if pd.notna(row['fecha_asignacion']) else '\\N'
                    operador_clean = str(row['operador']).replace(',', ';').replace('\n', ' ')
                    
                    f.write(f"{int(row['numero_inicial'])},{int(row['numero_final'])},{int(row['cantidad_numeros'])},{row['tipo_servicio']},{operador_clean},{fecha}\n")
            
            logger.info(f"📄 Archivo temporal creado: {temp_file}")
            
            # Copiar archivo al contenedor
            container_file = '/tmp/ift_data.csv'
            copy_cmd = ['docker', 'cp', temp_file, f'sms_postgres:{container_file}']
            
            copy_result = subprocess.run(copy_cmd, capture_output=True, text=True)
            if copy_result.returncode != 0:
                logger.error(f"❌ Error copiando archivo: {copy_result.stderr}")
                return False
            
            logger.info("📋 Archivo copiado al contenedor")
            
            # Ejecutar COPY
            copy_sql = f"""
            COPY ift_rangos (numero_inicial, numero_final, cantidad_numeros, tipo_servicio, operador, fecha_asignacion)
            FROM '{container_file}'
            WITH (FORMAT csv, HEADER true, NULL '\\N');
            """
            
            result = self.execute_sql(copy_sql, "Carga masiva COPY")
            
            # Limpiar archivo temporal
            os.unlink(temp_file)
            
            if result:
                # Verificar carga
                count_result = self.execute_sql("SELECT COUNT(*) FROM ift_rangos;", "Conteo final")
                if count_result:
                    count = count_result.strip().split('\n')[2].strip()
                    logger.info(f"✅ Datos IFT cargados: {count} rangos")
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"❌ Error en carga masiva: {e}")
            return False
    
    def create_verification_function(self):
        """Crear función de verificación"""
        logger.info("⚙️ Creando función de verificación...")
        
        sql = """
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
            
            IF NOT FOUND THEN
                RETURN QUERY SELECT FALSE, 'DESCONOCIDO'::TEXT, 'UNKNOWN'::VARCHAR(10), NULL::DATE, FALSE;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        result = self.execute_sql(sql, "Función de verificación")
        
        if result:
            # Test de la función
            test_result = self.execute_sql(
                "SELECT * FROM verificar_numero_ift(5551234567);",
                "Test función verificación"
            )
            if test_result:
                logger.info(f"🧪 Test función: {test_result.strip()}")
            return True
        
        return False
    
    def run_sample_validation(self, sample_size=10000):
        """Validación en muestra"""
        logger.info(f"🔍 Ejecutando validación en muestra de {sample_size:,} registros...")
        
        sql = f"""
        -- Crear muestra
        CREATE TEMP TABLE temp_sample AS
        SELECT id, phone_national, status, operator
        FROM contacts 
        WHERE phone_national IS NOT NULL 
          AND phone_national ~ '^[0-9]+$'
        ORDER BY RANDOM()
        LIMIT {sample_size};
        
        -- Ejecutar validación
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
        
        -- Resultados por status
        SELECT 
            status_actual,
            nuevo_status,
            COUNT(*) as cantidad,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje
        FROM temp_validation_results
        GROUP BY status_actual, nuevo_status
        ORDER BY cantidad DESC;
        """
        
        result = self.execute_sql(sql, "Validación de muestra")
        
        if result:
            logger.info("📊 Resultados de validación:")
            logger.info(result)
            
            # Estadísticas de operadores
            op_sql = """
            SELECT 
                operador_ift,
                COUNT(*) as cantidad
            FROM temp_validation_results
            WHERE encontrado = TRUE
            GROUP BY operador_ift
            ORDER BY cantidad DESC
            LIMIT 10;
            """
            
            op_result = self.execute_sql(op_sql, "Top operadores")
            if op_result:
                logger.info("🏢 Top operadores identificados:")
                logger.info(op_result)
            
            return True
        
        return False
    
    def run_integration(self):
        """Ejecutar integración completa"""
        logger.info("🚀 INICIANDO INTEGRACION IFT")
        logger.info("=" * 60)
        
        steps = [
            ("🔍 Test conexión", self.test_connection),
            ("📂 Cargar datos IFT", self.load_ift_data),
            ("🏗️ Crear tabla IFT", self.create_ift_table),
            ("📥 Cargar IFT a BD", self.load_ift_to_db),
            ("⚙️ Crear función verificación", self.create_verification_function),
            ("🔍 Validación muestra", lambda: self.run_sample_validation(10000)),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n{step_name}...")
            start_time = time.time()
            
            if not step_func():
                logger.error(f"❌ Falló: {step_name}")
                return False
            
            elapsed = time.time() - start_time
            logger.info(f"✅ Completado: {step_name} ({elapsed:.1f}s)")
        
        logger.info("\n🎉 INTEGRACION IFT COMPLETADA CON EXITO")
        return True

def main():
    """Función principal"""
    integrator = IFTIntegratorDocker()
    
    print("🚀 INTEGRADOR DE DATOS IFT - VERSION DOCKER")
    print("=" * 60)
    print("Este script integrará los datos oficiales del IFT")
    print("usando comandos Docker directos para máxima compatibilidad.")
    print()
    
    success = integrator.run_integration()
    
    if success:
        print("\n🎊 ¡INTEGRACION COMPLETADA EXITOSAMENTE!")
        print("📋 Revisa 'ift_integration.log' para detalles completos")
        print("🎯 La base de datos ahora tiene datos oficiales del IFT")
    else:
        print("\n❌ La integración falló. Revisa los logs.")

if __name__ == "__main__":
    main()