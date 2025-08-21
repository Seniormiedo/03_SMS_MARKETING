#!/usr/bin/env python3
"""
Migration Manager - Gestión profesional de migración de datos
SMS Marketing Platform - Migración de 36.6M registros
"""

import asyncio
import sqlite3
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from pathlib import Path

import asyncpg
import phonenumbers
from phonenumbers import carrier, geocoder, PhoneNumberType

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MigrationStats:
    """Estadísticas de migración"""
    total_records: int = 0
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    start_time: datetime = None
    current_batch: int = 0
    total_batches: int = 0
    records_per_second: float = 0.0
    estimated_completion: datetime = None

class PhoneNumberNormalizer:
    """Normalizador de números telefónicos mexicanos"""
    
    def __init__(self):
        self.mexico_region = "MX"
        self.mobile_operators = {
            "Telcel": ["55", "56", "81", "82", "83", "84"],
            "Movistar": ["55", "56"],
            "AT&T": ["55", "56"],
            "Virgin": ["55", "56"]
        }
    
    def normalize_mexican_phone(self, phone_str: str) -> Dict[str, Any]:
        """
        Normalizar número telefónico mexicano
        
        Args:
            phone_str: Número telefónico como string
            
        Returns:
            Dict con información normalizada del número
        """
        if not phone_str:
            return self._create_error_result("Empty phone number")
        
        try:
            # Limpiar el número
            clean_phone = self._clean_phone_number(phone_str)
            
            # Intentar parsear como número mexicano
            parsed_number = phonenumbers.parse(clean_phone, self.mexico_region)
            
            # Validar número
            if not phonenumbers.is_valid_number(parsed_number):
                return self._create_error_result("Invalid phone number format")
            
            # Extraer información
            e164_format = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            national_format = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL)
            
            # Detectar tipo de número
            number_type = phonenumbers.number_type(parsed_number)
            is_mobile = number_type in [PhoneNumberType.MOBILE, PhoneNumberType.PERSONAL_NUMBER]
            
            # Obtener información del carrier
            try:
                operator_name = carrier.name_for_number(parsed_number, "es")
            except:
                operator_name = None
                
            try:
                location = geocoder.description_for_number(parsed_number, "es")
            except:
                location = None
            
            # Limpiar formato nacional (remover espacios y paréntesis)
            national_clean = ''.join(filter(str.isdigit, national_format))
            
            # Determinar tipo de número de forma más robusta
            number_type_name = "UNKNOWN"
            if number_type:
                try:
                    number_type_name = number_type.name
                except:
                    number_type_name = str(number_type)
            
            return {
                "success": True,
                "phone_e164": e164_format,
                "phone_national": national_clean,
                "phone_original": phone_str,
                "is_mobile": is_mobile,
                "operator": operator_name or None,
                "location": location or None,
                "number_type": number_type_name,
                "status": "VERIFIED" if is_mobile else "NOT_MOBILE"
            }
            
        except phonenumbers.NumberParseException as e:
            return self._create_error_result(f"Parse error: {e}")
        except Exception as e:
            return self._create_error_result(f"Unexpected error: {e}")
    
    def _clean_phone_number(self, phone_str: str) -> str:
        """Limpiar número telefónico para parsing"""
        if not phone_str:
            return ""
        
        # Convertir a string y limpiar
        clean = str(phone_str).strip()
        
        # Si ya tiene +52, mantenerlo
        if clean.startswith("+52"):
            return clean
        
        # Si es número de 10 dígitos, agregar +52
        digits_only = ''.join(filter(str.isdigit, clean))
        if len(digits_only) == 10:
            return f"+52{digits_only}"
        
        # Si es número de 12 dígitos y empieza con 52
        if len(digits_only) == 12 and digits_only.startswith("52"):
            return f"+{digits_only}"
        
        return clean
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Crear resultado de error"""
        return {
            "success": False,
            "error": error_message,
            "phone_e164": None,
            "phone_national": None,
            "phone_original": None,
            "is_mobile": False,
            "operator": None,
            "location": None,
            "number_type": "INVALID",
            "status": "INVALID_FORMAT"
        }

class DataTransformer:
    """Transformador de datos para migración"""
    
    def __init__(self):
        self.phone_normalizer = PhoneNumberNormalizer()
        
        # Mapeo de estados
        self.state_mapping = {
            "AGS": "AGUASCALIENTES",
            "BC": "BAJA CALIFORNIA",
            "BCS": "BAJA CALIFORNIA SUR",
            "CAM": "CAMPECHE",
            "CHIS": "CHIAPAS",
            "CHIH": "CHIHUAHUA",
            "CDMX": "CIUDAD DE MEXICO",
            "COAH": "COAHUILA",
            "COL": "COLIMA",
            "DUR": "DURANGO",
            "GTO": "GUANAJUATO",
            "GRO": "GUERRERO",
            "HGO": "HIDALGO",
            "JAL": "JALISCO",
            "MEX": "MEXICO",
            "MICH": "MICHOACAN",
            "MOR": "MORELOS",
            "NAY": "NAYARIT",
            "NL": "NUEVO LEON",
            "OAX": "OAXACA",
            "PUE": "PUEBLA",
            "QRO": "QUERETARO",
            "QROO": "QUINTANA ROO",
            "SLP": "SAN LUIS POTOSI",
            "SIN": "SINALOA",
            "SON": "SONORA",
            "TAB": "TABASCO",
            "TAMS": "TAMAULIPAS",
            "TLAX": "TLAXCALA",
            "VER": "VERACRUZ",
            "YUC": "YUCATAN",
            "ZAC": "ZACATECAS"
        }
    
    def transform_record(self, source_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transformar un registro de SQLite a formato PostgreSQL
        
        Args:
            source_record: Registro de la base de datos fuente
            
        Returns:
            Registro transformado para PostgreSQL
        """
        try:
            # Normalizar número telefónico
            phone_info = self.phone_normalizer.normalize_mexican_phone(source_record.get('numero'))
            
            # Transformar campos básicos
            transformed = {
                # Campos de teléfono
                "phone_e164": phone_info.get("phone_e164"),
                "phone_national": phone_info.get("phone_national"),
                "phone_original": source_record.get('campo1_original') or source_record.get('numero'),
                
                # Información personal
                "full_name": self._clean_text(source_record.get('nombre')),
                "address": self._clean_text(source_record.get('direccion')),
                "neighborhood": self._clean_text(source_record.get('colonia')),
                
                # Información geográfica
                "lada": self._clean_lada(source_record.get('lada')),
                "state_code": self._normalize_state_code(source_record.get('estado_cof')),
                "state_name": self._get_state_name(source_record.get('estado_cof')),
                "municipality": self._clean_text(source_record.get('municipio_cof')),
                "city": self._clean_text(source_record.get('ciudad_por_lada')),
                
                # Características del teléfono
                "is_mobile": phone_info.get("is_mobile", True),
                "operator": phone_info.get("operator"),
                
                # Status (mapear desde es_valido)
                "status": self._map_status(source_record.get('es_valido'), phone_info.get("status")),
                "status_updated_at": datetime.now(timezone.utc),
                "status_source": "migration_script",
                
                # Control de envíos
                "send_count": 0,
                "last_sent_at": None,
                
                # Opt-out
                "opt_out_at": None,
                "opt_out_method": None,
                
                # Validación
                "last_validated_at": datetime.now(timezone.utc),
                "validation_attempts": 1,
                
                # Fuente de datos
                "source": "TELCEL2022",
                "import_batch_id": f"migration_{datetime.now().strftime('%Y%m%d')}",
                
                # Timestamps
                "created_at": self._parse_timestamp(source_record.get('fecha_migracion')),
                "updated_at": datetime.now(timezone.utc)
            }
            
            return {
                "success": True,
                "data": transformed,
                "warnings": []
            }
            
        except Exception as e:
            logger.error(f"Error transforming record: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def _clean_text(self, text: str) -> Optional[str]:
        """Limpiar texto general"""
        if not text:
            return None
        
        cleaned = str(text).strip()
        return cleaned if cleaned else None
    
    def _clean_lada(self, lada: str) -> Optional[str]:
        """Limpiar y validar código LADA"""
        if not lada:
            return None
        
        clean_lada = ''.join(filter(str.isdigit, str(lada)))
        
        # Validar longitud de LADA mexicana
        if len(clean_lada) in [2, 3]:
            return clean_lada
        
        return None
    
    def _normalize_state_code(self, state: str) -> Optional[str]:
        """Normalizar código de estado"""
        if not state:
            return None
        
        state_upper = str(state).strip().upper()
        
        # Si ya es un código conocido, devolverlo
        if state_upper in self.state_mapping:
            return state_upper
        
        # Buscar por nombre completo
        for code, name in self.state_mapping.items():
            if name.upper() == state_upper:
                return code
        
        return state_upper[:5]  # Truncar a 5 caracteres máximo
    
    def _get_state_name(self, state: str) -> Optional[str]:
        """Obtener nombre completo del estado"""
        if not state:
            return None
        
        state_upper = str(state).strip().upper()
        
        # Si es un código, devolver el nombre
        if state_upper in self.state_mapping:
            return self.state_mapping[state_upper]
        
        # Si ya es un nombre, devolverlo limpio
        return state_upper.title()
    
    def _map_status(self, es_valido: Any, phone_status: str) -> str:
        """Mapear campo es_valido a enum de status"""
        if phone_status in ["INVALID_FORMAT", "NOT_MOBILE"]:
            return phone_status
        
        if es_valido is None:
            return "UNKNOWN"
        
        # Convertir a boolean
        if isinstance(es_valido, str):
            es_valido = es_valido.lower() in ['true', '1', 'yes', 'sí']
        elif isinstance(es_valido, int):
            es_valido = bool(es_valido)
        
        return "VERIFIED" if es_valido else "UNKNOWN"
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parsear timestamp de SQLite"""
        if not timestamp_str:
            return datetime.now(timezone.utc)
        
        try:
            # Intentar varios formatos
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d",
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(str(timestamp_str), fmt)
                    return dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            
            # Si no se puede parsear, usar fecha actual
            return datetime.now(timezone.utc)
            
        except Exception:
            return datetime.now(timezone.utc)

class MigrationManager:
    """Gestor principal de migración de datos"""
    
    def __init__(self, 
                 sqlite_path: str = "numeros.db",
                 postgres_url: str = "postgresql://sms_user:sms_password@localhost:15432/sms_marketing",
                 batch_size: int = 10000):
        
        self.sqlite_path = sqlite_path
        self.postgres_url = postgres_url
        self.batch_size = batch_size
        self.transformer = DataTransformer()
        self.stats = MigrationStats()
        
        # Configuración de logging
        self.setup_logging()
    
    def setup_logging(self):
        """Configurar logging específico para migración"""
        migration_logger = logging.getLogger('migration')
        migration_logger.setLevel(logging.INFO)
        
        # Handler para archivo de migración
        file_handler = logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        migration_logger.addHandler(file_handler)
    
    async def migrate_all_data(self) -> bool:
        """
        Migrar todos los datos de SQLite a PostgreSQL
        
        Returns:
            True si la migración fue exitosa
        """
        logger.info("🚀 Iniciando migración completa de datos")
        
        try:
            # Inicializar estadísticas
            await self._initialize_migration_stats()
            
            # Crear conexión a PostgreSQL
            postgres_conn = await asyncpg.connect(self.postgres_url)
            
            try:
                # Migrar datos por lotes
                async for batch_result in self._process_batches(postgres_conn):
                    self._update_stats(batch_result)
                    self._log_progress()
                
                # Finalizar migración
                await self._finalize_migration(postgres_conn)
                
                logger.info("✅ Migración completada exitosamente")
                return True
                
            finally:
                await postgres_conn.close()
                
        except Exception as e:
            logger.error(f"❌ Error en migración: {e}")
            return False
    
    async def _initialize_migration_stats(self):
        """Inicializar estadísticas de migración"""
        # Contar registros totales en SQLite
        sqlite_conn = sqlite3.connect(self.sqlite_path)
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM numeros")
        self.stats.total_records = cursor.fetchone()[0]
        sqlite_conn.close()
        
        self.stats.total_batches = (self.stats.total_records + self.batch_size - 1) // self.batch_size
        self.stats.start_time = datetime.now()
        
        logger.info(f"📊 Total de registros: {self.stats.total_records:,}")
        logger.info(f"📦 Tamaño de lote: {self.batch_size:,}")
        logger.info(f"🔢 Total de lotes: {self.stats.total_batches:,}")
    
    async def _process_batches(self, postgres_conn: asyncpg.Connection) -> AsyncGenerator[Dict[str, Any], None]:
        """Procesar datos por lotes"""
        
        sqlite_conn = sqlite3.connect(self.sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        cursor = sqlite_conn.cursor()
        
        try:
            offset = 0
            batch_num = 0
            
            while offset < self.stats.total_records:
                batch_num += 1
                self.stats.current_batch = batch_num
                
                # Leer lote desde SQLite
                cursor.execute("""
                    SELECT * FROM numeros 
                    ORDER BY id 
                    LIMIT ? OFFSET ?
                """, (self.batch_size, offset))
                
                batch_records = [dict(row) for row in cursor.fetchall()]
                
                if not batch_records:
                    break
                
                # Procesar lote
                batch_result = await self._process_batch(postgres_conn, batch_records)
                yield batch_result
                
                offset += self.batch_size
                
        finally:
            sqlite_conn.close()
    
    async def _process_batch(self, postgres_conn: asyncpg.Connection, batch_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Procesar un lote específico de registros"""
        
        successful_records = []
        failed_records = []
        
        # Transformar registros
        for record in batch_records:
            transformation_result = self.transformer.transform_record(record)
            
            if transformation_result["success"]:
                successful_records.append(transformation_result["data"])
            else:
                failed_records.append({
                    "original": record,
                    "error": transformation_result["error"]
                })
        
        # Insertar registros exitosos en PostgreSQL
        if successful_records:
            try:
                await self._bulk_insert_contacts(postgres_conn, successful_records)
            except Exception as e:
                logger.error(f"Error en bulk insert: {e}")
                # Mover todos los registros exitosos a fallidos
                failed_records.extend([{"original": rec, "error": str(e)} for rec in successful_records])
                successful_records = []
        
        return {
            "batch_number": self.stats.current_batch,
            "total_records": len(batch_records),
            "successful_records": len(successful_records),
            "failed_records": len(failed_records),
            "failures": failed_records
        }
    
    async def _bulk_insert_contacts(self, postgres_conn: asyncpg.Connection, records: List[Dict[str, Any]]):
        """Insertar registros en lote en PostgreSQL"""
        
        # Preparar datos para inserción
        insert_data = []
        for record in records:
            insert_data.append((
                record["phone_e164"],
                record["phone_national"],
                record["phone_original"],
                record["full_name"],
                record["address"],
                record["neighborhood"],
                record["lada"],
                record["state_code"],
                record["state_name"],
                record["municipality"],
                record["city"],
                record["is_mobile"],
                record["operator"],
                record["status"],
                record["status_updated_at"],
                record["status_source"],
                record["send_count"],
                record["last_sent_at"],
                record["opt_out_at"],
                record["opt_out_method"],
                record["last_validated_at"],
                record["validation_attempts"],
                record["source"],
                record["import_batch_id"],
                record["created_at"],
                record["updated_at"]
            ))
        
        # Ejecutar inserción en lote
        await postgres_conn.executemany("""
            INSERT INTO contacts (
                phone_e164, phone_national, phone_original, full_name, address, neighborhood,
                lada, state_code, state_name, municipality, city, is_mobile, operator,
                status, status_updated_at, status_source, send_count, last_sent_at,
                opt_out_at, opt_out_method, last_validated_at, validation_attempts,
                source, import_batch_id, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, 
                     $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26)
            ON CONFLICT (phone_e164) DO UPDATE SET
                phone_national = EXCLUDED.phone_national,
                full_name = EXCLUDED.full_name,
                address = EXCLUDED.address,
                updated_at = EXCLUDED.updated_at
        """, insert_data)
    
    def _update_stats(self, batch_result: Dict[str, Any]):
        """Actualizar estadísticas de migración"""
        self.stats.processed_records += batch_result["total_records"]
        self.stats.successful_records += batch_result["successful_records"]
        self.stats.failed_records += batch_result["failed_records"]
        
        # Calcular velocidad
        elapsed_time = (datetime.now() - self.stats.start_time).total_seconds()
        if elapsed_time > 0:
            self.stats.records_per_second = self.stats.processed_records / elapsed_time
            
            # Estimar tiempo de finalización
            remaining_records = self.stats.total_records - self.stats.processed_records
            if self.stats.records_per_second > 0:
                remaining_seconds = remaining_records / self.stats.records_per_second
                self.stats.estimated_completion = datetime.now() + timedelta(seconds=remaining_seconds)
    
    def _log_progress(self):
        """Log del progreso actual"""
        progress_pct = (self.stats.processed_records / self.stats.total_records) * 100
        
        logger.info(f"📈 Progreso: {self.stats.processed_records:,}/{self.stats.total_records:,} "
                   f"({progress_pct:.1f}%) - Lote {self.stats.current_batch}/{self.stats.total_batches}")
        logger.info(f"⚡ Velocidad: {self.stats.records_per_second:.0f} registros/seg")
        
        if self.stats.estimated_completion:
            logger.info(f"⏰ Finalización estimada: {self.stats.estimated_completion.strftime('%H:%M:%S')}")
    
    async def _finalize_migration(self, postgres_conn: asyncpg.Connection):
        """Finalizar proceso de migración"""
        
        # Verificar conteos finales
        result = await postgres_conn.fetchrow("SELECT COUNT(*) FROM contacts")
        final_count = result[0]
        
        # Log de resumen final
        elapsed_time = datetime.now() - self.stats.start_time
        
        logger.info("="*60)
        logger.info("📊 RESUMEN FINAL DE MIGRACIÓN")
        logger.info("="*60)
        logger.info(f"📱 Registros procesados: {self.stats.processed_records:,}")
        logger.info(f"✅ Registros exitosos: {self.stats.successful_records:,}")
        logger.info(f"❌ Registros fallidos: {self.stats.failed_records:,}")
        logger.info(f"🎯 Registros en PostgreSQL: {final_count:,}")
        logger.info(f"⏱️ Tiempo total: {elapsed_time}")
        logger.info(f"⚡ Velocidad promedio: {self.stats.records_per_second:.0f} registros/seg")
        logger.info("="*60)

async def main():
    """Función principal para ejecutar migración"""
    print("🚀 Migration Manager - SMS Marketing Platform")
    print("="*60)
    
    # Crear manager de migración
    migration_manager = MigrationManager(
        sqlite_path="numeros.db",
        postgres_url="postgresql://sms_user:sms_password@localhost:15432/sms_marketing",
        batch_size=10000
    )
    
    # Ejecutar migración
    success = await migration_manager.migrate_all_data()
    
    if success:
        print("✅ Migración completada exitosamente!")
    else:
        print("❌ Error en la migración")

if __name__ == "__main__":
    asyncio.run(main())