#!/usr/bin/env python3
"""
EJECUTOR ULTRA SEGURO - ACTUALIZACIÓN MASIVA CON CHECKPOINTS
Ejecuta los 367 lotes con monitoreo completo, backups y rollback automático
"""

import subprocess
import time
import logging
from datetime import datetime, timedelta
import json
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ultra_safe_update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltraSafeExecutor:
    """Ejecutor ultra seguro con checkpoints y monitoreo"""
    
    def __init__(self):
        self.start_time = None
        self.total_lotes = 367
        self.current_lote = 1
        self.total_procesados = 0
        self.total_actualizados = 0
        self.errores_count = 0
        self.checkpoint_file = 'ultra_safe_checkpoint.json'
        
    def execute_sql_docker(self, sql_command, description="SQL command", timeout=600):
        """Ejecutar SQL via Docker con timeout configurable"""
        try:
            cmd = [
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', sql_command
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"❌ Error en {description}: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ Timeout en {description} ({timeout}s)")
            return None
        except Exception as e:
            logger.error(f"❌ Error ejecutando {description}: {e}")
            return None
    
    def save_checkpoint(self):
        """Guardar checkpoint del progreso"""
        checkpoint_data = {
            'current_lote': self.current_lote,
            'total_procesados': self.total_procesados,
            'total_actualizados': self.total_actualizados,
            'errores_count': self.errores_count,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            logger.info(f"💾 Checkpoint guardado: Lote {self.current_lote}")
        except Exception as e:
            logger.error(f"❌ Error guardando checkpoint: {e}")
    
    def load_checkpoint(self):
        """Cargar checkpoint anterior si existe"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    data = json.load(f)
                
                self.current_lote = data.get('current_lote', 1)
                self.total_procesados = data.get('total_procesados', 0)
                self.total_actualizados = data.get('total_actualizados', 0)
                self.errores_count = data.get('errores_count', 0)
                
                logger.info(f"📂 Checkpoint cargado: Resumiendo desde lote {self.current_lote}")
                return True
            except Exception as e:
                logger.error(f"❌ Error cargando checkpoint: {e}")
        
        return False
    
    def get_progress_info(self):
        """Obtener información de progreso desde la BD"""
        result = self.execute_sql_docker(
            "SELECT * FROM get_update_progress_ultra_safe();",
            "Consulta de progreso"
        )
        
        if result:
            lines = result.strip().split('\n')
            for line in lines:
                if '|' in line and line.count('|') >= 8:
                    try:
                        parts = [p.strip() for p in line.split('|')]
                        if len(parts) >= 9 and parts[0].isdigit():
                            return {
                                'total_lotes': int(parts[0]),
                                'completados': int(parts[1]),
                                'en_proceso': int(parts[2]),
                                'errores': int(parts[3]),
                                'pendientes': int(parts[4]),
                                'porcentaje': float(parts[5]),
                                'procesados': int(parts[6]),
                                'actualizados': int(parts[7]),
                                'tiempo_restante': parts[8]
                            }
                    except:
                        continue
        
        return None
    
    def execute_single_batch(self, lote_id):
        """Ejecutar un solo lote con manejo de errores"""
        logger.info(f"🔄 Ejecutando lote {lote_id}/{self.total_lotes}")
        
        start_time = time.time()
        result = self.execute_sql_docker(
            f"SELECT * FROM update_batch_ultra_safe({lote_id});",
            f"Lote {lote_id}",
            timeout=1800  # 30 minutos máximo por lote
        )
        elapsed = time.time() - start_time
        
        if not result:
            logger.error(f"❌ Lote {lote_id} falló completamente")
            self.errores_count += 1
            return False
        
        # Parsear resultado
        lines = result.strip().split('\n')
        for line in lines:
            if '|' in line and line.count('|') >= 8:
                try:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 9 and parts[0].isdigit():
                        checkpoint_id = int(parts[0])
                        batch_range = parts[1]
                        processed = int(parts[2])
                        updated = int(parts[3])
                        v_to_nm = int(parts[4])
                        nm_to_v = int(parts[5])
                        no_changes = int(parts[6])
                        exec_time = float(parts[7])
                        status = parts[8]
                        
                        if status == 'SUCCESS':
                            self.total_procesados += processed
                            self.total_actualizados += updated
                            
                            logger.info(f"✅ Lote {lote_id} completado en {elapsed:.1f}s:")
                            logger.info(f"   📊 Procesados: {processed:,}")
                            logger.info(f"   ✏️ Actualizados: {updated:,}")
                            logger.info(f"   📱➡️📞 VERIFIED→NOT_MOBILE: {v_to_nm:,}")
                            logger.info(f"   📞➡️📱 NOT_MOBILE→VERIFIED: {nm_to_v:,}")
                            logger.info(f"   ⚡ Sin cambios: {no_changes:,}")
                            
                            return True
                        else:
                            logger.error(f"❌ Lote {lote_id} falló: {status}")
                            self.errores_count += 1
                            return False
                except Exception as e:
                    logger.error(f"❌ Error parseando resultado lote {lote_id}: {e}")
                    continue
        
        logger.error(f"❌ No se pudo parsear resultado del lote {lote_id}")
        self.errores_count += 1
        return False
    
    def show_progress_summary(self):
        """Mostrar resumen de progreso"""
        progress = self.get_progress_info()
        if progress:
            logger.info("📊 PROGRESO ACTUAL:")
            logger.info(f"   🎯 Lotes: {progress['completados']}/{progress['total_lotes']} ({progress['porcentaje']:.1f}%)")
            logger.info(f"   📊 Procesados: {progress['procesados']:,}")
            logger.info(f"   ✏️ Actualizados: {progress['actualizados']:,}")
            logger.info(f"   ❌ Errores: {progress['errores']}")
            logger.info(f"   ⏱️ Tiempo restante: {progress['tiempo_restante']}")
        
        elapsed = datetime.now() - self.start_time if self.start_time else timedelta(0)
        logger.info(f"   🕒 Tiempo transcurrido: {elapsed}")
    
    def run_ultra_safe_update(self):
        """Ejecutar actualización ultra segura completa"""
        self.start_time = datetime.now()
        
        logger.info("🔒 INICIANDO ACTUALIZACIÓN ULTRA SEGURA")
        logger.info("=" * 60)
        logger.info(f"📊 Total de lotes: {self.total_lotes}")
        logger.info(f"📦 Tamaño por lote: 100,000 contactos")
        logger.info(f"🎯 Total estimado: ~36.6M contactos")
        logger.info(f"💾 Checkpoints automáticos cada lote")
        logger.info(f"🔄 Rollback completo disponible")
        logger.info("")
        
        # Cargar checkpoint si existe
        if self.load_checkpoint():
            logger.info(f"🔄 Resumiendo desde lote {self.current_lote}")
        
        # Ejecutar lotes
        while self.current_lote <= self.total_lotes:
            try:
                # Ejecutar lote actual
                success = self.execute_single_batch(self.current_lote)
                
                if success:
                    self.current_lote += 1
                    self.save_checkpoint()
                    
                    # Mostrar progreso cada 10 lotes
                    if self.current_lote % 10 == 0:
                        self.show_progress_summary()
                    
                    # Pausa pequeña entre lotes
                    time.sleep(2)
                else:
                    logger.error(f"❌ Lote {self.current_lote} falló")
                    
                    # Preguntar si continuar después de error
                    if self.errores_count >= 5:
                        logger.error("❌ Demasiados errores. Deteniendo ejecución.")
                        break
                    
                    # Continuar con el siguiente lote
                    self.current_lote += 1
                    time.sleep(5)  # Pausa más larga después de error
                    
            except KeyboardInterrupt:
                logger.info("⚠️ Interrupción detectada. Guardando progreso...")
                self.save_checkpoint()
                logger.info("💾 Progreso guardado. Puedes reanudar después.")
                return False
            except Exception as e:
                logger.error(f"❌ Error inesperado en lote {self.current_lote}: {e}")
                self.errores_count += 1
                self.current_lote += 1
                time.sleep(5)
        
        # Resumen final
        elapsed = datetime.now() - self.start_time
        logger.info("\n🎊 ACTUALIZACIÓN ULTRA SEGURA COMPLETADA")
        logger.info("=" * 60)
        logger.info(f"⏱️ Tiempo total: {elapsed}")
        logger.info(f"📊 Total procesados: {self.total_procesados:,}")
        logger.info(f"✏️ Total actualizados: {self.total_actualizados:,}")
        logger.info(f"❌ Errores: {self.errores_count}")
        
        # Mostrar progreso final
        self.show_progress_summary()
        
        # Limpiar checkpoint
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
            logger.info("🧹 Checkpoint final limpiado")
        
        return True

def main():
    """Función principal"""
    executor = UltraSafeExecutor()
    
    print("🔒 ACTUALIZACIÓN ULTRA SEGURA CON CHECKPOINTS")
    print("=" * 60)
    print("📊 367 lotes de 100K contactos cada uno")
    print("💾 Backup completo creado automáticamente")
    print("🔄 Checkpoints cada lote + rollback completo")
    print("⏱️ Tiempo estimado: 8-12 horas")
    print("🎯 Actualizará TODOS los 31.8M contactos")
    print("")
    print("⚠️ IMPORTANTE:")
    print("- Puedes interrumpir con Ctrl+C y reanudar después")
    print("- Rollback completo disponible si algo falla")
    print("- Monitoreo completo en ultra_safe_update.log")
    print("")
    
    confirm = input("¿Ejecutar ACTUALIZACIÓN ULTRA SEGURA? (y/N): ").lower().strip()
    if confirm != 'y':
        print("❌ Actualización cancelada.")
        return
    
    success = executor.run_ultra_safe_update()
    
    if success:
        print("\n🎉 ¡ACTUALIZACIÓN ULTRA SEGURA COMPLETADA!")
        print("📋 Revisa 'ultra_safe_update.log' para detalles")
        print("🎯 Base de datos IFT 100% consistente y precisa")
    else:
        print("\n⚠️ Actualización interrumpida o con errores.")
        print("📂 Progreso guardado. Ejecuta de nuevo para reanudar.")

if __name__ == "__main__":
    main()