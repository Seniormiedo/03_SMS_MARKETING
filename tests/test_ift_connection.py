#!/usr/bin/env python3
"""
Test simple de conexión y carga de datos IFT
"""

import pandas as pd
import psycopg2
from pathlib import Path

def test_connection():
    """Test de conexión básica"""
    try:
        conn = psycopg2.connect(
            host='127.0.0.1',
            port=15432,
            database='sms_marketing',
            user='sms_user',
            password='sms_password'
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT 'Connection OK' as status, COUNT(*) as contacts FROM contacts;")
        result = cursor.fetchone()
        
        print(f"✅ BD Connection: {result[0]}")
        print(f"📊 Total contacts: {result[1]:,}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_csv_load():
    """Test de carga del CSV"""
    try:
        csv_path = Path("data/Proveedores_05_08_2025.csv")
        
        if not csv_path.exists():
            print(f"❌ File not found: {csv_path}")
            return False
        
        # Leer solo las primeras 100 líneas para test
        df = pd.read_csv(csv_path, nrows=100, encoding='utf-8')
        
        print(f"✅ CSV loaded: {len(df)} rows (sample)")
        print(f"📋 Columns: {list(df.columns)}")
        
        # Mapear columnas correctamente
        df_clean = pd.DataFrame({
            'numero_inicial': df['ZONA'],
            'numero_final': df[' NUMERACION_INICIAL'], 
            'cantidad_numeros': df[' NUMERACION_FINAL'],
            'tipo_servicio': df[' OCUPACION'].str.strip(),
            'operador': df[' MODALIDAD'].str.strip(),
            'fecha_asignacion': df[' RAZON_SOCIAL'].str.strip()
        })
        
        print(f"✅ Data mapped correctly")
        print(f"📱 Sample data:")
        print(f"   Numero inicial: {df_clean['numero_inicial'].iloc[0]}")
        print(f"   Numero final: {df_clean['numero_final'].iloc[0]}")
        print(f"   Tipo servicio: {df_clean['tipo_servicio'].iloc[0]}")
        print(f"   Operador: {df_clean['operador'].iloc[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ CSV load error: {e}")
        return False

def main():
    print("🧪 TEST DE INTEGRACION IFT")
    print("=" * 40)
    
    print("\n1. Testing database connection...")
    db_ok = test_connection()
    
    print("\n2. Testing CSV load...")
    csv_ok = test_csv_load()
    
    print(f"\n📊 RESULTS:")
    print(f"   Database: {'✅ OK' if db_ok else '❌ FAIL'}")
    print(f"   CSV Load: {'✅ OK' if csv_ok else '❌ FAIL'}")
    
    if db_ok and csv_ok:
        print(f"\n🎉 All tests passed! Ready for full integration.")
    else:
        print(f"\n⚠️ Some tests failed. Check configuration.")

if __name__ == "__main__":
    main()