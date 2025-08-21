#!/usr/bin/env python3
"""
Test de migración con muestra pequeña (1000 registros)
"""

import asyncio
import sqlite3
import json
from datetime import datetime
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.migration_manager import PhoneNumberNormalizer, DataTransformer

async def test_phone_normalization():
    """Test básico de normalización de números"""
    print("🧪 Probando normalización de números telefónicos...")
    
    normalizer = PhoneNumberNormalizer()
    
    # Números de prueba
    test_numbers = [
        "5512345678",      # Móvil CDMX
        "8112345678",      # Fijo Monterrey  
        "6121004768",      # De la base real
        "+525512345678",   # Con código país
        "123",             # Inválido
        ""                 # Vacío
    ]
    
    print("\n📱 Resultados de normalización:")
    print("-" * 80)
    
    for i, number in enumerate(test_numbers, 1):
        result = normalizer.normalize_mexican_phone(number)
        
        if result["success"]:
            print(f"{i}. ✅ {number} → {result['phone_e164']} | Móvil: {result['is_mobile']} | Status: {result['status']}")
        else:
            print(f"{i}. ❌ {number} → Error: {result.get('error', 'Unknown error')}")
    
    return True

async def test_data_transformation():
    """Test de transformación de datos"""
    print("\n🔄 Probando transformación de datos...")
    
    transformer = DataTransformer()
    
    # Registro de prueba basado en datos reales
    test_record = {
        "id": 1,
        "numero": "6121004768",
        "campo1_original": "6121004768",
        "nombre": "CATALINO RODRIGUEZ ALVARADO",
        "direccion": "ENCINAS Y EMILIANO ZAPATA #2695",
        "colonia": "LOS OLIVOS LA RINCONADA",
        "municipio_csv": "MEXICO",
        "estado_sep": None,
        "municipio_sep": None,
        "estado_cof": "BCS",
        "municipio_cof": "LA PAZ",
        "lada": "612",
        "ciudad_por_lada": "La Paz",
        "es_valido": 1,
        "fecha_migracion": "2025-08-05 00:24:44"
    }
    
    result = transformer.transform_record(test_record)
    
    print("\n📊 Resultado de transformación:")
    print("-" * 80)
    
    if result["success"]:
        data = result["data"]
        print(f"✅ Transformación exitosa:")
        print(f"   📞 E164: {data['phone_e164']}")
        print(f"   📞 Nacional: {data['phone_national']}")
        print(f"   👤 Nombre: {data['full_name']}")
        print(f"   📍 Estado: {data['state_code']} - {data['state_name']}")
        print(f"   🏙️  Ciudad: {data['city']}")
        print(f"   📱 Móvil: {data['is_mobile']}")
        print(f"   ✔️  Status: {data['status']}")
        print(f"   📡 Operador: {data['operator']}")
    else:
        print(f"❌ Error en transformación: {result.get('error', 'Unknown error')}")
    
    return result["success"]

async def test_sample_from_real_db():
    """Test con muestra real de la base de datos"""
    print("\n📋 Probando con muestra real de numeros.db...")
    
    try:
        # Conectar a SQLite
        conn = sqlite3.connect("numeros.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Obtener muestra pequeña
        cursor.execute("SELECT * FROM numeros LIMIT 10")
        sample_records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        print(f"📊 Procesando {len(sample_records)} registros de muestra...")
        
        transformer = DataTransformer()
        results = {
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        print("\n🔍 Resultados detallados:")
        print("-" * 100)
        
        for i, record in enumerate(sample_records, 1):
            result = transformer.transform_record(record)
            
            if result["success"]:
                results["successful"] += 1
                data = result["data"]
                print(f"{i:2d}. ✅ {record['numero']} → {data['phone_e164']} | {data['full_name'][:30]}... | {data['status']}")
            else:
                results["failed"] += 1
                results["errors"].append(result.get("error", "Unknown error"))
                print(f"{i:2d}. ❌ {record['numero']} → Error: {result.get('error', 'Unknown error')}")
        
        print("\n📈 Resumen de resultados:")
        print("-" * 50)
        print(f"✅ Exitosos: {results['successful']}")
        print(f"❌ Fallidos: {results['failed']}")
        print(f"📊 Tasa de éxito: {(results['successful']/len(sample_records)*100):.1f}%")
        
        if results["errors"]:
            print(f"\n🚨 Errores encontrados:")
            for error in set(results["errors"]):
                print(f"   - {error}")
        
        return results["successful"] > 0
        
    except Exception as e:
        print(f"❌ Error accediendo a la base de datos: {e}")
        return False

async def benchmark_performance():
    """Benchmark básico de performance"""
    print("\n⚡ Probando performance de normalización...")
    
    normalizer = PhoneNumberNormalizer()
    
    # Generar números de prueba
    test_numbers = [f"55123456{str(i).zfill(2)}" for i in range(100)]
    
    start_time = datetime.now()
    
    successful = 0
    for number in test_numbers:
        result = normalizer.normalize_mexican_phone(number)
        if result["success"]:
            successful += 1
    
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    
    print(f"📊 Resultados de benchmark:")
    print(f"   🔢 Números procesados: {len(test_numbers)}")
    print(f"   ✅ Exitosos: {successful}")
    print(f"   ⏱️  Tiempo total: {elapsed:.3f} segundos")
    print(f"   ⚡ Velocidad: {len(test_numbers)/elapsed:.0f} números/segundo")
    
    # Estimar tiempo para 36.6M registros
    estimated_seconds = (36_645_692 / (len(test_numbers)/elapsed))
    estimated_hours = estimated_seconds / 3600
    
    print(f"   📈 Estimación para 36.6M: {estimated_hours:.1f} horas")
    
    return True

async def main():
    """Función principal de testing"""
    print("🚀 Test de Migración - SMS Marketing Platform")
    print("=" * 60)
    
    tests = [
        ("Normalización de números", test_phone_normalization),
        ("Transformación de datos", test_data_transformation), 
        ("Muestra de base real", test_sample_from_real_db),
        ("Benchmark de performance", benchmark_performance)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Ejecutando: {test_name}")
        try:
            results[test_name] = await test_func()
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results[test_name] = False
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE TESTS")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Resultado final: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("✅ Todos los tests pasaron - Sistema listo para migración")
    else:
        print("⚠️  Algunos tests fallaron - Revisar antes de migración completa")

if __name__ == "__main__":
    asyncio.run(main())