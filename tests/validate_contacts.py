#!/usr/bin/env python3
"""
Script para validar el conteo exacto de contactos en la base de datos
"""

import psycopg2

def validate_contact_count():
    """Validar el conteo exacto de contactos"""
    try:
        # Conectar directamente a PostgreSQL
        conn = psycopg2.connect(
            host='127.0.0.1',
            port=15432,
            database='sms_marketing',
            user='sms_user',
            password='sms_password'
        )
        
        cursor = conn.cursor()
        
        print('✅ Conexión exitosa a PostgreSQL')
        print('=' * 60)
        
        # 1. Conteo total de contactos
        cursor.execute('SELECT COUNT(*) FROM contacts;')
        total_contacts = cursor.fetchone()[0]
        print(f'📊 TOTAL CONTACTOS EN BD: {total_contacts:,}')
        
        # 2. Conteo por status
        cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM contacts 
        GROUP BY status 
        ORDER BY count DESC;
        """)
        
        print('\n📋 DISTRIBUCIÓN POR STATUS:')
        for status, count in cursor.fetchall():
            percentage = (count / total_contacts) * 100
            print(f'  • {status}: {count:,} ({percentage:.1f}%)')
        
        # 3. Conteo de verificados disponibles
        cursor.execute("""
        SELECT COUNT(*) 
        FROM contacts 
        WHERE status = 'VERIFIED' AND opt_out_at IS NULL;
        """)
        verified_available = cursor.fetchone()[0]
        print(f'\n✅ CONTACTOS VERIFIED DISPONIBLES: {verified_available:,}')
        
        # 4. Conteo de móviles vs fijos en verificados
        cursor.execute("""
        SELECT is_mobile, COUNT(*) as count 
        FROM contacts 
        WHERE status = 'VERIFIED' AND opt_out_at IS NULL
        GROUP BY is_mobile
        ORDER BY count DESC;
        """)
        
        print('\n📱 DISTRIBUCIÓN MÓVILES/FIJOS (Solo VERIFIED):')
        mobile_total = 0
        for is_mobile, count in cursor.fetchall():
            tipo = 'Móviles' if is_mobile else 'Fijos'
            percentage = (count / verified_available) * 100
            print(f'  • {tipo}: {count:,} ({percentage:.1f}%)')
            if is_mobile:
                mobile_total = count
        
        # 5. Verificar si hay contactos con opt_out_at
        cursor.execute("""
        SELECT COUNT(*) 
        FROM contacts 
        WHERE opt_out_at IS NOT NULL;
        """)
        opted_out = cursor.fetchone()[0]
        print(f'\n🚫 CONTACTOS OPTED_OUT: {opted_out:,}')
        
        # 6. Verificar tabla original vs procesada
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE source = 'TELCEL2022';")
        telcel_contacts = cursor.fetchone()[0]
        print(f'\n📄 CONTACTOS DE TELCEL2022: {telcel_contacts:,}')
        
        # 7. Resumen final
        print('\n' + '=' * 60)
        print('📈 RESUMEN FINAL:')
        print(f'  • Total en BD: {total_contacts:,}')
        print(f'  • Verificados disponibles: {verified_available:,}')
        print(f'  • Móviles disponibles: {mobile_total:,}')
        print(f'  • Opted out: {opted_out:,}')
        print(f'  • De fuente TELCEL2022: {telcel_contacts:,}')
        
        # Explicar la diferencia con 36M
        print('\n🤔 ANÁLISIS DE DIFERENCIA CON 36M:')
        if total_contacts < 36000000:
            diff = 36000000 - total_contacts
            print(f'  • Faltan {diff:,} contactos del objetivo de 36M')
            print(f'  • Posibles causas: duplicados eliminados, datos inválidos filtrados')
        
        cursor.close()
        conn.close()
        
        return {
            'total': total_contacts,
            'verified_available': verified_available,
            'mobile_available': mobile_total,
            'opted_out': opted_out,
            'telcel_source': telcel_contacts
        }
        
    except Exception as e:
        print(f'❌ Error de conexión: {e}')
        return None

if __name__ == "__main__":
    validate_contact_count()