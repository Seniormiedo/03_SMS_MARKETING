#!/usr/bin/env python3
"""
Actualizador eficiente con lotes pequeños y manejo robusto de errores
Procesa 10K registros por lote para evitar timeouts
"""

import psycopg2
import time
import logging
from datetime import datetime
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('efficient_update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EfficientUpdater:
    """Actualizador eficiente con lotes pequeños"""
    
    def __init__(self, batch_size=10000):
        self.batch_size = batch_size
        self.conn = None
        self.total_processed = 0
        self.total_updated = 0
        self.start_time = None
        
    def connect_db(self):
        """Conectar a PostgreSQL"""
        try:
            self.conn = psycopg2.connect(
                host='127.0.0.1',
                port=15432,
                database='sms_marketing',
                user='sms_user',
                password='sms_password',
                connect_timeout=30
            )
            self.conn.autocommit = False
            logger.info("✅ Conexión a BD establecida")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando a BD: {e}")
            return False
    
    def test_batch_function(self):
        """Probar la función batch con un lote muy pequeño"""
        try:
            logger.info("🧪 Probando función batch con lote pequeño...")
            
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM update_contacts_batch(1, 100);")
            result = cursor.fetchone()
            
            if result:
                processed, updated, v_to_nm, nm_to_v, no_changes, not_found = result
                logger.info(f"✅ Test exitoso:")
                logger.info(f"   📊 Procesados: {processed}")
                logger.info(f"   ✏️ Actualizados: {updated}")
                logger.info(f"   🔄 VERIFIED→NOT_MOBILE: {v_to_nm}")
                logger.info(f"   🔄 NOT_MOBILE→VERIFIED: {nm_to_v}")
                logger.info(f"   ⚪ Sin cambios: {no_changes}")
                logger.info(f"   ❓ No encontrados: {not_found}")
                
                self.conn.commit()
                return True
            else:
                logger.error("❌ No se obtuvo resultado del test")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en test: {e}")
            self.conn.rollback()
            return False
    
    def get_id_range(self):
        """Obtener rango de IDs válidos"""
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
    
    def process_batch(self, start_id, end_id, batch_num, total_batches):
        """Procesar un lote con manejo robusto de errores"""
        try:
            logger.info(f"🔄 Lote {batch_num}/{total_batches}: IDs {start_id:,}-{end_id:,}")
            
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM update_contacts_batch(%s, %s);", (start_id, end_id))
            
            result = cursor.fetchone()
            
            if result:
                processed, updated, v_to_nm, nm_to_v, no_changes, not_found = result
                
                self.total_processed += processed
                self.total_updated += updated
                
                logger.info(f"✅ Lote {batch_num} completado:")
                logger.info(f"   📊 Procesados: {processed:,}")
                logger.info(f"   ✏️ Actualizados: {updated:,}")
                logger.info(f"   📱➡️📞 VERIFIED→NOT_MOBILE: {v_to_nm:,}")
                logger.info(f"   📞➡️📱 NOT_MOBILE→VERIFIED: {nm_to_v:,}")
                logger.info(f"   ⚪ Sin cambios: {no_changes:,}")
                logger.info(f"   ❓ No encontrados: {not_found:,}")
                
                self.conn.commit()
                return True
            else:
                logger.error(f"❌ No se obtuvo resultado para lote {batch_num}")
                return False
                
        except psycopg2.OperationalError as e:
            logger.error(f"❌ Error operacional en lote {batch_num}: {e}")
            self.conn.rollback()
            return False
        except Exception as e:
            logger.error(f"❌ Error en lote {batch_num}: {e}")
            self.conn.rollback()
            return False
    
    def get_progress(self):
        """Obtener progreso actual"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM get_update_progress();")
            result = cursor.fetchone()
            
            if result:
                total, processed, percentage, verified, not_mobile, changes = result
                
                logger.info(f"📈 PROGRESO TOTAL:")
                logger.info(f"   📊 Total contactos: {total:,}")
                logger.info(f"   ✅ Procesados: {processed:,} ({percentage:.2f}%)")
                logger.info(f"   📱 VERIFIED actuales: {verified:,}")
                logger.info(f"   📞 NOT_MOBILE actuales: {not_mobile:,}")
                logger.info(f"   🔄 Cambios realizados: {changes:,}")
                
                return processed, total, percentage
            else:
                return 0, 0, 0.0
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo progreso: {e}")
            return 0, 0, 0.0
    
    def run_efficient_update(self):
        """Ejecutar actualización eficiente"""
        self.start_time = datetime.now()
        logger.info("🚀 INICIANDO ACTUALIZACIÓN EFICIENTE CON LOTES PEQUEÑOS")
        logger.info("=" * 60)
        
        # 1. Conectar
        if not self.connect_db():
            logger.error("❌ Error de conexión. Abortando.")
            return False
        
        # 2. Test inicial
        if not self.test_batch_function():
            logger.error("❌ Test de función falló. Abortando.")
            return False
        
        # 3. Obtener rango
        min_id, max_id, total_contacts = self.get_id_range()
        if not min_id:
            logger.error("❌ Error obteniendo rango. Abortando.")
            return False
        
        # 4. Calcular lotes
        total_batches = ((max_id - min_id) // self.batch_size) + 1
        logger.info(f"📋 Plan de ejecución:")
        logger.info(f"   📊 Total contactos: {total_contacts:,}")
        logger.info(f"   🔢 Rango IDs: {min_id:,} - {max_id:,}")
        logger.info(f"   📦 Tamaño lote: {self.batch_size:,}")
        logger.info(f"   🔄 Total lotes: {total_batches:,}")
        logger.info(f"   ⏱️ Tiempo estimado: {(total_batches * 30) // 60} minutos")
        
        # 5. Procesar lotes
        current_id = min_id
        batch_num = 1
        failed_batches = 0
        
        while current_id <= max_id and failed_batches < 5:
            end_id = min(current_id + self.batch_size - 1, max_id)
            
            # Procesar lote
            success = self.process_batch(current_id, end_id, batch_num, total_batches)
            
            if success:
                failed_batches = 0  # Reset contador de fallos
            else:
                failed_batches += 1
                logger.warning(f"⚠️ Lote {batch_num} falló. Intentos fallidos consecutivos: {failed_batches}")
                
                if failed_batches >= 5:
                    logger.error("❌ Demasiados fallos consecutivos. Abortando.")
                    break
                
                # Pausa más larga después de fallo
                time.sleep(5)
            
            # Mostrar progreso cada 50 lotes
            if batch_num % 50 == 0:
                self.get_progress()
            
            # Pausa para no saturar la BD
            time.sleep(1)
            
            current_id = end_id + 1
            batch_num += 1
        
        # 6. Progreso final
        logger.info("\n🎊 ACTUALIZACIÓN EFICIENTE COMPLETADA")
        self.get_progress()
        
        elapsed = datetime.now() - self.start_time
        logger.info(f"⏱️ Tiempo total: {elapsed}")
        logger.info(f"📊 Total procesados: {self.total_processed:,}")
        logger.info(f"✏️ Total actualizados: {self.total_updated:,}")
        
        if self.conn:
            self.conn.close()
        
        return failed_batches < 5

def main():
    """Función principal"""
    updater = EfficientUpdater(batch_size=10000)  # Lotes de 10K
    
    print("🚀 ACTUALIZADOR EFICIENTE IFT")
    print("=" * 40)
    print("Este script procesará todos los contactos")
    print("en lotes pequeños de 10K para evitar timeouts.")
    print()
    
    confirm = input("¿Continuar con la actualización? (y/N): ").lower().strip()
    if confirm != 'y':
        print("❌ Actualización cancelada.")
        return
    
    success = updater.run_efficient_update()
    
    if success:
        print("\n🎉 ¡ACTUALIZACIÓN COMPLETADA EXITOSAMENTE!")
        print("📋 Revisa 'efficient_update.log' para detalles completos")
    else:
        print("\n❌ La actualización tuvo problemas. Revisa los logs.")

if __name__ == "__main__":
    main()