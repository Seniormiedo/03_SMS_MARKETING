#!/usr/bin/env python3
"""
Análisis detallado de la base de datos fuente (numeros.db)
para mapear campos y planificar migración
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class SourceDatabaseAnalyzer:
    """Analizador de la base de datos SQLite fuente"""
    
    def __init__(self, db_path: str = "numeros.db"):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        
    def connect(self):
        """Conectar a la base de datos SQLite"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            print(f"✅ Conectado a {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            return False
    
    def analyze_table_structure(self, table_name: str) -> Dict[str, Any]:
        """Analizar estructura de una tabla específica"""
        if not self.connection:
            return {}
            
        cursor = self.connection.cursor()
        
        # Información de columnas
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append({
                "name": row['name'],
                "type": row['type'],
                "nullable": not bool(row['notnull']),
                "primary_key": bool(row['pk']),
                "default_value": row['dflt_value']
            })
        
        # Conteo de registros
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_records = cursor.fetchone()[0]
        
        # Muestra de datos
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
        sample_data = [dict(row) for row in cursor.fetchall()]
        
        return {
            "table_name": table_name,
            "columns": columns,
            "total_records": total_records,
            "sample_data": sample_data
        }
    
    def analyze_data_patterns(self, table_name: str, column_name: str, sample_size: int = 1000) -> Dict[str, Any]:
        """Analizar patrones de datos en una columna"""
        if not self.connection:
            return {}
            
        cursor = self.connection.cursor()
        
        # Obtener muestra de datos
        cursor.execute(f"""
            SELECT {column_name} 
            FROM {table_name} 
            WHERE {column_name} IS NOT NULL 
            LIMIT {sample_size}
        """)
        
        values = [row[0] for row in cursor.fetchall()]
        
        if not values:
            return {"error": "No data found"}
        
        # Análisis básico
        analysis = {
            "column_name": column_name,
            "total_sample": len(values),
            "unique_values": len(set(values)),
            "null_count": 0,  # Ya filtrados
            "data_types": list(set(type(v).__name__ for v in values)),
            "sample_values": values[:10]
        }
        
        # Análisis específico por tipo de columna
        if column_name in ['numero', 'campo1_original']:
            analysis.update(self._analyze_phone_patterns(values))
        elif column_name in ['nombre']:
            analysis.update(self._analyze_name_patterns(values))
        elif column_name in ['direccion']:
            analysis.update(self._analyze_address_patterns(values))
        elif column_name in ['lada']:
            analysis.update(self._analyze_lada_patterns(values))
        elif column_name in ['estado_cof', 'estado_sep']:
            analysis.update(self._analyze_state_patterns(values))
        
        return analysis
    
    def _analyze_phone_patterns(self, values: List[str]) -> Dict[str, Any]:
        """Análisis específico de números telefónicos"""
        import re
        
        patterns = {
            "lengths": {},
            "formats": {},
            "prefixes": {},
            "valid_count": 0,
            "invalid_count": 0
        }
        
        for value in values:
            if not value:
                continue
                
            str_value = str(value).strip()
            length = len(str_value)
            
            # Contar longitudes
            patterns["lengths"][length] = patterns["lengths"].get(length, 0) + 1
            
            # Detectar formatos
            if re.match(r'^\+52\d{10}$', str_value):
                fmt = "e164_format"
            elif re.match(r'^\d{10}$', str_value):
                fmt = "national_10_digits"
            elif re.match(r'^\d{8}$', str_value):
                fmt = "local_8_digits"
            elif re.match(r'^[\d\s\-\(\)]+$', str_value):
                fmt = "formatted_with_separators"
            else:
                fmt = "unknown_format"
            
            patterns["formats"][fmt] = patterns["formats"].get(fmt, 0) + 1
            
            # Analizar prefijos (primeros 3 dígitos)
            digits_only = re.sub(r'\D', '', str_value)
            if len(digits_only) >= 3:
                prefix = digits_only[:3]
                patterns["prefixes"][prefix] = patterns["prefixes"].get(prefix, 0) + 1
            
            # Validar formato mexicano
            if len(digits_only) == 10 and digits_only.isdigit():
                patterns["valid_count"] += 1
            else:
                patterns["invalid_count"] += 1
        
        return {"phone_analysis": patterns}
    
    def _analyze_name_patterns(self, values: List[str]) -> Dict[str, Any]:
        """Análisis de patrones de nombres"""
        patterns = {
            "avg_length": sum(len(str(v)) for v in values if v) / len(values),
            "word_count": {},
            "has_numbers": 0,
            "all_caps": 0,
            "mixed_case": 0
        }
        
        for value in values:
            if not value:
                continue
                
            str_value = str(value).strip()
            words = len(str_value.split())
            patterns["word_count"][words] = patterns["word_count"].get(words, 0) + 1
            
            if any(c.isdigit() for c in str_value):
                patterns["has_numbers"] += 1
            if str_value.isupper():
                patterns["all_caps"] += 1
            elif not str_value.isupper() and not str_value.islower():
                patterns["mixed_case"] += 1
        
        return {"name_analysis": patterns}
    
    def _analyze_address_patterns(self, values: List[str]) -> Dict[str, Any]:
        """Análisis de patrones de direcciones"""
        patterns = {
            "avg_length": sum(len(str(v)) for v in values if v) / len(values),
            "has_numbers": 0,
            "common_words": {}
        }
        
        common_address_words = ['CALLE', 'AV', 'AVENIDA', 'BLVD', 'COL', 'COLONIA', 'NUM', '#']
        
        for value in values:
            if not value:
                continue
                
            str_value = str(value).upper().strip()
            
            if any(c.isdigit() for c in str_value):
                patterns["has_numbers"] += 1
            
            for word in common_address_words:
                if word in str_value:
                    patterns["common_words"][word] = patterns["common_words"].get(word, 0) + 1
        
        return {"address_analysis": patterns}
    
    def _analyze_lada_patterns(self, values: List[str]) -> Dict[str, Any]:
        """Análisis de códigos LADA"""
        patterns = {
            "lengths": {},
            "frequency": {},
            "valid_ladas": 0
        }
        
        for value in values:
            if not value:
                continue
                
            str_value = str(value).strip()
            length = len(str_value)
            patterns["lengths"][length] = patterns["lengths"].get(length, 0) + 1
            patterns["frequency"][str_value] = patterns["frequency"].get(str_value, 0) + 1
            
            # Validar LADA mexicana (2-3 dígitos)
            if length in [2, 3] and str_value.isdigit():
                patterns["valid_ladas"] += 1
        
        return {"lada_analysis": patterns}
    
    def _analyze_state_patterns(self, values: List[str]) -> Dict[str, Any]:
        """Análisis de patrones de estados"""
        patterns = {
            "frequency": {},
            "lengths": {},
            "abbreviations": 0,
            "full_names": 0
        }
        
        for value in values:
            if not value:
                continue
                
            str_value = str(value).strip()
            length = len(str_value)
            
            patterns["frequency"][str_value] = patterns["frequency"].get(str_value, 0) + 1
            patterns["lengths"][length] = patterns["lengths"].get(length, 0) + 1
            
            if length <= 5:
                patterns["abbreviations"] += 1
            else:
                patterns["full_names"] += 1
        
        return {"state_analysis": patterns}
    
    def create_field_mapping(self) -> Dict[str, Dict[str, Any]]:
        """Crear mapeo de campos SQLite → PostgreSQL"""
        
        mapping = {
            # Campos de identificación
            "id": {
                "target_field": "id",
                "target_type": "SERIAL PRIMARY KEY",
                "transformation": "direct_copy",
                "notes": "Auto-increment ID"
            },
            
            # Campos de números telefónicos
            "numero": {
                "target_field": "phone_national",
                "target_type": "VARCHAR(12)",
                "transformation": "normalize_phone_national",
                "notes": "Normalizar a 10 dígitos sin formato"
            },
            "campo1_original": {
                "target_field": "phone_original",
                "target_type": "VARCHAR(20)",
                "transformation": "direct_copy",
                "notes": "Preservar número original como vino"
            },
            
            # Información personal
            "nombre": {
                "target_field": "full_name",
                "target_type": "VARCHAR(255)",
                "transformation": "clean_name",
                "notes": "Limpiar y normalizar nombre"
            },
            
            # Información geográfica
            "direccion": {
                "target_field": "address",
                "target_type": "TEXT",
                "transformation": "clean_address",
                "notes": "Limpiar dirección"
            },
            "colonia": {
                "target_field": "neighborhood",
                "target_type": "VARCHAR(100)",
                "transformation": "clean_text",
                "notes": "Normalizar colonia"
            },
            "municipio_cof": {
                "target_field": "municipality",
                "target_type": "VARCHAR(100)",
                "transformation": "clean_text",
                "notes": "Usar municipio_cof como principal"
            },
            "estado_cof": {
                "target_field": "state_code",
                "target_type": "VARCHAR(5)",
                "transformation": "normalize_state_code",
                "notes": "Normalizar código de estado"
            },
            "lada": {
                "target_field": "lada",
                "target_type": "VARCHAR(3)",
                "transformation": "validate_lada",
                "notes": "Validar y normalizar LADA"
            },
            "ciudad_por_lada": {
                "target_field": "city",
                "target_type": "VARCHAR(100)",
                "transformation": "clean_text",
                "notes": "Ciudad según LADA"
            },
            
            # Campos de control
            "es_valido": {
                "target_field": "status",
                "target_type": "contactstatus",
                "transformation": "map_to_status_enum",
                "notes": "Mapear boolean a enum de status"
            },
            "fecha_migracion": {
                "target_field": "created_at",
                "target_type": "TIMESTAMP WITH TIME ZONE",
                "transformation": "parse_timestamp",
                "notes": "Convertir a timestamp con zona"
            },
            
            # Campos nuevos (no en SQLite)
            "phone_e164": {
                "source_field": "numero",
                "target_field": "phone_e164",
                "target_type": "VARCHAR(15)",
                "transformation": "generate_e164",
                "notes": "Generar formato E.164 desde número nacional"
            },
            "is_mobile": {
                "source_field": "numero",
                "target_field": "is_mobile",
                "target_type": "BOOLEAN",
                "transformation": "detect_mobile",
                "notes": "Detectar si es móvil según LADA y prefijo"
            },
            "source": {
                "target_field": "source",
                "target_type": "VARCHAR(50)",
                "transformation": "set_constant",
                "constant_value": "TELCEL2022",
                "notes": "Marcar origen de datos"
            }
        }
        
        return mapping
    
    def generate_migration_report(self, output_file: str = "migration_analysis.json"):
        """Generar reporte completo de análisis para migración"""
        
        if not self.connect():
            return False
        
        print("🔍 Analizando estructura de base de datos fuente...")
        
        # Análisis de tablas
        tables_analysis = {}
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        
        for table_row in cursor.fetchall():
            table_name = table_row[0]
            print(f"  📋 Analizando tabla: {table_name}")
            tables_analysis[table_name] = self.analyze_table_structure(table_name)
        
        # Análisis detallado de la tabla principal 'numeros'
        if 'numeros' in tables_analysis:
            print("  🔎 Análisis detallado de columnas...")
            column_analysis = {}
            
            for column in tables_analysis['numeros']['columns']:
                col_name = column['name']
                print(f"    📊 Analizando columna: {col_name}")
                column_analysis[col_name] = self.analyze_data_patterns('numeros', col_name)
        
        # Crear mapeo de campos
        print("  🗺️  Creando mapeo de campos...")
        field_mapping = self.create_field_mapping()
        
        # Generar reporte completo
        report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "source_database": self.db_path,
            "tables_analysis": tables_analysis,
            "column_patterns": column_analysis if 'numeros' in tables_analysis else {},
            "field_mapping": field_mapping,
            "migration_recommendations": {
                "batch_size": 10000,
                "estimated_time_hours": round(tables_analysis.get('numeros', {}).get('total_records', 0) / 100000, 2),
                "memory_requirements_gb": 8,
                "disk_space_gb": round(tables_analysis.get('numeros', {}).get('total_records', 0) * 0.5 / 1000000, 2)
            }
        }
        
        # Guardar reporte
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Reporte generado: {output_file}")
        
        # Mostrar resumen
        self._print_summary(report)
        
        self.connection.close()
        return True
    
    def _print_summary(self, report: Dict[str, Any]):
        """Imprimir resumen del análisis"""
        print("\n" + "="*60)
        print("📊 RESUMEN DEL ANÁLISIS DE MIGRACIÓN")
        print("="*60)
        
        if 'numeros' in report['tables_analysis']:
            numeros_info = report['tables_analysis']['numeros']
            print(f"📱 Total de registros: {numeros_info['total_records']:,}")
            print(f"📋 Columnas en tabla numeros: {len(numeros_info['columns'])}")
        
        print(f"🗺️  Campos mapeados: {len(report['field_mapping'])}")
        
        recommendations = report['migration_recommendations']
        print(f"⏱️  Tiempo estimado: {recommendations['estimated_time_hours']} horas")
        print(f"💾 Memoria requerida: {recommendations['memory_requirements_gb']} GB")
        print(f"💿 Espacio en disco: {recommendations['disk_space_gb']} GB")
        print("="*60)

def main():
    """Función principal"""
    print("🚀 Analizador de Base de Datos Fuente - SMS Marketing")
    print("="*60)
    
    analyzer = SourceDatabaseAnalyzer("numeros.db")
    
    if analyzer.generate_migration_report():
        print("\n✅ Análisis completado exitosamente!")
    else:
        print("\n❌ Error en el análisis")

if __name__ == "__main__":
    main()