#!/usr/bin/env python3
"""
Análisis detallado y corrección del archivo Proveedores_05_08_2025.csv
"""

import pandas as pd
import re
from pathlib import Path

def analyze_detailed():
    """Análisis detallado con corrección de columnas"""
    
    csv_path = Path("data/Proveedores_05_08_2025.csv")
    
    print("🔍 ANÁLISIS DETALLADO DEL ARCHIVO PROVEEDORES")
    print("=" * 60)
    
    # Leer las primeras líneas como texto para entender la estructura real
    with open(csv_path, 'r', encoding='utf-8') as f:
        lines = [f.readline().strip() for _ in range(10)]
    
    print("📄 PRIMERAS 10 LÍNEAS RAW:")
    for i, line in enumerate(lines, 1):
        print(f"{i:2d}: {line}")
    
    print(f"\n🔍 ANÁLISIS DE SEPARADORES:")
    separators = [',', ';', '\t', '|']
    for sep in separators:
        cols = lines[0].split(sep) if lines else []
        print(f"  • Separador '{sep}': {len(cols)} columnas")
        if len(cols) > 1:
            print(f"    Columnas: {cols[:3]}...")
    
    # Intentar leer con diferentes parámetros
    print(f"\n🔄 INTENTANDO DIFERENTES CONFIGURACIONES...")
    
    configs = [
        {'sep': ',', 'header': 0},
        {'sep': ',', 'header': None},
        {'sep': '\t', 'header': 0},
        {'sep': ';', 'header': 0},
    ]
    
    best_config = None
    best_df = None
    
    for i, config in enumerate(configs):
        try:
            df = pd.read_csv(csv_path, nrows=100, **config)
            print(f"  ✅ Config {i+1}: {len(df.columns)} columnas, {len(df)} filas")
            print(f"     Columnas: {list(df.columns)[:3]}...")
            
            # Evaluar calidad de la configuración
            if len(df.columns) >= 6 and len(df.columns) <= 8:  # Esperamos 6-7 columnas
                best_config = config
                best_df = df
                break
                
        except Exception as e:
            print(f"  ❌ Config {i+1}: Error - {str(e)[:50]}...")
    
    if best_df is None:
        print("❌ No se pudo determinar la configuración correcta")
        return
    
    print(f"\n✅ MEJOR CONFIGURACIÓN ENCONTRADA:")
    print(f"   Separador: '{best_config['sep']}'")
    print(f"   Header: {best_config['header']}")
    print(f"   Columnas: {len(best_df.columns)}")
    
    # Cargar archivo completo con la mejor configuración
    print(f"\n📊 CARGANDO ARCHIVO COMPLETO...")
    df_full = pd.read_csv(csv_path, **best_config)
    
    print(f"📈 ESTADÍSTICAS COMPLETAS:")
    print(f"  • Total registros: {len(df_full):,}")
    print(f"  • Total columnas: {len(df_full.columns)}")
    
    # Analizar cada columna
    print(f"\n🔍 ANÁLISIS DETALLADO POR COLUMNA:")
    
    for i, col in enumerate(df_full.columns):
        print(f"\n📋 COLUMNA {i+1}: '{col}'")
        
        # Estadísticas básicas
        non_null = df_full[col].count()
        null_count = len(df_full) - non_null
        unique_count = df_full[col].nunique()
        
        print(f"  • Valores no nulos: {non_null:,} ({non_null/len(df_full)*100:.1f}%)")
        print(f"  • Valores únicos: {unique_count:,}")
        
        # Ejemplos de valores
        sample_values = df_full[col].dropna().head(10).tolist()
        print(f"  • Ejemplos: {sample_values}")
        
        # Análisis específico por tipo de dato
        if non_null > 0:
            # Verificar si son números
            numeric_values = 0
            phone_like_values = 0
            
            for val in sample_values:
                val_str = str(val).strip()
                if val_str.replace('.', '').replace('-', '').isdigit():
                    numeric_values += 1
                    # Verificar si parece un teléfono
                    clean_phone = re.sub(r'[^\d]', '', val_str)
                    if len(clean_phone) >= 10 and len(clean_phone) <= 15:
                        phone_like_values += 1
            
            if numeric_values > len(sample_values) * 0.8:
                print(f"  • Tipo detectado: NUMÉRICO ({numeric_values}/{len(sample_values)})")
                
                if phone_like_values > len(sample_values) * 0.5:
                    print(f"  • Subtipo: TELÉFONO ({phone_like_values}/{len(sample_values)})")
            
            # Verificar patrones de fecha
            date_like = 0
            for val in sample_values:
                val_str = str(val).strip()
                if re.match(r'\d{1,2}/\d{1,2}/\d{4}', val_str) or re.match(r'\d{4}-\d{1,2}-\d{1,2}', val_str):
                    date_like += 1
            
            if date_like > len(sample_values) * 0.5:
                print(f"  • Tipo detectado: FECHA ({date_like}/{len(sample_values)})")
    
    # Identificar rangos de numeración
    print(f"\n📞 ANÁLISIS DE RANGOS TELEFÓNICOS:")
    
    # Buscar columnas que parezcan rangos inicial y final
    numeric_cols = []
    for col in df_full.columns:
        sample = df_full[col].dropna().head(100)
        numeric_count = 0
        
        for val in sample:
            val_str = str(val).strip()
            clean_num = re.sub(r'[^\d]', '', val_str)
            if len(clean_num) == 10 and clean_num.isdigit():  # Números de 10 dígitos
                numeric_count += 1
        
        if numeric_count > len(sample) * 0.8:
            numeric_cols.append({
                'column': col,
                'numeric_percentage': (numeric_count / len(sample)) * 100,
                'sample_values': sample.head(5).tolist()
            })
    
    print(f"  • Columnas con números de 10 dígitos: {len(numeric_cols)}")
    for nc in numeric_cols:
        print(f"    - {nc['column']}: {nc['numeric_percentage']:.1f}%")
        print(f"      Ejemplos: {nc['sample_values']}")
    
    # Análisis de operadores
    print(f"\n📱 ANÁLISIS DE OPERADORES:")
    
    text_cols = []
    for col in df_full.columns:
        sample = df_full[col].dropna().head(100)
        text_count = 0
        
        for val in sample:
            val_str = str(val).strip()
            if len(val_str) > 5 and not val_str.replace('.', '').replace('-', '').replace('/', '').isdigit():
                text_count += 1
        
        if text_count > len(sample) * 0.8:
            unique_vals = df_full[col].nunique()
            sample_vals = df_full[col].value_counts().head(5)
            
            text_cols.append({
                'column': col,
                'unique_count': unique_vals,
                'top_values': sample_vals.to_dict()
            })
    
    print(f"  • Columnas de texto: {len(text_cols)}")
    for tc in text_cols:
        print(f"    - {tc['column']}: {tc['unique_count']} valores únicos")
        print(f"      Top valores:")
        for val, count in list(tc['top_values'].items())[:3]:
            print(f"        • {val}: {count:,} veces")
    
    return {
        'dataframe': df_full,
        'config': best_config,
        'numeric_columns': numeric_cols,
        'text_columns': text_cols,
        'total_records': len(df_full)
    }

if __name__ == "__main__":
    result = analyze_detailed()
    
    if result:
        print(f"\n🎯 ANÁLISIS DETALLADO COMPLETADO")
        print(f"📊 {result['total_records']:,} registros analizados")
        print(f"🔧 Listo para crear estrategia de integración")
    else:
        print(f"\n❌ ANÁLISIS FALLÓ")