#!/usr/bin/env python3
"""
Cargar TODOS los datos IFT incluyendo los rangos FIJO que faltaron
"""

import pandas as pd
import subprocess
import tempfile
import os
from pathlib import Path

def load_complete_ift_data():
    """Cargar datos IFT completos incluyendo FIJO"""
    try:
        print("🔧 CARGANDO DATOS IFT COMPLETOS...")
        print("=" * 50)
        
        # Cargar CSV
        csv_path = Path("data/Proveedores_05_08_2025.csv")
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        print(f"📋 Total registros: {len(df):,}")
        
        # Mapear columnas correctamente
        df_clean = pd.DataFrame({
            'numero_inicial': df['ZONA'],
            'numero_final': df[' NUMERACION_INICIAL'], 
            'cantidad_numeros': df[' NUMERACION_FINAL'],
            'tipo_servicio': df[' OCUPACION'].str.strip(),
            'operador': df[' MODALIDAD'].str.strip(),
            'fecha_asignacion': df[' RAZON_SOCIAL'].str.strip()
        })
        
        # Limpiar fechas
        df_clean['fecha_asignacion'] = pd.to_datetime(
            df_clean['fecha_asignacion'], 
            format='%d/%m/%Y', 
            errors='coerce'
        )
        
        # FILTRAR CORRECTAMENTE: incluir FIJO en lugar de FPP
        initial_count = len(df_clean)
        
        df_clean = df_clean[
            (df_clean['numero_inicial'].notna()) &
            (df_clean['numero_final'].notna()) &
            (df_clean['numero_inicial'] < df_clean['numero_final']) &
            (df_clean['tipo_servicio'].isin(['MPP', 'CPP', 'FIJO']))  # ¡CORREGIDO!
        ]
        
        final_count = len(df_clean)
        removed = initial_count - final_count
        
        print(f"🧹 Limpieza completada:")
        print(f"   - Registros válidos: {final_count:,}")
        print(f"   - Registros removidos: {removed:,}")
        
        # Estadísticas completas
        type_counts = df_clean['tipo_servicio'].value_counts()
        print(f"📊 Distribución COMPLETA por tipo:")
        for tipo, count in type_counts.items():
            percentage = (count / final_count) * 100
            clasificacion = "MÓVILES" if tipo == "CPP" else "FIJOS"
            print(f"   - {tipo}: {count:,} ({percentage:.1f}%) = {clasificacion}")
        
        # Crear archivo CSV temporal
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
            temp_file = f.name
            
            # Header
            f.write("numero_inicial,numero_final,cantidad_numeros,tipo_servicio,operador,fecha_asignacion\n")
            
            # Datos
            for _, row in df_clean.iterrows():
                fecha = row['fecha_asignacion'].strftime('%Y-%m-%d') if pd.notna(row['fecha_asignacion']) else '\\N'
                operador_clean = str(row['operador']).replace(',', ';').replace('\n', ' ')
                
                f.write(f"{int(row['numero_inicial'])},{int(row['numero_final'])},{int(row['cantidad_numeros'])},{row['tipo_servicio']},{operador_clean},{fecha}\n")
        
        print(f"📄 Archivo temporal: {temp_file}")
        
        # Recrear tabla con datos completos
        print("🗑️ Eliminando tabla anterior...")
        drop_cmd = [
            'docker-compose', 'exec', '-T', 'postgres',
            'psql', '-U', 'sms_user', '-d', 'sms_marketing',
            '-c', 'DROP TABLE IF EXISTS ift_rangos CASCADE;'
        ]
        subprocess.run(drop_cmd, check=True)
        
        print("🏗️ Creando tabla nueva...")
        create_cmd = [
            'docker-compose', 'exec', '-T', 'postgres',
            'psql', '-U', 'sms_user', '-d', 'sms_marketing',
            '-c', '''
            CREATE TABLE ift_rangos (
                id SERIAL PRIMARY KEY,
                numero_inicial BIGINT NOT NULL,
                numero_final BIGINT NOT NULL,
                cantidad_numeros INTEGER NOT NULL,
                tipo_servicio VARCHAR(10) NOT NULL,
                operador TEXT NOT NULL,
                fecha_asignacion DATE,
                created_at TIMESTAMP DEFAULT NOW(),
                
                CONSTRAINT ck_rango_valido CHECK (numero_final >= numero_inicial),
                CONSTRAINT ck_tipo_servicio CHECK (tipo_servicio IN ('MPP', 'CPP', 'FIJO'))
            );
            
            CREATE INDEX idx_ift_rangos_inicial ON ift_rangos (numero_inicial);
            CREATE INDEX idx_ift_rangos_final ON ift_rangos (numero_final);
            CREATE INDEX idx_ift_rangos_rango ON ift_rangos (numero_inicial, numero_final);
            CREATE INDEX idx_ift_rangos_tipo ON ift_rangos (tipo_servicio);
            CREATE INDEX idx_ift_rangos_operador ON ift_rangos (operador);
            '''
        ]
        subprocess.run(create_cmd, check=True)
        
        # Copiar archivo al contenedor
        container_file = '/tmp/ift_complete.csv'
        copy_cmd = ['docker', 'cp', temp_file, f'sms_postgres:{container_file}']
        subprocess.run(copy_cmd, check=True)
        
        print("📥 Cargando datos completos...")
        copy_sql_cmd = [
            'docker-compose', 'exec', '-T', 'postgres',
            'psql', '-U', 'sms_user', '-d', 'sms_marketing',
            '-c', f'''
            COPY ift_rangos (numero_inicial, numero_final, cantidad_numeros, tipo_servicio, operador, fecha_asignacion)
            FROM '{container_file}'
            WITH (FORMAT csv, HEADER true, NULL '\\N');
            '''
        ]
        subprocess.run(copy_sql_cmd, check=True)
        
        # Verificar carga
        count_cmd = [
            'docker-compose', 'exec', '-T', 'postgres',
            'psql', '-U', 'sms_user', '-d', 'sms_marketing',
            '-c', 'SELECT COUNT(*) as total FROM ift_rangos;'
        ]
        result = subprocess.run(count_cmd, capture_output=True, text=True, check=True)
        
        print("✅ Datos cargados exitosamente!")
        print(f"📊 Resultado: {result.stdout}")
        
        # Verificar distribución
        dist_cmd = [
            'docker-compose', 'exec', '-T', 'postgres',
            'psql', '-U', 'sms_user', '-d', 'sms_marketing',
            '-c', '''
            SELECT 
                tipo_servicio,
                COUNT(*) as rangos,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje
            FROM ift_rangos 
            GROUP BY tipo_servicio 
            ORDER BY rangos DESC;
            '''
        ]
        dist_result = subprocess.run(dist_cmd, capture_output=True, text=True, check=True)
        
        print("📊 Distribución final:")
        print(dist_result.stdout)
        
        # Limpiar archivo temporal
        os.unlink(temp_file)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = load_complete_ift_data()
    if success:
        print("\n🎉 ¡DATOS IFT COMPLETOS CARGADOS!")
        print("📋 Ahora incluye CPP, MPP y FIJO")
    else:
        print("\n❌ Error en la carga")