#!/usr/bin/env python3
"""
Script de diagnóstico de red para verificar conectividad al PostgreSQL
"""
import socket
import psycopg2
import sys

def test_dns_resolution():
    """Probar resolución DNS"""
    try:
        ip = socket.gethostbyname('postgres')
        print(f"✅ DNS: 'postgres' resuelve a {ip}")
        return True, ip
    except Exception as e:
        print(f"❌ DNS: Error resolviendo 'postgres': {e}")
        return False, None

def test_port_connectivity(host, port=5432):
    """Probar conectividad TCP"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ TCP: Puerto {port} abierto en {host}")
            return True
        else:
            print(f"❌ TCP: Puerto {port} cerrado en {host} (código: {result})")
            return False
    except Exception as e:
        print(f"❌ TCP: Error conectando a {host}:{port} - {e}")
        return False

def test_postgres_connection():
    """Probar conexión PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host='postgres',
            port=5432,
            dbname='sms_marketing',
            user='sms_user',
            password='sms_password',
            connect_timeout=10
        )
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM contacts')
        count = cur.fetchone()[0]
        print(f"✅ PostgreSQL: Conectado exitosamente. Contactos: {count:,}")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ PostgreSQL: Error conectando - {e}")
        return False

def main():
    print("🔍 DIAGNÓSTICO DE CONECTIVIDAD DE RED")
    print("="*50)
    
    # Paso 1: DNS
    dns_ok, ip = test_dns_resolution()
    
    # Paso 2: TCP
    if dns_ok:
        tcp_ok = test_port_connectivity('postgres', 5432)
        if ip:
            tcp_ip_ok = test_port_connectivity(ip, 5432)
    else:
        tcp_ok = False
        tcp_ip_ok = False
    
    # Paso 3: PostgreSQL
    if dns_ok and tcp_ok:
        pg_ok = test_postgres_connection()
    else:
        pg_ok = False
    
    print("\n📊 RESUMEN:")
    print(f"DNS Resolution: {'✅' if dns_ok else '❌'}")
    print(f"TCP Connectivity: {'✅' if tcp_ok else '❌'}")
    print(f"PostgreSQL Connection: {'✅' if pg_ok else '❌'}")
    
    if dns_ok and tcp_ok and pg_ok:
        print("\n🎉 ¡CONECTIVIDAD COMPLETA!")
        sys.exit(0)
    else:
        print("\n❌ PROBLEMAS DE CONECTIVIDAD DETECTADOS")
        sys.exit(1)

if __name__ == '__main__':
    main()
