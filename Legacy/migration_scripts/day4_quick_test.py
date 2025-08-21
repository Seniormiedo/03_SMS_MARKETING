#!/usr/bin/env python3
"""
Test rápido del DÍA 4 - Verificación de componentes
"""

import asyncio
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_day4_components():
    """Test rápido de todos los componentes del DÍA 4"""
    
    print("🧪 TEST RÁPIDO DÍA 4 - SMS Marketing Platform")
    print("="*60)
    
    tests = []
    
    # Test 1: Verificar existencia de archivos
    print("\n📁 Test 1: Verificando archivos necesarios...")
    required_files = [
        "scripts/day4_migration_orchestrator.py",
        "scripts/migration_validator.py", 
        "scripts/postgres_optimizer.py",
        "scripts/migration_manager.py",
        "numeros.db"
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
            tests.append(True)
        else:
            print(f"❌ {file_path} - NO ENCONTRADO")
            tests.append(False)
    
    # Test 2: Verificar imports
    print("\n📦 Test 2: Verificando imports...")
    try:
        from scripts.migration_manager import MigrationManager, PhoneNumberNormalizer
        print("✅ MigrationManager importado")
        tests.append(True)
    except Exception as e:
        print(f"❌ Error importando MigrationManager: {e}")
        tests.append(False)
    
    try:
        from scripts.postgres_optimizer import PostgreSQLOptimizer
        print("✅ PostgreSQLOptimizer importado")
        tests.append(True)
    except Exception as e:
        print(f"❌ Error importando PostgreSQLOptimizer: {e}")
        tests.append(False)
    
    try:
        from scripts.migration_validator import MigrationValidator
        print("✅ MigrationValidator importado")
        tests.append(True)
    except Exception as e:
        print(f"❌ Error importando MigrationValidator: {e}")
        tests.append(False)
    
    # Test 3: Verificar dependencias
    print("\n📚 Test 3: Verificando dependencias...")
    dependencies = ['asyncpg', 'phonenumbers', 'psutil']
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
            tests.append(True)
        except ImportError:
            print(f"❌ {dep} - NO INSTALADO")
            tests.append(False)
    
    # Test 4: Verificar base de datos
    print("\n🗄️  Test 4: Verificando base de datos...")
    try:
        import sqlite3
        conn = sqlite3.connect("numeros.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM numeros")
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f"✅ SQLite: {count:,} registros disponibles")
        tests.append(True)
    except Exception as e:
        print(f"❌ Error accediendo SQLite: {e}")
        tests.append(False)
    
    # Test 5: Verificar PostgreSQL (conexión)
    print("\n🐘 Test 5: Verificando PostgreSQL...")
    try:
        import asyncpg
        conn = await asyncpg.connect("postgresql://sms_user:sms_password@localhost:15432/sms_marketing")
        result = await conn.fetchrow("SELECT version()")
        await conn.close()
        
        print(f"✅ PostgreSQL conectado: {result[0][:50]}...")
        tests.append(True)
    except Exception as e:
        print(f"❌ Error conectando PostgreSQL: {e}")
        tests.append(False)
    
    # Test 6: Verificar estructura de tabla
    print("\n📋 Test 6: Verificando estructura de tabla contacts...")
    try:
        conn = await asyncpg.connect("postgresql://sms_user:sms_password@localhost:15432/sms_marketing")
        
        # Verificar que existe la tabla
        result = await conn.fetchrow("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'contacts'
        """)
        
        if result[0] > 0:
            # Verificar columnas críticas
            columns_result = await conn.fetch("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'contacts'
                ORDER BY ordinal_position
            """)
            
            columns = [row[0] for row in columns_result]
            critical_columns = ['phone_e164', 'phone_national', 'status', 'is_mobile']
            
            missing_columns = [col for col in critical_columns if col not in columns]
            
            if not missing_columns:
                print(f"✅ Tabla contacts: {len(columns)} columnas")
                tests.append(True)
            else:
                print(f"❌ Faltan columnas: {missing_columns}")
                tests.append(False)
        else:
            print("❌ Tabla contacts no existe")
            tests.append(False)
            
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando tabla: {e}")
        tests.append(False)
    
    # Test 7: Test de normalización rápido
    print("\n📞 Test 7: Test de normalización...")
    try:
        from scripts.migration_manager import PhoneNumberNormalizer
        
        normalizer = PhoneNumberNormalizer()
        result = normalizer.normalize_mexican_phone("5512345678")
        
        if result["success"] and result["phone_e164"] == "+525512345678":
            print("✅ Normalización funcionando")
            tests.append(True)
        else:
            print(f"❌ Error en normalización: {result}")
            tests.append(False)
            
    except Exception as e:
        print(f"❌ Error en test de normalización: {e}")
        tests.append(False)
    
    # Resumen final
    print("\n" + "="*60)
    print("📊 RESUMEN DE TESTS")
    print("="*60)
    
    passed = sum(tests)
    total = len(tests)
    success_rate = passed / total
    
    print(f"✅ Tests pasados: {passed}/{total} ({success_rate:.1%})")
    
    if success_rate >= 0.9:
        print("🎯 SISTEMA LISTO PARA DÍA 4")
        print("✅ Todos los componentes verificados exitosamente")
    elif success_rate >= 0.7:
        print("⚠️  SISTEMA PARCIALMENTE LISTO")
        print("🔧 Algunos componentes necesitan atención")
    else:
        print("❌ SISTEMA NO LISTO")
        print("🚨 Múltiples componentes fallan - Revisar configuración")
    
    return success_rate >= 0.9

async def main():
    """Función principal"""
    success = await test_day4_components()
    
    if success:
        print("\n🚀 ¡Listo para ejecutar DÍA 4!")
    else:
        print("\n🔧 Corregir errores antes de continuar")

if __name__ == "__main__":
    asyncio.run(main())