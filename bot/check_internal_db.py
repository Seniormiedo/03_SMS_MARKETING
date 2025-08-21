import psycopg2

# Verificar conexión interna al contenedor postgres
try:
    conn = psycopg2.connect(
        host='postgres',  # nombre del servicio en docker-compose
        port=5432, 
        dbname='sms_marketing', 
        user='sms_user', 
        password='sms_password'
    )
    cur = conn.cursor()
    
    print("✅ Conectado al contenedor postgres interno")
    
    # Listar tablas
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = [t[0] for t in cur.fetchall()]
    print(f"Tablas encontradas: {tables}")
    
    # Verificar tablas específicas
    for table in ['contacts', 'mejores_ladas']:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"✅ Tabla {table}: {count:,} registros")
        except Exception as e:
            print(f"❌ Tabla {table}: ERROR - {e}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error conectando al contenedor postgres: {e}")
