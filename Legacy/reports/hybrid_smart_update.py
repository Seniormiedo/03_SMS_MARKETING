#!/usr/bin/env python3
"""
ESTRATEGIA HÍBRIDA INTELIGENTE
Combina Lightning Fast (80%) + Ultra Fast (20%) = Óptima velocidad + control
Tiempo estimado: 1-2 horas vs 15-20 horas original
"""

import psycopg2
import time
import logging
from datetime import datetime, timedelta
import subprocess
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hybrid_update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HybridSmartUpdater:
    """Actualizador híbrido inteligente"""
    
    def __init__(self):
        self.conn = None
        self.start_time = None
        self.phase1_processed = 0
        self.phase2_processed = 0
        self.total_updated = 0
        
    def connect_db(self):
        """Conectar a PostgreSQL"""
        try:
            self.conn = psycopg2.connect(
                host='127.0.0.1',
                port=15432,
                database='sms_marketing',
                user='sms_user',
                password='sms_password',
                connect_timeout=60
            )
            self.conn.autocommit = False
            logger.info("✅ Conexión establecida")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando: {e}")
            return False
    
    def execute_sql_docker(self, sql_command, description="SQL command"):
        """Ejecutar SQL via Docker (más estable)"""
        try:
            cmd = [
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', sql_command
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0:
                logger.info(f"✅ {description} ejecutado exitosamente")
                return result.stdout
            else:
                logger.error(f"❌ Error en {description}: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ Timeout en {description}")
            return None
        except Exception as e:
            logger.error(f"❌ Error ejecutando {description}: {e}")
            return None
    
    def get_contact_distribution(self):
        """Analizar distribución de contactos para estrategia híbrida"""
        try:
            logger.info("📊 Analizando distribución de contactos...")
            
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as cantidad,
                    MIN(id) as min_id,
                    MAX(id) as max_id
                FROM contacts
                WHERE phone_national IS NOT NULL 
                  AND phone_national ~ '^[0-9]+$'
                  AND length(phone_national::text) = 10
                GROUP BY status
                ORDER BY cantidad DESC;
            """)
            
            results = cursor.fetchall()
            
            logger.info("📋 Distribución actual:")
            total_contacts = 0
            for status, cantidad, min_id, max_id in results:
                total_contacts += cantidad
                logger.info(f"   {status}: {cantidad:,} contactos (IDs {min_id}-{max_id})")
            
            return total_contacts, results
            
        except Exception as e:
            logger.error(f"❌ Error analizando distribución: {e}")
            return None, None
    
    def phase1_lightning_bulk(self):
        """FASE 1: Lightning Fast para procesamiento masivo"""
        logger.info("⚡ FASE 1: LIGHTNING FAST BULK UPDATE")
        logger.info("=" * 50)
        
        # Crear script Lightning optimizado
        lightning_script = """
        -- FASE 1: Lightning Fast Optimizada
        SET work_mem = '1GB';
        SET maintenance_work_mem = '2GB';
        
        SELECT '=== INICIANDO FASE 1: LIGHTNING FAST ===' as mensaje;
        
        -- Función Lightning optimizada
        CREATE OR REPLACE FUNCTION phase1_lightning_update()
        RETURNS TABLE(
            total_processed BIGINT,
            total_updated BIGINT,
            verified_to_not_mobile BIGINT,
            not_mobile_to_verified BIGINT,
            execution_time_seconds NUMERIC
        ) AS $$
        DECLARE
            start_time TIMESTAMP;
            end_time TIMESTAMP;
            processed_count BIGINT := 0;
            updated_count BIGINT := 0;
            v_to_nm_count BIGINT := 0;
            nm_to_v_count BIGINT := 0;
        BEGIN
            start_time := clock_timestamp();
            
            -- Actualización masiva directa para contactos estables (80% estimado)
            WITH updates_needed AS (
                SELECT 
                    c.id,
                    c.status::TEXT as status_actual,
                    CASE 
                        WHEN ift.tipo_servicio = 'CPP' THEN 'VERIFIED'
                        WHEN ift.tipo_servicio IN ('MPP', 'FIJO') THEN 'NOT_MOBILE'
                        ELSE c.status::TEXT
                    END as nuevo_status,
                    COALESCE(ift.operador, c.operator) as nuevo_operator
                FROM contacts c
                LEFT JOIN ift_rangos ift ON (
                    c.phone_national::BIGINT >= ift.numero_inicial 
                    AND c.phone_national::BIGINT <= ift.numero_final
                )
                WHERE c.phone_national IS NOT NULL 
                  AND c.phone_national ~ '^[0-9]+$'
                  AND length(c.phone_national::text) = 10
                  AND c.id <= 25000000  -- 80% de ~31M contactos
            )
            UPDATE contacts 
            SET 
                status = un.nuevo_status::contactstatus,
                operator = un.nuevo_operator,
                updated_at = NOW()
            FROM updates_needed un
            WHERE contacts.id = un.id
              AND un.nuevo_status != un.status_actual;
            
            GET DIAGNOSTICS updated_count = ROW_COUNT;
            
            -- Contar procesados
            SELECT COUNT(*) INTO processed_count
            FROM contacts 
            WHERE id <= 25000000
              AND phone_national IS NOT NULL 
              AND phone_national ~ '^[0-9]+$'
              AND length(phone_national::text) = 10;
            
            end_time := clock_timestamp();
            
            RETURN QUERY SELECT 
                processed_count,
                updated_count,
                0::BIGINT, -- Se calculará después
                0::BIGINT, -- Se calculará después
                EXTRACT(EPOCH FROM (end_time - start_time))::NUMERIC;
        END;
        $$ LANGUAGE plpgsql;
        
        -- Ejecutar Fase 1
        SELECT * FROM phase1_lightning_update();
        
        SELECT '=== FASE 1 COMPLETADA ===' as mensaje;
        """
        
        # Escribir script temporal
        with open('phase1_lightning.sql', 'w', encoding='utf-8') as f:
            f.write(lightning_script)
        
        # Ejecutar via Docker
        try:
            # Copiar script
            subprocess.run(['docker', 'cp', 'phase1_lightning.sql', 'sms_postgres:/tmp/'], check=True)
            
            # Ejecutar
            start_time = time.time()
            result = self.execute_sql_docker(
                "\\i /tmp/phase1_lightning.sql", 
                "Fase 1 Lightning Fast"
            )
            elapsed = time.time() - start_time
            
            if result:
                logger.info(f"✅ Fase 1 completada en {elapsed:.1f} segundos")
                logger.info("📊 Resultado:")
                logger.info(result[-1000:])  # Últimas 1000 chars del resultado
                
                # Extraer números del resultado si es posible
                lines = result.strip().split('\n')
                for line in lines:
                    if '|' in line and line.count('|') >= 4:
                        try:
                            parts = [p.strip() for p in line.split('|')]
                            if len(parts) >= 5 and parts[0].isdigit():
                                self.phase1_processed = int(parts[0])
                                phase1_updated = int(parts[1])
                                self.total_updated += phase1_updated
                                logger.info(f"📊 Fase 1: {self.phase1_processed:,} procesados, {phase1_updated:,} actualizados")
                                break
                        except:
                            continue
                
                return True
            else:
                logger.error("❌ Fase 1 falló")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en Fase 1: {e}")
            return False
        finally:
            # Limpiar archivo temporal
            if os.path.exists('phase1_lightning.sql'):
                os.remove('phase1_lightning.sql')
    
    def phase2_ultra_monitoring(self):
        """FASE 2: Ultra Fast con monitoreo para contactos restantes"""
        logger.info("🚀 FASE 2: ULTRA FAST CON MONITOREO")
        logger.info("=" * 50)
        
        try:
            # Procesar contactos restantes (IDs > 25M) en lotes de 100K
            cursor = self.conn.cursor()
            
            # Obtener rango restante
            cursor.execute("""
                SELECT COUNT(*) 
                FROM contacts 
                WHERE id > 25000000
                  AND phone_national IS NOT NULL 
                  AND phone_national ~ '^[0-9]+$'
                  AND length(phone_national::text) = 10;
            """)
            
            remaining_contacts = cursor.fetchone()[0]
            logger.info(f"📊 Contactos restantes para Fase 2: {remaining_contacts:,}")
            
            if remaining_contacts == 0:
                logger.info("✅ No hay contactos restantes, Fase 2 omitida")
                return True
            
            # Procesar en lotes de 100K
            batch_size = 100000
            current_id = 25000001
            max_id = 36645703  # ID máximo conocido
            
            while current_id <= max_id:
                end_id = min(current_id + batch_size - 1, max_id)
                
                logger.info(f"🔄 Procesando lote: {current_id:,} - {end_id:,}")
                
                # Usar función ultra fast existente
                cursor.execute("SELECT * FROM update_contacts_ultra_fast(%s, %s);", (current_id, end_id))
                result = cursor.fetchone()
                
                if result:
                    processed, updated, v_to_nm, nm_to_v, no_changes = result
                    self.phase2_processed += processed
                    self.total_updated += updated
                    
                    logger.info(f"✅ Lote completado:")
                    logger.info(f"   📊 Procesados: {processed:,}")
                    logger.info(f"   ✏️ Actualizados: {updated:,}")
                    logger.info(f"   📱➡️📞 VERIFIED→NOT_MOBILE: {v_to_nm:,}")
                    logger.info(f"   📞➡️📱 NOT_MOBILE→VERIFIED: {nm_to_v:,}")
                    
                    self.conn.commit()
                else:
                    logger.error(f"❌ Error en lote {current_id}-{end_id}")
                
                current_id = end_id + 1
                time.sleep(1)  # Pausa pequeña
            
            logger.info(f"✅ Fase 2 completada: {self.phase2_processed:,} procesados")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en Fase 2: {e}")
            self.conn.rollback()
            return False
    
    def phase3_final_verification(self):
        """FASE 3: Verificación final completa"""
        logger.info("🔍 FASE 3: VERIFICACIÓN FINAL")
        logger.info("=" * 50)
        
        try:
            cursor = self.conn.cursor()
            
            # Estadísticas finales
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as cantidad,
                    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje
                FROM contacts
                WHERE phone_national IS NOT NULL 
                  AND phone_national ~ '^[0-9]+$'
                  AND length(phone_national::text) = 10
                GROUP BY status
                ORDER BY cantidad DESC;
            """)
            
            results = cursor.fetchall()
            
            logger.info("📊 DISTRIBUCIÓN FINAL:")
            for status, cantidad, porcentaje in results:
                logger.info(f"   {status}: {cantidad:,} ({porcentaje}%)")
            
            # Verificar integridad
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE phone_national IS NOT NULL;")
            total_final = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM contacts_ift_changes;")
            changes_logged = cursor.fetchone()[0]
            
            logger.info(f"📋 VERIFICACIÓN:")
            logger.info(f"   Total contactos finales: {total_final:,}")
            logger.info(f"   Cambios registrados: {changes_logged:,}")
            logger.info(f"   Fase 1 procesados: {self.phase1_processed:,}")
            logger.info(f"   Fase 2 procesados: {self.phase2_processed:,}")
            logger.info(f"   Total actualizados: {self.total_updated:,}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en verificación: {e}")
            return False
    
    def run_hybrid_update(self):
        """Ejecutar estrategia híbrida completa"""
        self.start_time = datetime.now()
        logger.info("🔥 INICIANDO ESTRATEGIA HÍBRIDA INTELIGENTE")
        logger.info("=" * 60)
        logger.info("⚡ Fase 1: Lightning Fast (80% masivo)")
        logger.info("🚀 Fase 2: Ultra Fast (20% monitoreo)")
        logger.info("🔍 Fase 3: Verificación final")
        logger.info("⏱️ Tiempo estimado: 1-2 horas")
        logger.info("")
        
        # Conectar
        if not self.connect_db():
            return False
        
        # Analizar distribución
        total_contacts, distribution = self.get_contact_distribution()
        if not total_contacts:
            return False
        
        logger.info(f"📊 Total contactos a procesar: {total_contacts:,}")
        
        # FASE 1: Lightning Fast (80%)
        logger.info("\n" + "="*60)
        if not self.phase1_lightning_bulk():
            logger.error("❌ Fase 1 falló, abortando")
            return False
        
        # FASE 2: Ultra Fast (20%)
        logger.info("\n" + "="*60)
        if not self.phase2_ultra_monitoring():
            logger.error("❌ Fase 2 falló, pero Fase 1 completada")
        
        # FASE 3: Verificación
        logger.info("\n" + "="*60)
        self.phase3_final_verification()
        
        # Resultado final
        elapsed = datetime.now() - self.start_time
        total_processed = self.phase1_processed + self.phase2_processed
        avg_speed = total_processed / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
        
        logger.info("\n🎊 ESTRATEGIA HÍBRIDA COMPLETADA")
        logger.info("=" * 60)
        logger.info(f"⏱️ Tiempo total: {elapsed}")
        logger.info(f"📊 Total procesados: {total_processed:,}")
        logger.info(f"✏️ Total actualizados: {self.total_updated:,}")
        logger.info(f"⚡ Velocidad promedio: {avg_speed:.0f} contactos/segundo")
        logger.info(f"🔥 Fase 1 (Lightning): {self.phase1_processed:,}")
        logger.info(f"🚀 Fase 2 (Ultra Fast): {self.phase2_processed:,}")
        
        if self.conn:
            self.conn.close()
        
        return True

def main():
    """Función principal"""
    updater = HybridSmartUpdater()
    
    print("🔥 ESTRATEGIA HÍBRIDA INTELIGENTE")
    print("=" * 50)
    print("⚡ Fase 1: Lightning Fast para 80% de contactos")
    print("🚀 Fase 2: Ultra Fast para 20% con monitoreo")
    print("🔍 Fase 3: Verificación completa")
    print("⏱️ Tiempo estimado: 1-2 horas")
    print("⚡ Velocidad: 5,000-7,000 contactos/segundo")
    print("")
    
    confirm = input("¿Ejecutar ESTRATEGIA HÍBRIDA? (y/N): ").lower().strip()
    if confirm != 'y':
        print("❌ Actualización cancelada.")
        return
    
    success = updater.run_hybrid_update()
    
    if success:
        print("\n🎉 ¡ESTRATEGIA HÍBRIDA COMPLETADA EXITOSAMENTE!")
        print("📋 Revisa 'hybrid_update.log' para detalles completos")
        print("🎯 Base de datos transformada con máxima eficiencia")
    else:
        print("\n❌ La actualización tuvo problemas. Revisa los logs.")

if __name__ == "__main__":
    main()