#!/usr/bin/env python3
"""
Verificar qué pasó con los datos FIJO del CSV original
"""

import pandas as pd
from pathlib import Path

def analyze_original_csv():
    """Analizar el CSV original para encontrar datos FIJO"""
    try:
        csv_path = Path("data/Proveedores_05_08_2025.csv")
        
        print("🔍 ANALIZANDO CSV ORIGINAL...")
        print("=" * 50)
        
        # Cargar todo el CSV
        df = pd.read_csv(csv_path, encoding='utf-8')
        print(f"📋 Total registros en CSV: {len(df):,}")
        
        # Mapear columnas correctamente
        df_mapped = pd.DataFrame({
            'numero_inicial': df['ZONA'],
            'numero_final': df[' NUMERACION_INICIAL'], 
            'cantidad_numeros': df[' NUMERACION_FINAL'],
            'tipo_servicio': df[' OCUPACION'].str.strip(),
            'operador': df[' MODALIDAD'].str.strip(),
            'fecha_asignacion': df[' RAZON_SOCIAL'].str.strip()
        })
        
        print(f"\n📊 DISTRIBUCIÓN ORIGINAL POR TIPO:")
        tipo_counts = df_mapped['tipo_servicio'].value_counts()
        for tipo, count in tipo_counts.items():
            percentage = (count / len(df_mapped)) * 100
            print(f"   - {tipo}: {count:,} ({percentage:.2f}%)")
        
        # Verificar qué tipos únicos existen
        print(f"\n🔤 TIPOS ÚNICOS ENCONTRADOS:")
        tipos_unicos = df_mapped['tipo_servicio'].unique()
        for i, tipo in enumerate(sorted(tipos_unicos)):
            print(f"   {i+1}. '{tipo}'")
        
        # Buscar específicamente "FIJO"
        fijo_records = df_mapped[df_mapped['tipo_servicio'].str.contains('FIJO', na=False)]
        print(f"\n🎯 REGISTROS CON 'FIJO':")
        print(f"   - Cantidad: {len(fijo_records):,}")
        
        if len(fijo_records) > 0:
            print(f"   - Ejemplos:")
            for i, (_, row) in enumerate(fijo_records.head(5).iterrows()):
                print(f"     {i+1}. Tipo: '{row['tipo_servicio']}' | Operador: '{row['operador']}'")
        
        # Verificar registros que no son MPP, CPP, FPP
        valid_types = ['MPP', 'CPP', 'FPP']
        invalid_records = df_mapped[~df_mapped['tipo_servicio'].isin(valid_types)]
        
        print(f"\n❌ REGISTROS NO VÁLIDOS (no MPP/CPP/FPP):")
        print(f"   - Cantidad: {len(invalid_records):,}")
        
        if len(invalid_records) > 0:
            print(f"   - Tipos encontrados:")
            invalid_types = invalid_records['tipo_servicio'].value_counts()
            for tipo, count in invalid_types.items():
                print(f"     - '{tipo}': {count:,}")
        
        # Verificar registros válidos
        valid_records = df_mapped[df_mapped['tipo_servicio'].isin(valid_types)]
        print(f"\n✅ REGISTROS VÁLIDOS (MPP/CPP/FPP):")
        print(f"   - Cantidad: {len(valid_records):,}")
        
        valid_type_counts = valid_records['tipo_servicio'].value_counts()
        for tipo, count in valid_type_counts.items():
            percentage = (count / len(valid_records)) * 100
            print(f"   - {tipo}: {count:,} ({percentage:.2f}%)")
        
        # Verificar si FPP existe
        fpp_records = df_mapped[df_mapped['tipo_servicio'] == 'FPP']
        print(f"\n🔍 REGISTROS FPP ESPECÍFICOS:")
        print(f"   - Cantidad: {len(fpp_records):,}")
        
        if len(fpp_records) > 0:
            print(f"   - Ejemplos FPP:")
            for i, (_, row) in enumerate(fpp_records.head(3).iterrows()):
                print(f"     {i+1}. Rango: {row['numero_inicial']}-{row['numero_final']} | Operador: {row['operador']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    analyze_original_csv()