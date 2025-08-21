#!/usr/bin/env python3
"""
Ejecutor automático para actualización masiva de contactos con rangos IFT
Procesa por lotes para evitar timeouts y proporciona monitoreo en tiempo real
"""

import subprocess
import time
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mass_update_ift.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MassUpdateExecutor:
    """Ejecutor de actualización masiva por lotes"""
    
    def __init__(self, batch_size=100000):
        self.batch_size = batch_size
        self.total_processed = 0
        self.total_updated = 0
        self.start_time = None
        
    def execute_sql(self, sql_command, description="SQL command"):
        """Ejecutar comando SQL via Docker"""
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
    
    def load_update_script(self):
        """Cargar el script de actualización en la base de datos"""
        logger.info("📋 Cargando script de actualización masiva...")
        
        # Copiar script al contenedor
        copy_cmd = [
            'docker', 'cp', 
            'update_contacts_ift_complete.sql', 
            'sms_postgres:/tmp/update_contacts_ift_complete.sql'
        ]
        
        result = subprocess.run(copy_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"❌ Error copiando script: {result.stderr}")
            return False
        
        # Ejecutar script
        exec_cmd = [
            'docker-compose', 'exec', '-T', 'postgres',
            'psql', '-U', 'sms_user', '-d', 'sms_marketing',
            '-f', '/tmp/update_contacts_ift_complete.sql'
        ]
        
        result = subprocess.run(exec_cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            logger.info("✅ Script de actualización cargado")
            logger.info(f"📊 Resultado: {result.stdout[-500:]}")  # Últimas 500 chars
            return True
        else:
            logger.error(f"❌ Error cargando script: {result.stderr}")
            return False
    
    def get_id_range(self):
        """Obtener rango de IDs para procesamiento"""
        logger.info("🔍 Obteniendo rango de IDs...")
        
        sql = """
        SELECT 
            MIN(id) as min_id,
            MAX(id) as max_id,
            COUNT(*) as total_contacts
        FROM contacts
        WHERE phone_national IS NOT NULL 
          AND phone_national ~ '^[0-9]+$'
          AND length(phone_national::text) = 10;
        """
        
        result = self.execute_sql(sql, "Obtener rango IDs")
        if result:
            # Parsear resultado
            lines = result.strip().split('\n')
            for line in lines:
                if '|' in line and 'min_id' not in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 3:
                        try:
                            min_id = int(parts[0])
                            max_id = int(parts[1])
                            total = int(parts[2])
                            logger.info(f"📊 Rango: {min_id:,} - {max_id:,} ({total:,} contactos)")
                            return min_id, max_id, total
                        except:
                            continue
        
        logger.error("❌ No se pudo obtener rango de IDs")
        return None, None, None
    
    def process_batch(self, start_id, end_id, batch_num, total_batches):
        """Procesar un lote de contactos"""
        logger.info(f"🔄 Procesando lote {batch_num}/{total_batches}: IDs {start_id:,} - {end_id:,}")
        
        sql = f"SELECT * FROM update_contacts_batch({start_id}, {end_id});"
        
        start_time = time.time()
        result = self.execute_sql(sql, f"Lote {batch_num}")
        elapsed = time.time() - start_time
        
        if result:
            # Parsear resultados
            lines = result.strip().split('\n')
            for line in lines:
                if '|' in line and 'processed' not in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 6:
                        try:
                            processed = int(parts[0])
                            updated = int(parts[1])
                            v_to_nm = int(parts[2])
                            nm_to_v = int(parts[3])
                            no_changes = int(parts[4])
                            not_found = int(parts[5])
                            
                            self.total_processed += processed
                            self.total_updated += updated
                            
                            logger.info(f"✅ Lote {batch_num} completado en {elapsed:.1f}s:")
                            logger.info(f"   📊 Procesados: {processed:,}")
                            logger.info(f"   ✏️ Actualizados: {updated:,}")
                            logger.info(f"   📱➡️📞 VERIFIED→NOT_MOBILE: {v_to_nm:,}")
                            logger.info(f"   📞➡️📱 NOT_MOBILE→VERIFIED: {nm_to_v:,}")
                            logger.info(f"   ⚪ Sin cambios: {no_changes:,}")
                            logger.info(f"   ❓ No encontrados: {not_found:,}")
                            
                            return True
                        except Exception as e:
                            logger.error(f"❌ Error parseando resultados del lote {batch_num}: {e}")
                            return False
        
        logger.error(f"❌ Error procesando lote {batch_num}")
        return False
    
    def get_progress(self):
        """Obtener progreso actual"""
        sql = "SELECT * FROM get_update_progress();"
        result = self.execute_sql(sql, "Progreso actual")
        
        if result:
            lines = result.strip().split('\n')
            for line in lines:
                if '|' in line and 'total_contacts' not in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 6:
                        try:
                            total = int(parts[0])
                            processed = int(parts[1])
                            percentage = float(parts[2])
                            verified = int(parts[3])
                            not_mobile = int(parts[4])
                            changes = int(parts[5])
                            
                            logger.info(f"📈 PROGRESO ACTUAL:")
                            logger.info(f"   📊 Total contactos: {total:,}")
                            logger.info(f"   ✅ Procesados: {processed:,} ({percentage:.1f}%)")
                            logger.info(f"   📱 VERIFIED: {verified:,}")
                            logger.info(f"   📞 NOT_MOBILE: {not_mobile:,}")
                            logger.info(f"   🔄 Cambios realizados: {changes:,}")
                            
                            return processed, total, percentage
                        except:
                            continue
        
        return 0, 0, 0.0
    
    def run_mass_update(self):
        """Ejecutar actualización masiva completa"""
        self.start_time = datetime.now()
        logger.info("🚀 INICIANDO ACTUALIZACIÓN MASIVA CON RANGOS IFT")
        logger.info("=" * 60)
        
        # 1. Cargar script
        if not self.load_update_script():
            logger.error("❌ Error cargando script. Abortando.")
            return False
        
        # 2. Obtener rango
        min_id, max_id, total_contacts = self.get_id_range()
        if not min_id:
            logger.error("❌ Error obteniendo rango. Abortando.")
            return False
        
        # 3. Calcular lotes
        total_batches = ((max_id - min_id) // self.batch_size) + 1
        logger.info(f"📋 Plan de ejecución:")
        logger.info(f"   📊 Total contactos: {total_contacts:,}")
        logger.info(f"   🔢 Rango IDs: {min_id:,} - {max_id:,}")
        logger.info(f"   📦 Tamaño lote: {self.batch_size:,}")
        logger.info(f"   🔄 Total lotes: {total_batches:,}")
        
        # 4. Procesar lotes
        current_id = min_id
        batch_num = 1
        
        while current_id <= max_id:
            end_id = min(current_id + self.batch_size - 1, max_id)
            
            # Procesar lote
            if not self.process_batch(current_id, end_id, batch_num, total_batches):
                logger.error(f"❌ Error en lote {batch_num}. Continuando...")
            
            # Mostrar progreso cada 10 lotes
            if batch_num % 10 == 0:
                self.get_progress()
            
            # Pausa pequeña para no saturar la BD
            time.sleep(1)
            
            current_id = end_id + 1
            batch_num += 1
        
        # 5. Progreso final
        logger.info("\n🎊 ACTUALIZACIÓN MASIVA COMPLETADA")
        self.get_progress()
        
        elapsed = datetime.now() - self.start_time
        logger.info(f"⏱️ Tiempo total: {elapsed}")
        logger.info(f"📊 Total procesados: {self.total_processed:,}")
        logger.info(f"✏️ Total actualizados: {self.total_updated:,}")
        
        return True

def main():
    """Función principal"""
    executor = MassUpdateExecutor(batch_size=50000)  # Lotes de 50K para mayor velocidad
    
    print("🚀 EJECUTOR DE ACTUALIZACIÓN MASIVA IFT")
    print("=" * 50)
    print("Este script actualizará TODOS los contactos (31.8M)")
    print("basándose en los rangos oficiales del IFT.")
    print()
    
    confirm = input("¿Continuar con la actualización masiva? (y/N): ").lower().strip()
    if confirm != 'y':
        print("❌ Actualización cancelada.")
        return
    
    success = executor.run_mass_update()
    
    if success:
        print("\n🎉 ¡ACTUALIZACIÓN MASIVA COMPLETADA EXITOSAMENTE!")
        print("📋 Revisa 'mass_update_ift.log' para detalles completos")
        print("🎯 Todos los contactos ahora tienen clasificación IFT oficial")
    else:
        print("\n❌ La actualización tuvo problemas. Revisa los logs.")

if __name__ == "__main__":
    main()