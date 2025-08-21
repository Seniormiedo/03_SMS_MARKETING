#!/usr/bin/env python3
"""
Script completo para integrar datos oficiales del IFT y revalidar contactos
"""

import pandas as pd
import psycopg2
from pathlib import Path
import logging
from datetime import datetime
import time

# Configurar logging sin emojis para evitar problemas de encoding
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
            logger.info("✅ Conexión a BD establecida")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando a BD: {e}")
            return False
    
    def load_ift_data(self):
        """Cargar y limpiar datos del IFT"""
        try:
            logger.info("📊 Cargando archivo Proveedores_05_08_2025.csv...")
            
            # Cargar CSV
            csv_path = Path("data/Proveedores_05_08_2025.csv")
            df = pd.read_csv(csv_path, encoding='utf-8')
            
            logger.info(f"📁 Archivo cargado: {len(df):,} registros")
            
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
            
            logger.info(f"🧹 Limpieza completada:")
            logger.info(f"  • Registros válidos: {final_count:,}")
            logger.info(f"  • Registros removidos: {removed:,}")
            
            # Estadísticas
            logger.info(f"📊 Distribución por tipo de servicio:")
            type_counts = df_clean['tipo_servicio'].value_counts()
            for tipo, count in type_counts.items():
                percentage = (count / final_count) * 100
                logger.info(f"  • {tipo}: {count:,} ({percentage:.1f}%)")
            
            logger.info(f"📱 Top 5 operadores:")
            top_operators = df_clean['operador'].value_counts().head(5)
            for op, count in top_operators.items():
                percentage = (count / final_count) * 100
                logger.info(f"  • {op}: {count:,} ({percentage:.1f}%)")
            
            self.df_ift = df_clean
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cargando datos IFT: {e}")
            return False
    
    def create_ift_table(self):
        """Crear tabla para rangos IFT"""
        try:
            logger.info("🏗️ Creando tabla ift_rangos...")
            
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
            -- Índice para búsquedas de rangos (más eficiente)
            CREATE INDEX idx_ift_rangos_inicial ON ift_rangos (numero_inicial);
            CREATE INDEX idx_ift_rangos_final ON ift_rangos (numero_final);
            CREATE INDEX idx_ift_rangos_rango ON ift_rangos (numero_inicial, numero_final);
            
            -- Índices para filtros
            CREATE INDEX idx_ift_rangos_tipo ON ift_rangos (tipo_servicio);
            CREATE INDEX idx_ift_rangos_operador ON ift_rangos (operador);
            """)
            
            self.conn.commit()
            logger.info("✅ Tabla ift_rangos creada con índices")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando tabla: {e}")
            self.conn.rollback()
            return False
    
    def load_ift_to_db(self):
        """Cargar datos IFT a la base de datos"""
        try:
            logger.info("📥 Cargando datos IFT a la base de datos...")
            
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
                    logger.info(f"  📦 Lote {current_batch}/{total_batches} procesado")
            
            self.conn.commit()
            
            # Verificar carga
            cursor.execute("SELECT COUNT(*) FROM ift_rangos")
            count = cursor.fetchone()[0]
            
            logger.info(f"✅ Datos IFT cargados: {count:,} rangos")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cargando datos: {e}")
            self.conn.rollback()
            return False
    
    def create_verification_function(self):
        """Crear función de verificación de números"""
        try:
            logger.info("🔧 Creando función de verificación...")
            
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
            logger.info("✅ Función de verificación creada")
            
            # Test de la función
            cursor.execute("SELECT * FROM verificar_numero_ift(5551234567)")
            result = cursor.fetchone()
            logger.info(f"🧪 Test función: {result}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando función: {e}")
            self.conn.rollback()
            return False
    
    def create_backup(self):
        """Crear backup de la tabla contacts"""
        try:
            logger.info("💾 Creando backup de tabla contacts...")
            
            cursor = self.conn.cursor()
            
            # Crear tabla backup
            cursor.execute("""
            DROP TABLE IF EXISTS contacts_backup_ift;
            CREATE TABLE contacts_backup_ift AS 
            SELECT * FROM contacts;
            
            CREATE INDEX idx_contacts_backup_ift_id ON contacts_backup_ift(id);
            """)
            
            # Verificar backup
            cursor.execute("SELECT COUNT(*) FROM contacts_backup_ift")
            backup_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM contacts")
            original_count = cursor.fetchone()[0]
            
            if backup_count == original_count:
                self.conn.commit()
                logger.info(f"✅ Backup creado: {backup_count:,} registros")
                return True
            else:
                raise Exception(f"Backup incompleto: {backup_count} vs {original_count}")
                
        except Exception as e:
            logger.error(f"❌ Error creando backup: {e}")
            self.conn.rollback()
            return False
    
    def run_sample_validation(self, sample_size=10000):
        """Ejecutar validación en muestra"""
        try:
            logger.info(f"🧪 Ejecutando validación en muestra de {sample_size:,} registros...")
            
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
            
            logger.info("📊 Resultados de validación en muestra:")
            logger.info("Status Actual → Nuevo Status | Cantidad | %")
            logger.info("-" * 50)
            
            total_changes = 0
            for row in results:
                status_actual, nuevo_status, cantidad, porcentaje = row
                logger.info(f"{status_actual} → {nuevo_status} | {cantidad:,} | {porcentaje}%")
                
                if status_actual != nuevo_status:
                    total_changes += cantidad
            
            logger.info(f"\n📈 Resumen de muestra:")
            logger.info(f"  • Total validado: {sample_size:,}")
            logger.info(f"  • Cambios necesarios: {total_changes:,}")
            logger.info(f"  • % de cambios: {(total_changes/sample_size)*100:.1f}%")
            
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
            logger.info(f"\n📱 Top operadores identificados:")
            for op, count in operators:
                logger.info(f"  • {op}: {count:,}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en validación de muestra: {e}")
            return False
    
    def run_full_validation(self):
        """Ejecutar validación completa"""
        try:
            logger.info("🚀 Iniciando validación completa de contactos...")
            
            cursor = self.conn.cursor()
            
            # Obtener total de contactos
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE phone_national IS NOT NULL")
            total_contacts = cursor.fetchone()[0]
            
            logger.info(f"📊 Total contactos a validar: {total_contacts:,}")
            
            # Procesar en lotes
            batch_size = 50000
            total_batches = (total_contacts + batch_size - 1) // batch_size
            
            logger.info(f"🔄 Procesando en {total_batches} lotes de {batch_size:,}")
            
            # Crear tabla para resultados
            cursor.execute("""
            DROP TABLE IF EXISTS temp_full_validation;
            CREATE TABLE temp_full_validation (
                id INTEGER,
                phone_national VARCHAR(12),
                status_actual VARCHAR(20),
                operador_actual VARCHAR(100),
                es_movil BOOLEAN,
                operador_ift TEXT,
                tipo_servicio VARCHAR(10),
                encontrado BOOLEAN,
                nuevo_status VARCHAR(20)
            );
            
            CREATE INDEX idx_temp_full_validation_id ON temp_full_validation(id);
            """)
            
            # Procesar por lotes
            for batch_num in range(total_batches):
                start_time = time.time()
                offset = batch_num * batch_size
                
                logger.info(f"📦 Procesando lote {batch_num + 1}/{total_batches} (offset: {offset:,})")
                
                cursor.execute(f"""
                INSERT INTO temp_full_validation
                SELECT 
                    c.id,
                    c.phone_national,
                    c.status as status_actual,
                    c.operator as operador_actual,
                    ift.es_movil,
                    ift.operador as operador_ift,
                    ift.tipo_servicio,
                    ift.encontrado,
                    CASE 
                        WHEN ift.es_movil = TRUE THEN 'VERIFIED'
                        WHEN ift.es_movil = FALSE THEN 'NOT_MOBILE'
                        ELSE 'UNKNOWN'
                    END as nuevo_status
                FROM (
                    SELECT id, phone_national, status, operator
                    FROM contacts 
                    WHERE phone_national IS NOT NULL 
                      AND phone_national ~ '^[0-9]+$'
                    ORDER BY id
                    LIMIT {batch_size} OFFSET {offset}
                ) c
                CROSS JOIN LATERAL verificar_numero_ift(c.phone_national::BIGINT) ift;
                """)
                
                batch_time = time.time() - start_time
                logger.info(f"  ⏱️ Lote completado en {batch_time:.1f}s")
                
                # Commit cada lote
                self.conn.commit()
                
                # Progress cada 10 lotes
                if (batch_num + 1) % 10 == 0:
                    progress = ((batch_num + 1) / total_batches) * 100
                    logger.info(f"  📈 Progreso: {progress:.1f}% completado")
            
            # Estadísticas finales
            cursor.execute("SELECT COUNT(*) FROM temp_full_validation")
            validated_count = cursor.fetchone()[0]
            
            logger.info(f"✅ Validación completa finalizada: {validated_count:,} contactos")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en validación completa: {e}")
            self.conn.rollback()
            return False
    
    def apply_corrections(self):
        """Aplicar correcciones a la tabla contacts"""
        try:
            logger.info("🔄 Aplicando correcciones a tabla contacts...")
            
            cursor = self.conn.cursor()
            
            # Contar cambios necesarios
            cursor.execute("""
            SELECT COUNT(*) 
            FROM temp_full_validation 
            WHERE status_actual != nuevo_status
            """)
            changes_needed = cursor.fetchone()[0]
            
            logger.info(f"📊 Cambios necesarios: {changes_needed:,}")
            
            if changes_needed == 0:
                logger.info("✅ No se necesitan cambios")
                return True
            
            # Crear log de cambios
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS status_changes_log (
                id SERIAL PRIMARY KEY,
                contact_id INTEGER,
                phone_number VARCHAR(12),
                status_anterior VARCHAR(20),
                status_nuevo VARCHAR(20),
                operador_anterior VARCHAR(100),
                operador_nuevo VARCHAR(100),
                changed_at TIMESTAMP DEFAULT NOW(),
                change_source VARCHAR(50) DEFAULT 'IFT_REVALIDATION'
            );
            """)
            
            # Insertar log de cambios
            cursor.execute("""
            INSERT INTO status_changes_log 
            (contact_id, phone_number, status_anterior, status_nuevo, operador_anterior, operador_nuevo)
            SELECT 
                id, phone_national, status_actual, nuevo_status, 
                operador_actual, operador_ift
            FROM temp_full_validation
            WHERE status_actual != nuevo_status
               OR (operador_actual IS DISTINCT FROM operador_ift AND encontrado = TRUE);
            """)
            
            # Aplicar cambios
            cursor.execute("""
            UPDATE contacts 
            SET 
                status = tfv.nuevo_status::contactstatus,
                operator = CASE 
                    WHEN tfv.encontrado = TRUE THEN tfv.operador_ift 
                    ELSE contacts.operator 
                END,
                status_updated_at = NOW(),
                status_source = 'IFT_OFFICIAL'
            FROM temp_full_validation tfv
            WHERE contacts.id = tfv.id
              AND (contacts.status::text != tfv.nuevo_status 
                   OR (contacts.operator IS DISTINCT FROM tfv.operador_ift AND tfv.encontrado = TRUE));
            """)
            
            updated_count = cursor.rowcount
            self.conn.commit()
            
            logger.info(f"✅ Correcciones aplicadas: {updated_count:,} contactos actualizados")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error aplicando correcciones: {e}")
            self.conn.rollback()
            return False
    
    def generate_final_report(self):
        """Generar reporte final"""
        try:
            logger.info("📊 Generando reporte final...")
            
            cursor = self.conn.cursor()
            
            # Estadísticas finales
            cursor.execute("""
            SELECT 
                status,
                COUNT(*) as cantidad,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje
            FROM contacts
            GROUP BY status
            ORDER BY cantidad DESC;
            """)
            
            final_stats = cursor.fetchall()
            
            logger.info("\n" + "="*60)
            logger.info("📈 ESTADÍSTICAS FINALES POR STATUS:")
            logger.info("="*60)
            
            for status, cantidad, porcentaje in final_stats:
                logger.info(f"  • {status}: {cantidad:,} ({porcentaje}%)")
            
            # Estadísticas por operador
            cursor.execute("""
            SELECT 
                operator,
                COUNT(*) as cantidad
            FROM contacts
            WHERE operator IS NOT NULL
            GROUP BY operator
            ORDER BY cantidad DESC
            LIMIT 10;
            """)
            
            operator_stats = cursor.fetchall()
            
            logger.info("\n📱 TOP 10 OPERADORES:")
            logger.info("-" * 40)
            
            for operator, cantidad in operator_stats:
                logger.info(f"  • {operator}: {cantidad:,}")
            
            # Cambios realizados
            cursor.execute("SELECT COUNT(*) FROM status_changes_log WHERE change_source = 'IFT_REVALIDATION'")
            total_changes = cursor.fetchone()[0]
            
            logger.info(f"\n🔄 RESUMEN DE CAMBIOS:")
            logger.info(f"  • Total cambios realizados: {total_changes:,}")
            
            # Estadísticas de la validación
            cursor.execute("SELECT COUNT(*) FROM temp_full_validation WHERE encontrado = TRUE")
            found_in_ift = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM temp_full_validation")
            total_validated = cursor.fetchone()[0]
            
            coverage = (found_in_ift / total_validated) * 100 if total_validated > 0 else 0
            
            logger.info(f"\n📊 COBERTURA IFT:")
            logger.info(f"  • Números encontrados en IFT: {found_in_ift:,}")
            logger.info(f"  • Total validados: {total_validated:,}")
            logger.info(f"  • Cobertura: {coverage:.1f}%")
            
            logger.info("\n" + "="*60)
            logger.info("🎉 INTEGRACIÓN IFT COMPLETADA EXITOSAMENTE")
            logger.info("="*60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error generando reporte: {e}")
            return False
    
    def run_integration(self, run_full=False):
        """Ejecutar integración completa"""
        logger.info("🚀 INICIANDO INTEGRACIÓN IFT")
        logger.info("="*60)
        
        steps = [
            ("Conectar a BD", self.connect_db),
            ("Cargar datos IFT", self.load_ift_data),
            ("Crear tabla IFT", self.create_ift_table),
            ("Cargar IFT a BD", self.load_ift_to_db),
            ("Crear función verificación", self.create_verification_function),
            ("Crear backup", self.create_backup),
            ("Validación muestra", lambda: self.run_sample_validation(10000)),
        ]
        
        if run_full:
            steps.extend([
                ("Validación completa", self.run_full_validation),
                ("Aplicar correcciones", self.apply_corrections),
                ("Generar reporte final", self.generate_final_report)
            ])
        
        for step_name, step_func in steps:
            logger.info(f"\n🔄 {step_name}...")
            if not step_func():
                logger.error(f"❌ Falló: {step_name}")
                return False
            logger.info(f"✅ Completado: {step_name}")
        
        logger.info("\n🎊 INTEGRACIÓN IFT COMPLETADA CON ÉXITO")
        return True

def main():
    """Función principal"""
    integrator = IFTIntegrator()
    
    print("🚀 INTEGRADOR DE DATOS IFT")
    print("="*50)
    print("Este script integrará los datos oficiales del IFT")
    print("y revalidará todos los contactos en la base de datos.")
    print()
    
    choice = input("¿Ejecutar integración completa? (y/N): ").lower().strip()
    run_full = choice in ['y', 'yes', 'sí', 'si']
    
    if run_full:
        print("⚠️  ADVERTENCIA: Esto modificará la base de datos")
        confirm = input("¿Confirma que quiere continuar? (y/N): ").lower().strip()
        if confirm not in ['y', 'yes', 'sí', 'si']:
            print("❌ Operación cancelada")
            return
    
    success = integrator.run_integration(run_full=run_full)
    
    if success:
        print("\n🎉 ¡Integración completada exitosamente!")
        if run_full:
            print("📊 Revisa el archivo 'ift_integration.log' para detalles completos")
    else:
        print("\n❌ La integración falló. Revisa los logs para más detalles.")

if __name__ == "__main__":
    main()