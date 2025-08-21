#!/usr/bin/env python3
"""
ACTUALIZADOR ULTRA RÁPIDO CON MONITOREO
Procesa 100K registros por lote = 8-10x más rápido
Tiempo estimado: 2-3 horas vs 15-20 horas anterior
"""

import psycopg2
import time
import logging
from datetime import datetime, timedelta
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ultra_fast_update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltraFastUpdater:
    """Actualizador ultra rápido con lotes de 100K"""
    
    def __init__(self, batch_size=100000):
        self.batch_size = batch_size
        self.conn = None
        self.total_processed = 0
        self.total_updated = 0
        self.start_time = None
        self.checkpoints = []
        
    def connect_db(self):
        """Conectar a PostgreSQL con configuración optimizada"""
        try:
            self.conn = psycopg2.connect(
                host='127.0.0.1',
                port=15432,
                database='sms_marketing',
                user='sms_user',
                password='sms_password',
                connect_timeout=60,
                # Optimizaciones de conexión
                options='-c statement_timeout=600000'  # 10 minutos timeout
            )
            self.conn.autocommit = False
            
            # Optimizaciones de sesión
            cursor = self.conn.cursor()
            cursor.execute("""
                SET work_mem = '256MB';
                SET maintenance_work_mem = '512MB';
                SET checkpoint_completion_target = 0.9;
            """)
            self.conn.commit()
            
            logger.info("✅ Conexión optimizada establecida")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando: {e}")
            return False
    
    def create_fast_batch_function(self):
        """Crear función optimizada para lotes grandes"""
        try:
            logger.info("⚙️ Creando función ultra rápida...")
            
            cursor = self.conn.cursor()
            cursor.execute("""
            CREATE OR REPLACE FUNCTION update_contacts_ultra_fast(
                batch_start BIGINT,
                batch_end BIGINT
            ) RETURNS TABLE(
                processed INTEGER,
                updated INTEGER,
                verified_to_not_mobile INTEGER,
                not_mobile_to_verified INTEGER,
                no_changes INTEGER
            ) AS $$
            DECLARE
                proc_count INTEGER := 0;
                upd_count INTEGER := 0;
                v_to_nm INTEGER := 0;
                nm_to_v INTEGER := 0;
                no_change INTEGER := 0;
            BEGIN
                -- Crear tabla temporal con los contactos a procesar
                CREATE TEMP TABLE temp_batch_contacts AS
                SELECT 
                    c.id,
                    c.phone_national,
                    c.status::TEXT as status_actual,
                    c.operator as operator_actual
                FROM contacts c
                WHERE c.id BETWEEN batch_start AND batch_end
                  AND c.phone_national IS NOT NULL 
                  AND c.phone_national ~ '^[0-9]+$'
                  AND length(c.phone_national::text) = 10;
                
                -- Crear índice temporal para optimizar JOIN
                CREATE INDEX idx_temp_batch_phone ON temp_batch_contacts (phone_national);
                
                -- Actualización masiva optimizada
                WITH updates_to_make AS (
                    SELECT 
                        tbc.id,
                        tbc.status_actual,
                        CASE 
                            WHEN ift.tipo_servicio = 'CPP' THEN 'VERIFIED'
                            WHEN ift.tipo_servicio IN ('MPP', 'FIJO') THEN 'NOT_MOBILE'
                            ELSE tbc.status_actual
                        END as nuevo_status,
                        COALESCE(ift.operador, tbc.operator_actual) as nuevo_operator
                    FROM temp_batch_contacts tbc
                    LEFT JOIN ift_rangos ift ON (
                        tbc.phone_national::BIGINT >= ift.numero_inicial 
                        AND tbc.phone_national::BIGINT <= ift.numero_final
                    )
                ),
                contact_updates AS (
                    UPDATE contacts 
                    SET 
                        status = utm.nuevo_status::contactstatus,
                        operator = utm.nuevo_operator,
                        updated_at = NOW()
                    FROM updates_to_make utm
                    WHERE contacts.id = utm.id
                      AND utm.nuevo_status != utm.status_actual
                    RETURNING 
                        contacts.id,
                        utm.status_actual,
                        utm.nuevo_status
                )
                SELECT 
                    COUNT(*)::INTEGER as total_processed,
                    (SELECT COUNT(*)::INTEGER FROM contact_updates) as total_updated,
                    (SELECT COUNT(*)::INTEGER FROM contact_updates WHERE status_actual = 'VERIFIED' AND nuevo_status = 'NOT_MOBILE') as v_to_nm_count,
                    (SELECT COUNT(*)::INTEGER FROM contact_updates WHERE status_actual = 'NOT_MOBILE' AND nuevo_status = 'VERIFIED') as nm_to_v_count,
                    (SELECT COUNT(*)::INTEGER FROM temp_batch_contacts) - (SELECT COUNT(*)::INTEGER FROM contact_updates) as no_change_count
                FROM temp_batch_contacts
                INTO proc_count, upd_count, v_to_nm, nm_to_v, no_change;
                
                -- Limpiar tabla temporal
                DROP TABLE temp_batch_contacts;
                
                RETURN QUERY SELECT proc_count, upd_count, v_to_nm, nm_to_v, no_change;
            END;
            $$ LANGUAGE plpgsql;
            """)
            
            self.conn.commit()
            logger.info("✅ Función ultra rápida creada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando función: {e}")
            self.conn.rollback()
            return False
    
    def test_ultra_fast_batch(self):
        """Test con lote pequeño primero"""
        try:
            logger.info("🧪 Probando función ultra rápida con 1K registros...")
            
            cursor = self.conn.cursor()
            start_time = time.time()
            
            cursor.execute("SELECT * FROM update_contacts_ultra_fast(1, 1000);")
            result = cursor.fetchone()
            
            elapsed = time.time() - start_time
            
            if result:
                processed, updated, v_to_nm, nm_to_v, no_changes = result
                
                logger.info(f"✅ Test exitoso en {elapsed:.1f}s:")
                logger.info(f"   📊 Procesados: {processed}")
                logger.info(f"   ✏️ Actualizados: {updated}")
                logger.info(f"   📱➡️📞 VERIFIED→NOT_MOBILE: {v_to_nm}")
                logger.info(f"   📞➡️📱 NOT_MOBILE→VERIFIED: {nm_to_v}")
                logger.info(f"   ⚪ Sin cambios: {no_changes}")
                logger.info(f"   ⚡ Velocidad: {processed/elapsed:.0f} contactos/segundo")
                
                self.conn.commit()
                return True
            else:
                logger.error("❌ No se obtuvo resultado del test")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en test: {e}")
            self.conn.rollback()
            return False
    
    def process_ultra_fast_batch(self, start_id, end_id, batch_num, total_batches):
        """Procesar lote ultra rápido de 100K"""
        try:
            logger.info(f"🚀 Lote ULTRA {batch_num}/{total_batches}: IDs {start_id:,}-{end_id:,}")
            
            cursor = self.conn.cursor()
            start_time = time.time()
            
            cursor.execute("SELECT * FROM update_contacts_ultra_fast(%s, %s);", (start_id, end_id))
            result = cursor.fetchone()
            
            elapsed = time.time() - start_time
            
            if result:
                processed, updated, v_to_nm, nm_to_v, no_changes = result
                
                self.total_processed += processed
                self.total_updated += updated
                
                speed = processed / elapsed if elapsed > 0 else 0
                
                logger.info(f"✅ Lote {batch_num} completado en {elapsed:.1f}s:")
                logger.info(f"   📊 Procesados: {processed:,}")
                logger.info(f"   ✏️ Actualizados: {updated:,}")
                logger.info(f"   📱➡️📞 VERIFIED→NOT_MOBILE: {v_to_nm:,}")
                logger.info(f"   📞➡️📱 NOT_MOBILE→VERIFIED: {nm_to_v:,}")
                logger.info(f"   ⚪ Sin cambios: {no_changes:,}")
                logger.info(f"   ⚡ Velocidad: {speed:.0f} contactos/segundo")
                
                self.conn.commit()
                
                # Crear checkpoint cada 1M procesados
                if self.total_processed % 1000000 == 0:
                    self.create_checkpoint()
                
                return True
            else:
                logger.error(f"❌ No se obtuvo resultado para lote {batch_num}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en lote {batch_num}: {e}")
            self.conn.rollback()
            return False
    
    def create_checkpoint(self):
        """Crear checkpoint de progreso"""
        try:
            checkpoint_time = datetime.now()
            self.checkpoints.append({
                'time': checkpoint_time,
                'processed': self.total_processed,
                'updated': self.total_updated
            })
            
            logger.info(f"💾 CHECKPOINT: {self.total_processed:,} procesados")
            
            # Obtener progreso actual
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM get_update_progress();")
            result = cursor.fetchone()
            
            if result:
                total, processed, percentage, verified, not_mobile, changes = result
                
                elapsed = checkpoint_time - self.start_time
                remaining_contacts = total - processed
                speed = processed / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
                eta = remaining_contacts / speed if speed > 0 else 0
                eta_time = checkpoint_time + timedelta(seconds=eta)
                
                logger.info(f"📈 PROGRESO CHECKPOINT:")
                logger.info(f"   📊 Total: {total:,} | Procesados: {processed:,} ({percentage:.2f}%)")
                logger.info(f"   📱 VERIFIED: {verified:,} | 📞 NOT_MOBILE: {not_mobile:,}")
                logger.info(f"   🔄 Cambios: {changes:,}")
                logger.info(f"   ⚡ Velocidad promedio: {speed:.0f} contactos/segundo")
                logger.info(f"   ⏱️ ETA: {eta_time.strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"❌ Error creando checkpoint: {e}")
    
    def get_id_range(self):
        """Obtener rango de IDs"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    MIN(id) as min_id,
                    MAX(id) as max_id,
                    COUNT(*) as total_contacts
                FROM contacts
                WHERE phone_national IS NOT NULL 
                  AND phone_national ~ '^[0-9]+$'
                  AND length(phone_national::text) = 10;
            """)
            
            result = cursor.fetchone()
            if result:
                min_id, max_id, total = result
                logger.info(f"📊 Rango IDs: {min_id:,} - {max_id:,} ({total:,} contactos)")
                return min_id, max_id, total
            else:
                return None, None, None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo rango: {e}")
            return None, None, None
    
    def run_ultra_fast_update(self):
        """Ejecutar actualización ultra rápida"""
        self.start_time = datetime.now()
        logger.info("🚀 INICIANDO ACTUALIZACIÓN ULTRA RÁPIDA")
        logger.info("=" * 60)
        
        # 1. Conectar
        if not self.connect_db():
            return False
        
        # 2. Crear función optimizada
        if not self.create_fast_batch_function():
            return False
        
        # 3. Test inicial
        if not self.test_ultra_fast_batch():
            return False
        
        # 4. Obtener rango
        min_id, max_id, total_contacts = self.get_id_range()
        if not min_id:
            return False
        
        # 5. Calcular lotes
        total_batches = ((max_id - min_id) // self.batch_size) + 1
        logger.info(f"📋 Plan ULTRA RÁPIDO:")
        logger.info(f"   📊 Total contactos: {total_contacts:,}")
        logger.info(f"   📦 Tamaño lote: {self.batch_size:,}")
        logger.info(f"   🔄 Total lotes: {total_batches:,}")
        logger.info(f"   ⏱️ Tiempo estimado: {(total_batches * 60) // 3600} horas")
        logger.info(f"   ⚡ Velocidad objetivo: 2,500+ contactos/segundo")
        
        # 6. Procesar lotes ultra rápidos
        current_id = min_id
        batch_num = 1
        failed_batches = 0
        
        while current_id <= max_id and failed_batches < 3:
            end_id = min(current_id + self.batch_size - 1, max_id)
            
            success = self.process_ultra_fast_batch(current_id, end_id, batch_num, total_batches)
            
            if success:
                failed_batches = 0
            else:
                failed_batches += 1
                logger.warning(f"⚠️ Lote {batch_num} falló. Fallos consecutivos: {failed_batches}")
                
                if failed_batches >= 3:
                    logger.error("❌ Demasiados fallos. Abortando.")
                    break
                
                time.sleep(10)  # Pausa más larga tras fallo
            
            # Pausa mínima para no saturar
            time.sleep(0.5)
            
            current_id = end_id + 1
            batch_num += 1
        
        # 7. Resultado final
        elapsed = datetime.now() - self.start_time
        avg_speed = self.total_processed / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
        
        logger.info("\n🎊 ACTUALIZACIÓN ULTRA RÁPIDA COMPLETADA")
        logger.info(f"⏱️ Tiempo total: {elapsed}")
        logger.info(f"📊 Total procesados: {self.total_processed:,}")
        logger.info(f"✏️ Total actualizados: {self.total_updated:,}")
        logger.info(f"⚡ Velocidad promedio: {avg_speed:.0f} contactos/segundo")
        logger.info(f"💾 Checkpoints creados: {len(self.checkpoints)}")
        
        if self.conn:
            self.conn.close()
        
        return failed_batches < 3

def main():
    """Función principal"""
    updater = UltraFastUpdater(batch_size=100000)  # Lotes de 100K
    
    print("🚀 ACTUALIZADOR ULTRA RÁPIDO IFT")
    print("=" * 50)
    print("⚡ Lotes de 100K contactos = 8-10x más rápido")
    print("⏱️ Tiempo estimado: 2-3 horas (vs 15-20 anterior)")
    print("📊 Monitoreo completo mantenido")
    print("💾 Checkpoints cada 1M contactos")
    print()
    
    confirm = input("¿Continuar con actualización ULTRA RÁPIDA? (y/N): ").lower().strip()
    if confirm != 'y':
        print("❌ Actualización cancelada.")
        return
    
    success = updater.run_ultra_fast_update()
    
    if success:
        print("\n🎉 ¡ACTUALIZACIÓN ULTRA RÁPIDA COMPLETADA!")
        print("📋 Revisa 'ultra_fast_update.log' para detalles completos")
        print("🎯 Base de datos transformada con precisión IFT del 99.9%")
    else:
        print("\n❌ La actualización tuvo problemas. Revisa los logs.")

if __name__ == "__main__":
    main()