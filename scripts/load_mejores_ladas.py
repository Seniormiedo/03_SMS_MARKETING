#!/usr/bin/env python3
"""
Script para cargar datos de mejores LADAs desde CSV a PostgreSQL
Archivo: scripts/load_mejores_ladas.py
Fecha: Agosto 2025
"""

import csv
import subprocess
import sys
from pathlib import Path

def load_mejores_ladas_to_db():
    """
    Carga los datos del archivo mejores_ladas_enriquecido.csv a la tabla mejores_ladas
    """
    print("🚀 Iniciando carga de mejores LADAs a PostgreSQL...")
    
    # Ruta del archivo CSV
    csv_file = Path("data/mejores_ladas_enriquecido.csv")
    
    if not csv_file.exists():
        print(f"❌ Error: No se encuentra el archivo {csv_file}")
        return False
    
    try:
        # Leer y procesar el CSV
        records_processed = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                # Limpiar y preparar los datos
                ranking = int(row['#'])
                municipio = row['Municipio'].strip()
                estado = row['Estado'].strip()
                icpth_2022 = int(row['ICPTH_2022'])
                lada = row['LADA'].strip()
                zona_horaria = row['UCT'].strip() if row['UCT'] else None
                hora_recomendada = row['hora_recomendada'].strip() if row['hora_recomendada'] else None
                pib = int(row['pib']) if row['pib'] else None
                
                # Escapar comillas simples para SQL
                municipio = municipio.replace("'", "''")
                estado = estado.replace("'", "''")
                if hora_recomendada:
                    hora_recomendada = hora_recomendada.replace("'", "''")
                
                # Construir comando SQL
                sql_command = f"""
                INSERT INTO mejores_ladas (ranking, municipio, estado, icpth_2022, lada, zona_horaria, hora_recomendada, pib)
                VALUES ({ranking}, '{municipio}', '{estado}', {icpth_2022}, '{lada}', 
                        {'NULL' if zona_horaria is None else f"'{zona_horaria}'"}, 
                        {'NULL' if hora_recomendada is None else f"'{hora_recomendada}'"}, 
                        {'NULL' if pib is None else pib})
                ON CONFLICT (ranking) DO UPDATE SET
                    municipio = EXCLUDED.municipio,
                    estado = EXCLUDED.estado,
                    icpth_2022 = EXCLUDED.icpth_2022,
                    lada = EXCLUDED.lada,
                    zona_horaria = EXCLUDED.zona_horaria,
                    hora_recomendada = EXCLUDED.hora_recomendada,
                    pib = EXCLUDED.pib,
                    updated_at = NOW();
                """
                
                # Ejecutar comando SQL
                result = subprocess.run([
                    "docker-compose", "exec", "-T", "postgres", 
                    "psql", "-U", "sms_user", "-d", "sms_marketing", 
                    "-c", sql_command
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    records_processed += 1
                    print(f"✅ Procesado: {ranking}. {municipio}, {estado} (LADA {lada})")
                else:
                    print(f"❌ Error procesando {ranking}. {municipio}: {result.stderr}")
                    return False
        
        print(f"\n🎉 Carga completada exitosamente!")
        print(f"📊 Registros procesados: {records_processed}")
        
        # Verificar la carga
        verify_result = subprocess.run([
            "docker-compose", "exec", "-T", "postgres",
            "psql", "-U", "sms_user", "-d", "sms_marketing",
            "-c", "SELECT COUNT(*) as total_registros FROM mejores_ladas;"
        ], capture_output=True, text=True)
        
        if verify_result.returncode == 0:
            print("📈 Verificación de la base de datos:")
            print(verify_result.stdout)
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la carga: {str(e)}")
        return False

def show_mejores_ladas_stats():
    """
    Muestra estadísticas de las mejores LADAs cargadas
    """
    print("\n📊 Consultando estadísticas de mejores LADAs...")
    
    queries = [
        ("Top 10 LADAs por ICPTH 2022", """
            SELECT ranking, municipio, estado, lada, icpth_2022 
            FROM mejores_ladas 
            ORDER BY icpth_2022 DESC 
            LIMIT 10;
        """),
        ("Distribución por Estado", """
            SELECT estado, COUNT(*) as cantidad, AVG(icpth_2022) as icpth_promedio
            FROM mejores_ladas 
            GROUP BY estado 
            ORDER BY cantidad DESC;
        """),
        ("LADAs por Zona Horaria", """
            SELECT zona_horaria, COUNT(*) as cantidad
            FROM mejores_ladas 
            GROUP BY zona_horaria 
            ORDER BY cantidad DESC;
        """)
    ]
    
    for title, query in queries:
        print(f"\n🔍 {title}:")
        result = subprocess.run([
            "docker-compose", "exec", "-T", "postgres",
            "psql", "-U", "sms_user", "-d", "sms_marketing",
            "-c", query
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"❌ Error en consulta: {result.stderr}")

def main():
    """
    Función principal
    """
    print("📋 CARGADOR DE MEJORES LADAs - SMS MARKETING")
    print("=" * 50)
    
    # Verificar que Docker Compose esté funcionando
    print("🔍 Verificando conexión a base de datos...")
    test_result = subprocess.run([
        "docker-compose", "exec", "-T", "postgres",
        "psql", "-U", "sms_user", "-d", "sms_marketing",
        "-c", "SELECT 'Conexión exitosa' as status;"
    ], capture_output=True, text=True)
    
    if test_result.returncode != 0:
        print("❌ Error: No se puede conectar a la base de datos")
        print("💡 Asegúrate de que Docker Compose esté ejecutándose: docker-compose up -d")
        sys.exit(1)
    
    print("✅ Conexión a base de datos exitosa")
    
    # Cargar datos
    if load_mejores_ladas_to_db():
        show_mejores_ladas_stats()
        print("\n🎯 CARGA COMPLETADA EXITOSAMENTE")
        print("💡 Los datos están listos para usar en campañas SMS segmentadas")
    else:
        print("\n❌ CARGA FALLIDA")
        sys.exit(1)

if __name__ == "__main__":
    main()