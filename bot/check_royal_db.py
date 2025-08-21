import psycopg2

# Verificar RoyalGranel_DB en puerto 5432
try:
    conn = psycopg2.connect(
        host='127.0.0.1', 
        port=5432, 
        dbname='sms_marketing', 
        user='sms_user', 
        password='sms_password'
    )
    cur = conn.cursor()
    
    print("✅ Conectado a RoyalGranel_DB (puerto 5432)")
    
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
    print(f"❌ Error conectando a RoyalGranel_DB: {e}")
    
    # Probar con otras credenciales comunes
    try:
        conn = psycopg2.connect(
            host='127.0.0.1', 
            port=5432, 
            dbname='postgres', 
            user='postgres', 
            password='password'
        )
        cur = conn.cursor()
        print("✅ Conectado a RoyalGranel_DB con credenciales postgres/postgres")
        
        # Listar bases de datos
        cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
        databases = [d[0] for d in cur.fetchall()]
        print(f"Bases de datos: {databases}")
        
        cur.close()
        conn.close()
    except Exception as e2:
        print(f"❌ Error con credenciales postgres: {e2}")
