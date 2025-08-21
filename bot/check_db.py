#!/usr/bin/env python3
"""
Script para verificar la base de datos y sus tablas
"""

import psycopg2
from config import get_config

def main():
    config = get_config()
    
    print(f"Conectando a:")
    print(f"Host: {config.db_host}")
    print(f"Port: {config.db_port}")
    print(f"Database: {config.db_name}")
    print(f"User: {config.db_user}")
    print("-" * 50)
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(
            host=config.db_host,
            port=config.db_port,
            dbname=config.db_name,
            user=config.db_user,
            password=config.db_password
        )
        cur = conn.cursor()
        
        # Listar todas las tablas
        cur.execute("""
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        
        print(f"Tablas encontradas ({len(tables)}):")
        for table_name, table_type in tables:
            print(f"- {table_name} ({table_type})")
        
        print("-" * 50)
        
        # Verificar tablas específicas que necesita el bot
        required_tables = ['contacts', 'mejores_ladas']
        for table in required_tables:
            cur.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = '{table}';
            """)
            exists = cur.fetchone()[0] > 0
            
            if exists:
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                count = cur.fetchone()[0]
                print(f"✅ Tabla '{table}' existe con {count:,} registros")
            else:
                print(f"❌ Tabla '{table}' NO existe")
        
        cur.close()
        conn.close()
        print("✅ Conexión cerrada correctamente")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
