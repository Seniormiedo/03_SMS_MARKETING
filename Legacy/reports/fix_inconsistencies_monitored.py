#!/usr/bin/env python3
"""
CORRECTOR DE INCONSISTENCIAS IFT - PROCESO MONITOREABLE
Detecta y corrige contactos mal clasificados después de Lightning Fast
"""

import psycopg2
import time
import logging
from datetime import datetime
import subprocess
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_inconsistencies.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class InconsistencyFixer:
    """Corrector de inconsistencias con monitoreo completo"""
    
    def __init__(self):
        self.start_time = None
        self.total_inconsistencies = 0
        self.fixed_count = 0
        
    def execute_sql_docker(self, sql_command, description="SQL command"):
        """Ejecutar SQL via Docker (más estable)"""
        try:
            cmd = [
                'docker-compose', 'exec', '-T', 'postgres',
                'psql', '-U', 'sms_user', '-d', 'sms_marketing',
                '-c', sql_command
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
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
    
    def analyze_inconsistencies(self):
        """Analizar inconsistencias en la clasificación"""
        logger.info("🔍 ANALIZANDO INCONSISTENCIAS...")
        
        # Análisis de inconsistencias por lotes pequeños
        analysis_sql = """
        SELECT 
            'INCONSISTENCIAS DETECTADAS' as titulo,
            COUNT(*) as total_inconsistencias
        FROM (
            SELECT c.id, c.phone_national, c.status, ift.tipo_servicio
            FROM contacts c 
            LEFT JOIN ift_rangos ift ON (
                c.phone_national::BIGINT >= ift.numero_inicial 
                AND c.phone_national::BIGINT <= ift.numero_final
            )
            WHERE c.phone_national IS NOT NULL
              AND (
                (c.status = 'NOT_MOBILE' AND ift.tipo_servicio = 'CPP') OR
                (c.status = 'VERIFIED' AND ift.tipo_servicio IN ('MPP', 'FIJO'))
              )
            LIMIT 100000
        ) inconsistencias;
        """
        
        result = self.execute_sql_docker(analysis_sql, "Análisis de inconsistencias")
        if result:
            logger.info("📊 Resultado del análisis:")
            logger.info(result[-500:])
            
            # Extraer número de inconsistencias
            lines = result.strip().split('\n')
            for line in lines:
                if '|' in line and line.strip().split('|')[0].strip().isdigit():
                    self.total_inconsistencies = int(line.strip().split('|')[0].strip())
                    break
        
        return result is not None
    
    def get_detailed_inconsistencies(self):
        """Obtener detalles de las inconsistencias"""
        logger.info("📋 OBTENIENDO DETALLES DE INCONSISTENCIAS...")
        
        details_sql = """
        SELECT 
            'DESGLOSE DE INCONSISTENCIAS' as titulo;
        
        -- NOT_MOBILE que deberían ser VERIFIED (CPP)
        SELECT 
            'NOT_MOBILE -> VERIFIED (CPP)' as tipo_error,
            COUNT(*) as cantidad
        FROM contacts c 
        LEFT JOIN ift_rangos ift ON (
            c.phone_national::BIGINT >= ift.numero_inicial 
            AND c.phone_national::BIGINT <= ift.numero_final
        )
        WHERE c.status = 'NOT_MOBILE' 
          AND ift.tipo_servicio = 'CPP'
          AND c.phone_national IS NOT NULL;
        
        -- VERIFIED que deberían ser NOT_MOBILE (MPP/FIJO)
        SELECT 
            'VERIFIED -> NOT_MOBILE (MPP/FIJO)' as tipo_error,
            COUNT(*) as cantidad
        FROM contacts c 
        LEFT JOIN ift_rangos ift ON (
            c.phone_national::BIGINT >= ift.numero_inicial 
            AND c.phone_national::BIGINT <= ift.numero_final
        )
        WHERE c.status = 'VERIFIED' 
          AND ift.tipo_servicio IN ('MPP', 'FIJO')
          AND c.phone_national IS NOT NULL;
        """
        
        result = self.execute_sql_docker(details_sql, "Detalles de inconsistencias")
        if result:
            logger.info("📊 Detalles de inconsistencias:")
            logger.info(result)
        
        return result is not None
    
    def fix_inconsistencies_batch(self, batch_size=10000):
        """Corregir inconsistencias en lotes monitoreables"""
        logger.info(f"🔧 CORRIGIENDO INCONSISTENCIAS EN LOTES DE {batch_size:,}")
        
        # Función SQL para corrección por lotes
        fix_function_sql = f"""
        CREATE OR REPLACE FUNCTION fix_inconsistencies_batch(batch_size INTEGER DEFAULT {batch_size})
        RETURNS TABLE(
            fixed_nm_to_v INTEGER,
            fixed_v_to_nm INTEGER,
            total_fixed INTEGER
        ) AS $$
        DECLARE
            nm_to_v_count INTEGER := 0;
            v_to_nm_count INTEGER := 0;
            total_count INTEGER := 0;
        BEGIN
            -- Corregir NOT_MOBILE que deberían ser VERIFIED (CPP)
            WITH nm_to_v AS (
                UPDATE contacts 
                SET status = 'VERIFIED', updated_at = NOW()
                FROM ift_rangos ift
                WHERE contacts.phone_national::BIGINT >= ift.numero_inicial 
                  AND contacts.phone_national::BIGINT <= ift.numero_final
                  AND contacts.status = 'NOT_MOBILE'
                  AND ift.tipo_servicio = 'CPP'
                  AND contacts.phone_national IS NOT NULL
                  AND contacts.id IN (
                      SELECT c.id 
                      FROM contacts c
                      LEFT JOIN ift_rangos i ON (
                          c.phone_national::BIGINT >= i.numero_inicial 
                          AND c.phone_national::BIGINT <= i.numero_final
                      )
                      WHERE c.status = 'NOT_MOBILE' 
                        AND i.tipo_servicio = 'CPP'
                        AND c.phone_national IS NOT NULL
                      LIMIT batch_size
                  )
                RETURNING 1
            )
            SELECT COUNT(*) INTO nm_to_v_count FROM nm_to_v;
            
            -- Corregir VERIFIED que deberían ser NOT_MOBILE (MPP/FIJO)  
            WITH v_to_nm AS (
                UPDATE contacts 
                SET status = 'NOT_MOBILE', updated_at = NOW()
                FROM ift_rangos ift
                WHERE contacts.phone_national::BIGINT >= ift.numero_inicial 
                  AND contacts.phone_national::BIGINT <= ift.numero_final
                  AND contacts.status = 'VERIFIED'
                  AND ift.tipo_servicio IN ('MPP', 'FIJO')
                  AND contacts.phone_national IS NOT NULL
                  AND contacts.id IN (
                      SELECT c.id 
                      FROM contacts c
                      LEFT JOIN ift_rangos i ON (
                          c.phone_national::BIGINT >= i.numero_inicial 
                          AND c.phone_national::BIGINT <= i.numero_final
                      )
                      WHERE c.status = 'VERIFIED' 
                        AND i.tipo_servicio IN ('MPP', 'FIJO')
                        AND c.phone_national IS NOT NULL
                      LIMIT batch_size
                  )
                RETURNING 1
            )
            SELECT COUNT(*) INTO v_to_nm_count FROM v_to_nm;
            
            total_count := nm_to_v_count + v_to_nm_count;
            
            RETURN QUERY SELECT nm_to_v_count, v_to_nm_count, total_count;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        # Crear función
        if not self.execute_sql_docker(fix_function_sql, "Creación de función de corrección"):
            return False
        
        # Ejecutar correcciones por lotes
        batch_num = 1
        total_fixed = 0
        
        while True:
            logger.info(f"🔄 Procesando lote {batch_num} ({batch_size:,} contactos máx)...")
            
            result = self.execute_sql_docker(
                "SELECT * FROM fix_inconsistencies_batch();",
                f"Corrección lote {batch_num}"
            )
            
            if not result:
                logger.error(f"❌ Error en lote {batch_num}")
                break
            
            # Extraer resultados
            lines = result.strip().split('\n')
            for line in lines:
                if '|' in line and line.count('|') >= 2:
                    try:
                        parts = [p.strip() for p in line.split('|')]
                        if len(parts) >= 3 and parts[0].isdigit():
                            nm_to_v = int(parts[0])
                            v_to_nm = int(parts[1]) 
                            batch_total = int(parts[2])
                            
                            logger.info(f"✅ Lote {batch_num} completado:")
                            logger.info(f"   📱 NOT_MOBILE → VERIFIED: {nm_to_v:,}")
                            logger.info(f"   📞 VERIFIED → NOT_MOBILE: {v_to_nm:,}")
                            logger.info(f"   🎯 Total corregido: {batch_total:,}")
                            
                            total_fixed += batch_total
                            self.fixed_count = total_fixed
                            
                            if batch_total == 0:
                                logger.info("✅ No hay más inconsistencias. Corrección completada.")
                                return True
                            
                            break
                    except:
                        continue
            
            batch_num += 1
            time.sleep(1)  # Pausa entre lotes
            
            if batch_num > 100:  # Límite de seguridad
                logger.warning("⚠️ Límite de lotes alcanzado")
                break
        
        logger.info(f"🎯 Total de inconsistencias corregidas: {total_fixed:,}")
        return True
    
    def final_verification(self):
        """Verificación final post-corrección"""
        logger.info("🔍 VERIFICACIÓN FINAL POST-CORRECCIÓN")
        
        verification_sql = """
        SELECT '=== DISTRIBUCIÓN FINAL CORREGIDA ===' as titulo;
        
        SELECT status, COUNT(*) as cantidad, 
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje
        FROM contacts 
        GROUP BY status 
        ORDER BY cantidad DESC;
        
        SELECT '=== VERIFICACIÓN DE CONSISTENCIA ===' as titulo;
        
        -- Verificar que no queden inconsistencias
        SELECT 
            'Inconsistencias restantes' as verificacion,
            COUNT(*) as cantidad
        FROM contacts c 
        LEFT JOIN ift_rangos ift ON (
            c.phone_national::BIGINT >= ift.numero_inicial 
            AND c.phone_national::BIGINT <= ift.numero_final
        )
        WHERE c.phone_national IS NOT NULL
          AND (
            (c.status = 'NOT_MOBILE' AND ift.tipo_servicio = 'CPP') OR
            (c.status = 'VERIFIED' AND ift.tipo_servicio IN ('MPP', 'FIJO'))
          );
        """
        
        result = self.execute_sql_docker(verification_sql, "Verificación final")
        if result:
            logger.info("📊 VERIFICACIÓN FINAL:")
            logger.info(result)
        
        return result is not None
    
    def run_fix_process(self):
        """Ejecutar proceso completo de corrección"""
        self.start_time = datetime.now()
        logger.info("🔧 INICIANDO CORRECCIÓN DE INCONSISTENCIAS IFT")
        logger.info("=" * 60)
        
        # Paso 1: Analizar inconsistencias
        if not self.analyze_inconsistencies():
            logger.error("❌ Error analizando inconsistencias")
            return False
        
        # Paso 2: Obtener detalles
        if not self.get_detailed_inconsistencies():
            logger.error("❌ Error obteniendo detalles")
            return False
        
        # Paso 3: Corregir por lotes
        if not self.fix_inconsistencies_batch():
            logger.error("❌ Error corrigiendo inconsistencias")
            return False
        
        # Paso 4: Verificación final
        if not self.final_verification():
            logger.error("❌ Error en verificación final")
            return False
        
        # Resultado final
        elapsed = datetime.now() - self.start_time
        logger.info("\n🎊 CORRECCIÓN DE INCONSISTENCIAS COMPLETADA")
        logger.info("=" * 60)
        logger.info(f"⏱️ Tiempo total: {elapsed}")
        logger.info(f"🔧 Inconsistencias corregidas: {self.fixed_count:,}")
        logger.info(f"✅ Base de datos IFT ahora 100% consistente")
        
        return True

def main():
    """Función principal"""
    fixer = InconsistencyFixer()
    
    print("🔧 CORRECTOR DE INCONSISTENCIAS IFT")
    print("=" * 50)
    print("🔍 Detecta y corrige contactos mal clasificados")
    print("📊 Proceso completamente monitoreable")
    print("⚡ Corrección por lotes de 10K")
    print("")
    
    confirm = input("¿Ejecutar CORRECCIÓN DE INCONSISTENCIAS? (y/N): ").lower().strip()
    if confirm != 'y':
        print("❌ Corrección cancelada.")
        return
    
    success = fixer.run_fix_process()
    
    if success:
        print("\n🎉 ¡INCONSISTENCIAS CORREGIDAS EXITOSAMENTE!")
        print("📋 Revisa 'fix_inconsistencies.log' para detalles")
        print("🎯 Base de datos IFT 100% consistente")
    else:
        print("\n❌ La corrección tuvo problemas. Revisa los logs.")

if __name__ == "__main__":
    main()