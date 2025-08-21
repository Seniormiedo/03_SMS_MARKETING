#!/usr/bin/env python3
"""
Script para analizar la estructura de numeros.db y generar Estructura.md
Autor: SMS Marketing Platform
Fecha: 2025-01-27
"""

import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
from typing import Dict, List, Any, Optional
import json

class DatabaseAnalyzer:
    """Analizador de estructura de base de datos SQLite"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None
        self.analysis_results: Dict[str, Any] = {}
        
    def connect(self) -> bool:
        """Establece conexión con la base de datos"""
        try:
            self.connection = sqlite3.connect(self.db_path, timeout=30.0)
            self.connection.row_factory = sqlite3.Row
            return True
        except sqlite3.Error as e:
            print(f"❌ Error conectando a la base de datos: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Obtiene información general de la base de datos"""
        if not self.connection:
            return {}
            
        try:
            # Información del archivo
            file_stats = self.db_path.stat()
            
            # Información de SQLite
            cursor = self.connection.cursor()
            cursor.execute("PRAGMA database_list")
            db_info = cursor.fetchall()
            
            cursor.execute("PRAGMA user_version")
            user_version = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA schema_version")
            schema_version = cursor.fetchone()[0]
            
            return {
                "archivo": {
                    "nombre": self.db_path.name,
                    "tamaño_bytes": file_stats.st_size,
                    "tamaño_mb": round(file_stats.st_size / (1024 * 1024), 2),
                    "tamaño_gb": round(file_stats.st_size / (1024 * 1024 * 1024), 2),
                    "fecha_modificacion": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                    "fecha_creacion": datetime.fromtimestamp(file_stats.st_ctime).isoformat()
                },
                "sqlite": {
                    "version_usuario": user_version,
                    "version_schema": schema_version,
                    "bases_datos": [dict(row) for row in db_info]
                }
            }
        except Exception as e:
            print(f"⚠️  Error obteniendo información general: {e}")
            return {}
    
    def get_tables_info(self) -> List[Dict[str, Any]]:
        """Obtiene información de todas las tablas"""
        if not self.connection:
            return []
            
        try:
            cursor = self.connection.cursor()
            
            # Obtener lista de tablas
            cursor.execute("""
                SELECT name, type, sql 
                FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            
            tables = []
            for row in cursor.fetchall():
                table_name = row['name']
                table_info = {
                    "nombre": table_name,
                    "tipo": row['type'],
                    "sql_creacion": row['sql'],
                    "columnas": self.get_table_columns(table_name),
                    "indices": self.get_table_indexes(table_name),
                    "estadisticas": self.get_table_stats(table_name)
                }
                tables.append(table_info)
                
            return tables
        except Exception as e:
            print(f"⚠️  Error obteniendo información de tablas: {e}")
            return []
    
    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Obtiene información de columnas de una tabla"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    "id": row['cid'],
                    "nombre": row['name'],
                    "tipo": row['type'],
                    "no_nulo": bool(row['notnull']),
                    "valor_defecto": row['dflt_value'],
                    "clave_primaria": bool(row['pk'])
                })
            return columns
        except Exception as e:
            print(f"⚠️  Error obteniendo columnas de {table_name}: {e}")
            return []
    
    def get_table_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Obtiene información de índices de una tabla"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA index_list({table_name})")
            
            indexes = []
            for row in cursor.fetchall():
                index_name = row['name']
                
                # Obtener columnas del índice
                cursor.execute(f"PRAGMA index_info({index_name})")
                index_columns = [col['name'] for col in cursor.fetchall()]
                
                indexes.append({
                    "nombre": index_name,
                    "unico": bool(row['unique']),
                    "columnas": index_columns,
                    "origen": row['origin']
                })
            return indexes
        except Exception as e:
            print(f"⚠️  Error obteniendo índices de {table_name}: {e}")
            return []
    
    def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """Obtiene estadísticas de una tabla"""
        try:
            cursor = self.connection.cursor()
            
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
            total_rows = cursor.fetchone()['total']
            
            stats = {
                "total_registros": total_rows,
                "muestra_datos": []
            }
            
            # Obtener muestra de datos (primeros 5 registros)
            if total_rows > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                sample_rows = cursor.fetchall()
                stats["muestra_datos"] = [dict(row) for row in sample_rows]
            
            return stats
        except Exception as e:
            print(f"⚠️  Error obteniendo estadísticas de {table_name}: {e}")
            return {"total_registros": 0, "muestra_datos": []}
    
    def analyze_data_patterns(self, table_name: str, column_name: str, sample_size: int = 1000) -> Dict[str, Any]:
        """Analiza patrones en los datos de una columna específica"""
        try:
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
                return {"patron": "sin_datos"}
            
            # Analizar patrones
            patterns = {
                "total_valores": len(values),
                "valores_unicos": len(set(values)),
                "longitud_promedio": sum(len(str(v)) for v in values) / len(values) if values else 0,
                "tipos_detectados": list(set(type(v).__name__ for v in values)),
                "muestra_valores": values[:10]
            }
            
            # Detectar si son números de teléfono
            if column_name.lower() in ['numero', 'telefono', 'phone', 'celular', 'movil']:
                phone_patterns = self.analyze_phone_patterns(values)
                patterns.update(phone_patterns)
            
            return patterns
        except Exception as e:
            print(f"⚠️  Error analizando patrones de {table_name}.{column_name}: {e}")
            return {"error": str(e)}
    
    def analyze_phone_patterns(self, values: List[Any]) -> Dict[str, Any]:
        """Analiza patrones específicos de números telefónicos"""
        import re
        
        patterns = {
            "formatos_detectados": {},
            "longitudes": {},
            "prefijos_comunes": {},
            "numeros_validos": 0,
            "numeros_invalidos": 0
        }
        
        for value in values:
            str_value = str(value).strip()
            
            # Analizar longitud
            length = len(str_value)
            patterns["longitudes"][length] = patterns["longitudes"].get(length, 0) + 1
            
            # Detectar formato
            if re.match(r'^\+\d+$', str_value):
                fmt = "internacional_plus"
            elif re.match(r'^\d{10}$', str_value):
                fmt = "nacional_10_digitos"
            elif re.match(r'^\d{8,15}$', str_value):
                fmt = "numerico_puro"
            elif re.match(r'^[\d\s\-\(\)]+$', str_value):
                fmt = "con_separadores"
            else:
                fmt = "formato_desconocido"
            
            patterns["formatos_detectados"][fmt] = patterns["formatos_detectados"].get(fmt, 0) + 1
            
            # Analizar prefijo (primeros 2-3 dígitos)
            digits_only = re.sub(r'\D', '', str_value)
            if len(digits_only) >= 3:
                prefix = digits_only[:3]
                patterns["prefijos_comunes"][prefix] = patterns["prefijos_comunes"].get(prefix, 0) + 1
            
            # Validar si parece un número válido
            if len(digits_only) >= 8 and len(digits_only) <= 15:
                patterns["numeros_validos"] += 1
            else:
                patterns["numeros_invalidos"] += 1
        
        return patterns
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """Ejecuta análisis completo de la base de datos"""
        print("🔍 Iniciando análisis de la base de datos...")
        
        if not self.connect():
            return {"error": "No se pudo conectar a la base de datos"}
        
        try:
            # Información general
            print("📊 Obteniendo información general...")
            db_info = self.get_database_info()
            
            # Información de tablas
            print("📋 Analizando tablas...")
            tables_info = self.get_tables_info()
            
            # Análisis de patrones en columnas sospechosas de contener teléfonos
            print("📱 Analizando patrones de datos...")
            pattern_analysis = {}
            
            for table in tables_info:
                table_name = table["nombre"]
                for column in table["columnas"]:
                    column_name = column["nombre"]
                    
                    # Analizar columnas que podrían contener números de teléfono
                    if any(keyword in column_name.lower() for keyword in 
                           ['numero', 'telefono', 'phone', 'celular', 'movil', 'contact']):
                        print(f"  🔎 Analizando {table_name}.{column_name}...")
                        pattern_analysis[f"{table_name}.{column_name}"] = self.analyze_data_patterns(
                            table_name, column_name
                        )
            
            results = {
                "timestamp": datetime.now().isoformat(),
                "informacion_general": db_info,
                "tablas": tables_info,
                "analisis_patrones": pattern_analysis
            }
            
            self.analysis_results = results
            print("✅ Análisis completado exitosamente")
            return results
            
        except Exception as e:
            print(f"❌ Error durante el análisis: {e}")
            return {"error": str(e)}
        finally:
            if self.connection:
                self.connection.close()
    
    def generate_markdown_report(self, output_file: str = "Estructura.md") -> bool:
        """Genera reporte en formato Markdown"""
        try:
            if not self.analysis_results:
                print("❌ No hay resultados de análisis disponibles")
                return False
            
            results = self.analysis_results
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# 📊 Análisis de Estructura - SMS Marketing Database\n\n")
                f.write(f"**Fecha de análisis:** {results['timestamp']}\n\n")
                
                # Información general
                if 'informacion_general' in results:
                    info = results['informacion_general']
                    f.write("## 📁 Información General del Archivo\n\n")
                    
                    if 'archivo' in info:
                        archivo = info['archivo']
                        f.write(f"- **Nombre:** `{archivo.get('nombre', 'N/A')}`\n")
                        f.write(f"- **Tamaño:** {archivo.get('tamaño_gb', 0):.2f} GB ({archivo.get('tamaño_mb', 0):.2f} MB)\n")
                        f.write(f"- **Última modificación:** {archivo.get('fecha_modificacion', 'N/A')}\n")
                        f.write(f"- **Fecha de creación:** {archivo.get('fecha_creacion', 'N/A')}\n\n")
                
                # Información de tablas
                if 'tablas' in results:
                    f.write("## 📋 Estructura de Tablas\n\n")
                    
                    for table in results['tablas']:
                        f.write(f"### 🗂️ Tabla: `{table['nombre']}`\n\n")
                        
                        # Estadísticas básicas
                        stats = table.get('estadisticas', {})
                        f.write(f"**Registros totales:** {stats.get('total_registros', 0):,}\n\n")
                        
                        # Columnas
                        f.write("#### Columnas\n\n")
                        f.write("| Nombre | Tipo | Nulo | Clave Primaria | Valor Defecto |\n")
                        f.write("|--------|------|------|----------------|---------------|\n")
                        
                        for col in table.get('columnas', []):
                            f.write(f"| `{col['nombre']}` | {col['tipo']} | "
                                   f"{'❌' if col['no_nulo'] else '✅'} | "
                                   f"{'🔑' if col['clave_primaria'] else '➖'} | "
                                   f"{col['valor_defecto'] or '➖'} |\n")
                        
                        f.write("\n")
                        
                        # Índices
                        if table.get('indices'):
                            f.write("#### Índices\n\n")
                            for idx in table['indices']:
                                f.write(f"- **{idx['nombre']}**: {', '.join(idx['columnas'])} "
                                       f"{'(ÚNICO)' if idx['unico'] else ''}\n")
                            f.write("\n")
                        
                        # Muestra de datos
                        sample_data = stats.get('muestra_datos', [])
                        if sample_data:
                            f.write("#### Muestra de Datos (primeros 5 registros)\n\n")
                            f.write("```json\n")
                            f.write(json.dumps(sample_data, indent=2, ensure_ascii=False, default=str))
                            f.write("\n```\n\n")
                        
                        # SQL de creación
                        if table.get('sql_creacion'):
                            f.write("#### SQL de Creación\n\n")
                            f.write("```sql\n")
                            f.write(table['sql_creacion'])
                            f.write("\n```\n\n")
                        
                        f.write("---\n\n")
                
                # Análisis de patrones
                if 'analisis_patrones' in results:
                    f.write("## 📱 Análisis de Patrones de Datos\n\n")
                    
                    for column_path, analysis in results['analisis_patrones'].items():
                        if 'error' in analysis:
                            continue
                            
                        f.write(f"### 🔍 Columna: `{column_path}`\n\n")
                        
                        f.write(f"- **Total valores:** {analysis.get('total_valores', 0):,}\n")
                        f.write(f"- **Valores únicos:** {analysis.get('valores_unicos', 0):,}\n")
                        f.write(f"- **Longitud promedio:** {analysis.get('longitud_promedio', 0):.1f} caracteres\n")
                        f.write(f"- **Tipos detectados:** {', '.join(analysis.get('tipos_detectados', []))}\n\n")
                        
                        # Análisis específico de teléfonos
                        if 'formatos_detectados' in analysis:
                            f.write("#### 📞 Análisis de Números Telefónicos\n\n")
                            
                            f.write("**Formatos detectados:**\n")
                            for fmt, count in analysis['formatos_detectados'].items():
                                percentage = (count / analysis['total_valores']) * 100
                                f.write(f"- `{fmt}`: {count:,} ({percentage:.1f}%)\n")
                            f.write("\n")
                            
                            f.write("**Distribución por longitud:**\n")
                            for length, count in sorted(analysis['longitudes'].items()):
                                percentage = (count / analysis['total_valores']) * 100
                                f.write(f"- {length} dígitos: {count:,} ({percentage:.1f}%)\n")
                            f.write("\n")
                            
                            f.write("**Prefijos más comunes (top 10):**\n")
                            sorted_prefixes = sorted(analysis['prefijos_comunes'].items(), 
                                                   key=lambda x: x[1], reverse=True)[:10]
                            for prefix, count in sorted_prefixes:
                                percentage = (count / analysis['total_valores']) * 100
                                f.write(f"- `{prefix}`: {count:,} ({percentage:.1f}%)\n")
                            f.write("\n")
                            
                            valid_pct = (analysis['numeros_validos'] / analysis['total_valores']) * 100
                            f.write(f"**Validez:** {analysis['numeros_validos']:,} válidos ({valid_pct:.1f}%), "
                                   f"{analysis['numeros_invalidos']:,} inválidos\n\n")
                        
                        # Muestra de valores
                        if 'muestra_valores' in analysis:
                            f.write("#### Muestra de Valores\n\n")
                            f.write("```\n")
                            for value in analysis['muestra_valores'][:10]:
                                f.write(f"{value}\n")
                            f.write("```\n\n")
                        
                        f.write("---\n\n")
                
                # Recomendaciones
                f.write("## 💡 Recomendaciones para Migración\n\n")
                f.write("### 🔄 Estrategia de Migración\n\n")
                f.write("1. **Limpieza de datos:**\n")
                f.write("   - Normalizar formatos de números telefónicos\n")
                f.write("   - Eliminar duplicados\n")
                f.write("   - Validar números según estándares internacionales\n\n")
                
                f.write("2. **Optimización:**\n")
                f.write("   - Crear índices en columnas de búsqueda frecuente\n")
                f.write("   - Particionar tablas grandes por fecha o región\n")
                f.write("   - Implementar compresión para reducir espacio\n\n")
                
                f.write("3. **Seguridad:**\n")
                f.write("   - Cifrar números telefónicos sensibles\n")
                f.write("   - Implementar auditoría de accesos\n")
                f.write("   - Configurar backups automáticos\n\n")
                
                f.write("### 🏗️ Arquitectura Recomendada\n\n")
                f.write("```\n")
                f.write("PostgreSQL (Principal)\n")
                f.write("├── contacts (números normalizados)\n")
                f.write("├── campaigns (campañas de marketing)\n")
                f.write("├── messages (historial de mensajes)\n")
                f.write("├── opt_outs (lista de exclusión)\n")
                f.write("└── analytics (métricas y reportes)\n")
                f.write("\n")
                f.write("Redis (Cache/Queue)\n")
                f.write("├── session_cache\n")
                f.write("├── message_queue\n")
                f.write("└── rate_limiting\n")
                f.write("```\n\n")
                
                f.write("---\n\n")
                f.write("*Reporte generado automáticamente por SMS Marketing Platform Analyzer*\n")
            
            print(f"✅ Reporte generado exitosamente: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error generando reporte: {e}")
            return False

def main():
    """Función principal"""
    print("🚀 SMS Marketing Database Analyzer")
    print("=" * 50)
    
    db_file = "numeros.db"
    
    if not os.path.exists(db_file):
        print(f"❌ No se encontró el archivo: {db_file}")
        sys.exit(1)
    
    # Crear analizador
    analyzer = DatabaseAnalyzer(db_file)
    
    # Ejecutar análisis
    results = analyzer.run_full_analysis()
    
    if 'error' in results:
        print(f"❌ Error en el análisis: {results['error']}")
        sys.exit(1)
    
    # Generar reporte
    if analyzer.generate_markdown_report():
        print("\n✅ Análisis completado exitosamente!")
        print("📄 Consulta el archivo 'Estructura.md' para ver los resultados detallados.")
    else:
        print("❌ Error generando el reporte")
        sys.exit(1)

if __name__ == "__main__":
    main()