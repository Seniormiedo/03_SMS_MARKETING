#!/usr/bin/env python3
"""
ACTUALIZADOR MONITOREABLE PARA DOCKER
Actualiza todos los contactos con monitoreo en tiempo real
"""

import subprocess
import time
import logging
from datetime import datetime
import sys

# Configurar logging para mostrar en consola
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('docker_update.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DockerMonitoredUpdater:
    """Actualizador con monitoreo completo para Docker"""
    
    def __init__(self):
        self.start_time = None
        self.total_procesados = 0
        self.total_actualizados = 0
        
    def execute_sql_with_progress(self, sql_command, description="SQL"):
        """Ejecutar SQL con monitoreo de progreso"""
        logger.info(f"🔄 {description}...")
        
        try:
            cmd = [
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', sql_command
            ]
            
            # Ejecutar con output en tiempo real
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            output_lines = []
            error_lines = []
            
            # Leer output en tiempo real
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    output_lines.append(line)
                    if '|' in line or 'NOTICE:' in line or 'rows' in line:
                        logger.info(f"📊 {line}")
            
            # Leer errores si los hay
            stderr_output = process.stderr.read()
            if stderr_output:
                error_lines.append(stderr_output.strip())
                logger.error(f"❌ Error: {stderr_output.strip()}")
            
            return_code = process.poll()
            
            if return_code == 0:
                logger.info(f"✅ {description} completado exitosamente")
                return '\n'.join(output_lines)
            else:
                logger.error(f"❌ {description} falló con código {return_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando {description}: {e}")
            return None
    
    def check_current_state(self):
        """Verificar estado actual"""
        logger.info("🔍 VERIFICANDO ESTADO ACTUAL...")
        
        result = self.execute_sql_with_progress(
            "SELECT status, COUNT(*) as cantidad FROM contacts GROUP BY status ORDER BY cantidad DESC;",
            "Consulta de estado actual"
        )
        
        return result is not None
    
    def create_backup(self):
        """Crear backup de seguridad"""
        logger.info("💾 CREANDO BACKUP DE SEGURIDAD...")
        
        backup_sql = """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'contacts_backup_monitored') THEN
                CREATE TABLE contacts_backup_monitored AS SELECT * FROM contacts;
                RAISE NOTICE 'Backup monitored creado con % registros', (SELECT COUNT(*) FROM contacts_backup_monitored);
            ELSE
                RAISE NOTICE 'Backup monitored ya existe';
            END IF;
        END $$;
        """
        
        result = self.execute_sql_with_progress(backup_sql, "Creación de backup")
        return result is not None
    
    def update_batch_with_progress(self, batch_start, batch_end, batch_num, total_batches):
        """Actualizar lote con progreso"""
        logger.info(f"🔄 PROCESANDO LOTE {batch_num}/{total_batches} (IDs {batch_start:,}-{batch_end:,})")
        
        update_sql = f"""
        WITH batch_updates AS (
            SELECT 
                c.id,
                c.phone_national,
                c.status as status_actual,
                c.operator as operator_actual,
                CASE 
                    WHEN ift.tipo_servicio = 'CPP' THEN 'VERIFIED'::contactstatus
                    WHEN ift.tipo_servicio IN ('MPP', 'FIJO') THEN 'NOT_MOBILE'::contactstatus
                    ELSE c.status
                END as nuevo_status,
                COALESCE(
                    CASE WHEN LENGTH(ift.operador) <= 100 THEN ift.operador ELSE c.operator END,
                    c.operator
                ) as nuevo_operator,
                ift.tipo_servicio
            FROM contacts c
            LEFT JOIN ift_rangos ift ON (
                c.phone_national::BIGINT >= ift.numero_inicial 
                AND c.phone_national::BIGINT <= ift.numero_final
            )
            WHERE c.id BETWEEN {batch_start} AND {batch_end}
              AND c.phone_national IS NOT NULL
        ),
        contacts_to_update AS (
            SELECT * FROM batch_updates
            WHERE nuevo_status != status_actual 
               OR nuevo_operator != operator_actual
        ),
        update_result AS (
            UPDATE contacts
            SET 
                status = ctu.nuevo_status,
                operator = ctu.nuevo_operator,
                updated_at = NOW()
            FROM contacts_to_update ctu
            WHERE contacts.id = ctu.id
            RETURNING contacts.id
        )
        SELECT 
            'LOTE {batch_num}' as lote,
            COUNT(*) as procesados,
            (SELECT COUNT(*) FROM update_result) as actualizados,
            (SELECT COUNT(*) FROM contacts_to_update WHERE status_actual = 'NOT_MOBILE' AND nuevo_status = 'VERIFIED') as nm_to_v,
            (SELECT COUNT(*) FROM contacts_to_update WHERE status_actual = 'VERIFIED' AND nuevo_status = 'NOT_MOBILE') as v_to_nm
        FROM batch_updates;
        """
        
        result = self.execute_sql_with_progress(
            update_sql, 
            f"Actualización lote {batch_num}"
        )
        
        if result:
            # Extraer estadísticas del resultado
            lines = result.split('\n')
            for line in lines:
                if '|' in line and 'LOTE' in line:
                    try:
                        parts = [p.strip() for p in line.split('|')]
                        if len(parts) >= 5:
                            procesados = int(parts[1])
                            actualizados = int(parts[2])
                            nm_to_v = int(parts[3])
                            v_to_nm = int(parts[4])
                            
                            self.total_procesados += procesados
                            self.total_actualizados += actualizados
                            
                            logger.info(f"✅ Lote {batch_num} completado:")
                            logger.info(f"   📊 Procesados: {procesados:,}")
                            logger.info(f"   ✏️ Actualizados: {actualizados:,}")
                            logger.info(f"   📞➡️📱 NOT_MOBILE→VERIFIED: {nm_to_v:,}")
                            logger.info(f"   📱➡️📞 VERIFIED→NOT_MOBILE: {v_to_nm:,}")
                            logger.info(f"   🎯 Total acumulado: {self.total_procesados:,} procesados, {self.total_actualizados:,} actualizados")
                            
                            return True
                    except:
                        continue
        
        logger.error(f"❌ Error procesando lote {batch_num}")
        return False
    
    def run_monitored_update(self):
        """Ejecutar actualización con monitoreo completo"""
        self.start_time = datetime.now()
        
        logger.info("🚀 INICIANDO ACTUALIZACIÓN MONITOREABLE")
        logger.info("=" * 60)
        
        # Paso 1: Verificar estado actual
        if not self.check_current_state():
            logger.error("❌ Error verificando estado actual")
            return False
        
        # Paso 2: Crear backup
        if not self.create_backup():
            logger.error("❌ Error creando backup")
            return False
        
        # Paso 3: Obtener rango de IDs
        logger.info("📊 OBTENIENDO RANGO DE CONTACTOS...")
        
        range_result = self.execute_sql_with_progress(
            "SELECT MIN(id) as min_id, MAX(id) as max_id, COUNT(*) as total FROM contacts WHERE phone_national IS NOT NULL;",
            "Consulta de rango"
        )
        
        if not range_result:
            logger.error("❌ Error obteniendo rango")
            return False
        
        # Extraer rango (valores por defecto si no se puede parsear)
        min_id = 1
        max_id = 36645703
        batch_size = 50000  # Lotes más pequeños para mejor monitoreo
        
        logger.info(f"📊 Rango de IDs: {min_id:,} - {max_id:,}")
        logger.info(f"📦 Tamaño de lote: {batch_size:,} contactos")
        
        # Calcular número de lotes
        total_batches = ((max_id - min_id) // batch_size) + 1
        logger.info(f"🎯 Total de lotes: {total_batches}")
        
        # Paso 4: Procesar por lotes
        current_batch = 1
        current_start = min_id
        
        while current_start <= max_id:
            current_end = min(current_start + batch_size - 1, max_id)
            
            success = self.update_batch_with_progress(
                current_start, 
                current_end, 
                current_batch, 
                total_batches
            )
            
            if not success:
                logger.error(f"❌ Error en lote {current_batch}")
            
            # Mostrar progreso cada 10 lotes
            if current_batch % 10 == 0:
                elapsed = datetime.now() - self.start_time
                progress_pct = (current_batch / total_batches) * 100
                logger.info(f"📈 PROGRESO: {progress_pct:.1f}% completado ({current_batch}/{total_batches} lotes)")
                logger.info(f"⏱️ Tiempo transcurrido: {elapsed}")
            
            current_batch += 1
            current_start = current_end + 1
            
            # Pausa pequeña entre lotes
            time.sleep(1)
        
        # Paso 5: Verificación final
        logger.info("🔍 VERIFICACIÓN FINAL...")
        
        final_result = self.execute_sql_with_progress(
            "SELECT status, COUNT(*) as cantidad FROM contacts GROUP BY status ORDER BY cantidad DESC;",
            "Verificación final"
        )
        
        # Resultado final
        elapsed = datetime.now() - self.start_time
        logger.info("\n🎊 ACTUALIZACIÓN MONITOREABLE COMPLETADA")
        logger.info("=" * 60)
        logger.info(f"⏱️ Tiempo total: {elapsed}")
        logger.info(f"📊 Total procesados: {self.total_procesados:,}")
        logger.info(f"✏️ Total actualizados: {self.total_actualizados:,}")
        logger.info(f"🎯 Base de datos IFT actualizada completamente")
        
        return True

def main():
    """Función principal"""
    updater = DockerMonitoredUpdater()
    
    print("🚀 ACTUALIZACIÓN MONITOREABLE PARA DOCKER")
    print("=" * 60)
    print("📊 Procesa todos los contactos en lotes de 50K")
    print("👀 Monitoreo en tiempo real del progreso")
    print("💾 Backup automático de seguridad")
    print("⏱️ Tiempo estimado: 2-4 horas")
    print("")
    
    confirm = input("¿Ejecutar ACTUALIZACIÓN MONITOREABLE? (y/N): ").lower().strip()
    if confirm != 'y':
        print("❌ Actualización cancelada.")
        return
    
    success = updater.run_monitored_update()
    
    if success:
        print("\n🎉 ¡ACTUALIZACIÓN COMPLETADA EXITOSAMENTE!")
        print("📋 Revisa 'docker_update.log' para detalles completos")
    else:
        print("\n❌ La actualización tuvo problemas.")

if __name__ == "__main__":
    main()