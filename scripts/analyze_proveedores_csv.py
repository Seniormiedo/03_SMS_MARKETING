#!/usr/bin/env python3
"""
Script para analizar la estructura del archivo Proveedores_05_08_2025.csv
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path

def analyze_proveedores_csv():
    """Analizar la estructura del CSV de proveedores"""
    
    csv_path = Path("data/Proveedores_05_08_2025.csv")
    
    if not csv_path.exists():
        print(f"❌ Error: Archivo no encontrado: {csv_path}")
        return
    
    print("📊 ANÁLISIS DEL ARCHIVO PROVEEDORES_05_08_2025.CSV")
    print("=" * 60)
    
    try:
        # 1. Información básica del archivo
        file_size = csv_path.stat().st_size / (1024 * 1024)  # MB
        print(f"📁 Archivo: {csv_path.name}")
        print(f"📏 Tamaño: {file_size:.2f} MB")
        
        # 2. Leer las primeras líneas para detectar estructura
        print("\n🔍 DETECTANDO ESTRUCTURA...")
        
        # Intentar diferentes encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        df_sample = None
        encoding_used = None
        
        for encoding in encodings:
            try:
                df_sample = pd.read_csv(csv_path, nrows=20, encoding=encoding)
                encoding_used = encoding
                print(f"✅ Encoding detectado: {encoding}")
                break
            except Exception as e:
                print(f"❌ Error con encoding {encoding}: {str(e)[:50]}...")
                continue
        
        if df_sample is None:
            print("❌ No se pudo leer el archivo con ningún encoding")
            return
        
        # 3. Análisis de estructura
        print(f"\n📋 ESTRUCTURA INICIAL:")
        print(f"  • Columnas detectadas: {len(df_sample.columns)}")
        print(f"  • Columnas: {list(df_sample.columns)}")
        
        # 4. Mostrar primeras filas
        print(f"\n📄 PRIMERAS 10 FILAS:")
        print(df_sample.head(10).to_string())
        
        # 5. Leer archivo completo para análisis detallado
        print(f"\n🔄 CARGANDO ARCHIVO COMPLETO...")
        df = pd.read_csv(csv_path, encoding=encoding_used)
        
        print(f"📊 ESTADÍSTICAS GENERALES:")
        print(f"  • Total filas: {len(df):,}")
        print(f"  • Total columnas: {len(df.columns)}")
        print(f"  • Memoria usada: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        
        # 6. Análisis de cada columna
        print(f"\n📈 ANÁLISIS POR COLUMNA:")
        for col in df.columns:
            non_null = df[col].count()
            null_count = len(df) - non_null
            unique_values = df[col].nunique()
            
            print(f"  • {col}:")
            print(f"    - Valores no nulos: {non_null:,} ({non_null/len(df)*100:.1f}%)")
            print(f"    - Valores nulos: {null_count:,} ({null_count/len(df)*100:.1f}%)")
            print(f"    - Valores únicos: {unique_values:,}")
            
            # Mostrar algunos valores de ejemplo
            sample_values = df[col].dropna().head(5).tolist()
            print(f"    - Ejemplos: {sample_values}")
            print()
        
        # 7. Detectar si hay números telefónicos
        print(f"🔍 DETECCIÓN DE NÚMEROS TELEFÓNICOS:")
        phone_patterns = []
        
        for col in df.columns:
            sample_values = df[col].dropna().astype(str).head(100)
            
            # Buscar patrones de teléfono
            phone_like = 0
            for value in sample_values:
                # Limpiar y verificar si parece un teléfono
                clean_value = re.sub(r'[^\d]', '', str(value))
                if len(clean_value) >= 10 and len(clean_value) <= 15 and clean_value.isdigit():
                    phone_like += 1
            
            phone_percentage = (phone_like / len(sample_values)) * 100 if len(sample_values) > 0 else 0
            
            if phone_percentage > 50:  # Si más del 50% parecen teléfonos
                phone_patterns.append({
                    'column': col,
                    'phone_like_percentage': phone_percentage,
                    'sample_values': sample_values.head(3).tolist()
                })
                print(f"  ✅ {col}: {phone_percentage:.1f}% parecen teléfonos")
                print(f"     Ejemplos: {sample_values.head(3).tolist()}")
        
        # 8. Detectar información geográfica
        print(f"\n🗺️ DETECCIÓN DE INFORMACIÓN GEOGRÁFICA:")
        geo_columns = []
        
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['estado', 'state', 'ciudad', 'city', 'lada', 'municipio', 'region']):
                unique_count = df[col].nunique()
                sample_values = df[col].dropna().head(5).tolist()
                geo_columns.append({
                    'column': col,
                    'unique_count': unique_count,
                    'sample_values': sample_values
                })
                print(f"  ✅ {col}: {unique_count} valores únicos")
                print(f"     Ejemplos: {sample_values}")
        
        # 9. Detectar información de operadores/proveedores
        print(f"\n📱 DETECCIÓN DE OPERADORES/PROVEEDORES:")
        operator_columns = []
        
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['operador', 'operator', 'proveedor', 'provider', 'carrier', 'company']):
                unique_count = df[col].nunique()
                sample_values = df[col].dropna().head(10).tolist()
                operator_columns.append({
                    'column': col,
                    'unique_count': unique_count,
                    'sample_values': sample_values
                })
                print(f"  ✅ {col}: {unique_count} valores únicos")
                print(f"     Ejemplos: {sample_values}")
        
        # 10. Análisis de duplicados
        print(f"\n🔄 ANÁLISIS DE DUPLICADOS:")
        if phone_patterns:
            main_phone_col = phone_patterns[0]['column']
            duplicates = df.duplicated(subset=[main_phone_col]).sum()
            print(f"  • Duplicados en {main_phone_col}: {duplicates:,}")
            
            # Verificar duplicados en combinación de columnas
            if len(df.columns) > 1:
                total_duplicates = df.duplicated().sum()
                print(f"  • Duplicados totales (todas las columnas): {total_duplicates:,}")
        
        # 11. Resumen y recomendaciones
        print(f"\n📋 RESUMEN DEL ANÁLISIS:")
        print(f"  • Archivo: {csv_path.name}")
        print(f"  • Registros: {len(df):,}")
        print(f"  • Columnas: {len(df.columns)}")
        print(f"  • Encoding: {encoding_used}")
        print(f"  • Columnas con teléfonos: {len(phone_patterns)}")
        print(f"  • Columnas geográficas: {len(geo_columns)}")
        print(f"  • Columnas de operadores: {len(operator_columns)}")
        
        return {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': list(df.columns),
            'encoding': encoding_used,
            'phone_columns': phone_patterns,
            'geo_columns': geo_columns,
            'operator_columns': operator_columns,
            'file_size_mb': file_size,
            'dataframe': df  # Para uso posterior
        }
        
    except Exception as e:
        print(f"❌ Error durante el análisis: {e}")
        return None

if __name__ == "__main__":
    result = analyze_proveedores_csv()
    
    if result:
        print(f"\n🎯 ANÁLISIS COMPLETADO EXITOSAMENTE")
        print(f"📊 Datos listos para integración con base de datos")
    else:
        print(f"\n❌ ANÁLISIS FALLÓ")