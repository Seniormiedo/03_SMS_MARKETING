#!/usr/bin/env python3
"""
Tests unitarios para el sistema de migración
SMS Marketing Platform
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, patch
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.migration_manager import PhoneNumberNormalizer, DataTransformer, MigrationManager

class TestPhoneNumberNormalizer:
    """Tests para el normalizador de números telefónicos"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.normalizer = PhoneNumberNormalizer()
    
    def test_normalize_valid_mexican_mobile(self):
        """Test normalización de número móvil mexicano válido"""
        result = self.normalizer.normalize_mexican_phone("5512345678")
        
        assert result["success"] is True
        assert result["phone_e164"] == "+525512345678"
        assert result["phone_national"] == "5512345678"
        assert result["is_mobile"] is True
        assert result["status"] == "VERIFIED"
    
    def test_normalize_with_country_code(self):
        """Test normalización con código de país"""
        result = self.normalizer.normalize_mexican_phone("+525512345678")
        
        assert result["success"] is True
        assert result["phone_e164"] == "+525512345678"
        assert result["phone_national"] == "5512345678"
    
    def test_normalize_landline_number(self):
        """Test normalización de número fijo"""
        result = self.normalizer.normalize_mexican_phone("8112345678")
        
        assert result["success"] is True
        assert result["phone_e164"] == "+528112345678"
        assert result["is_mobile"] is False
        assert result["status"] == "NOT_MOBILE"
    
    def test_normalize_invalid_number(self):
        """Test normalización de número inválido"""
        result = self.normalizer.normalize_mexican_phone("123")
        
        assert result["success"] is False
        assert result["status"] == "INVALID_FORMAT"
        assert result["phone_e164"] is None
    
    def test_normalize_empty_number(self):
        """Test normalización de número vacío"""
        result = self.normalizer.normalize_mexican_phone("")
        
        assert result["success"] is False
        assert "Empty phone number" in result["error"]
    
    def test_normalize_none_number(self):
        """Test normalización de número None"""
        result = self.normalizer.normalize_mexican_phone(None)
        
        assert result["success"] is False
        assert "Empty phone number" in result["error"]
    
    def test_clean_phone_number(self):
        """Test limpieza de números telefónicos"""
        # Test con espacios y caracteres especiales
        cleaned = self.normalizer._clean_phone_number("(55) 1234-5678")
        assert cleaned == "+52 (55) 1234-5678"  # Se agrega +52
        
        # Test con número ya con +52
        cleaned = self.normalizer._clean_phone_number("+525512345678")
        assert cleaned == "+525512345678"
        
        # Test con número de 12 dígitos
        cleaned = self.normalizer._clean_phone_number("525512345678")
        assert cleaned == "+525512345678"

class TestDataTransformer:
    """Tests para el transformador de datos"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.transformer = DataTransformer()
    
    def test_transform_complete_record(self):
        """Test transformación de registro completo"""
        source_record = {
            "id": 1,
            "numero": "5512345678",
            "campo1_original": "5512345678",
            "nombre": "JUAN PEREZ LOPEZ",
            "direccion": "CALLE FALSA 123",
            "colonia": "CENTRO",
            "municipio_cof": "CIUDAD DE MEXICO",
            "estado_cof": "CDMX",
            "lada": "55",
            "ciudad_por_lada": "Ciudad de México",
            "es_valido": 1,
            "fecha_migracion": "2025-01-27 12:00:00"
        }
        
        result = self.transformer.transform_record(source_record)
        
        assert result["success"] is True
        data = result["data"]
        
        assert data["phone_e164"] == "+525512345678"
        assert data["phone_national"] == "5512345678"
        assert data["full_name"] == "JUAN PEREZ LOPEZ"
        assert data["state_code"] == "CDMX"
        assert data["state_name"] == "CIUDAD DE MEXICO"
        assert data["is_mobile"] is True
        assert data["status"] == "VERIFIED"
        assert data["source"] == "TELCEL2022"
    
    def test_transform_minimal_record(self):
        """Test transformación de registro mínimo"""
        source_record = {
            "numero": "5512345678",
            "es_valido": 1
        }
        
        result = self.transformer.transform_record(source_record)
        
        assert result["success"] is True
        data = result["data"]
        
        assert data["phone_e164"] == "+525512345678"
        assert data["full_name"] is None
        assert data["address"] is None
        assert data["status"] == "VERIFIED"
    
    def test_clean_text(self):
        """Test limpieza de texto"""
        # Texto normal
        assert self.transformer._clean_text("  HOLA MUNDO  ") == "HOLA MUNDO"
        
        # Texto vacío
        assert self.transformer._clean_text("") is None
        assert self.transformer._clean_text("   ") is None
        assert self.transformer._clean_text(None) is None
    
    def test_clean_lada(self):
        """Test limpieza de códigos LADA"""
        # LADA válida de 2 dígitos
        assert self.transformer._clean_lada("55") == "55"
        
        # LADA válida de 3 dígitos
        assert self.transformer._clean_lada("612") == "612"
        
        # LADA con caracteres especiales
        assert self.transformer._clean_lada("(55)") == "55"
        
        # LADA inválida
        assert self.transformer._clean_lada("1") is None
        assert self.transformer._clean_lada("12345") is None
        assert self.transformer._clean_lada("") is None
    
    def test_normalize_state_code(self):
        """Test normalización de códigos de estado"""
        # Código existente
        assert self.transformer._normalize_state_code("CDMX") == "CDMX"
        
        # Nombre completo a código
        assert self.transformer._normalize_state_code("CIUDAD DE MEXICO") == "CDMX"
        
        # Código desconocido
        result = self.transformer._normalize_state_code("DESCONOCIDO")
        assert len(result) <= 5
    
    def test_map_status(self):
        """Test mapeo de status"""
        # Número válido
        assert self.transformer._map_status(1, "VERIFIED") == "VERIFIED"
        assert self.transformer._map_status(True, "VERIFIED") == "VERIFIED"
        assert self.transformer._map_status("1", "VERIFIED") == "VERIFIED"
        
        # Número inválido
        assert self.transformer._map_status(0, "VERIFIED") == "UNKNOWN"
        assert self.transformer._map_status(False, "VERIFIED") == "UNKNOWN"
        
        # Status de teléfono inválido
        assert self.transformer._map_status(1, "INVALID_FORMAT") == "INVALID_FORMAT"
        assert self.transformer._map_status(1, "NOT_MOBILE") == "NOT_MOBILE"
        
        # Valor None
        assert self.transformer._map_status(None, "VERIFIED") == "UNKNOWN"

class TestMigrationManager:
    """Tests para el gestor de migración"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.manager = MigrationManager(
            sqlite_path="test.db",
            postgres_url="postgresql://test:test@localhost:5432/test",
            batch_size=100
        )
    
    @patch('sqlite3.connect')
    def test_initialize_migration_stats(self, mock_sqlite_connect):
        """Test inicialización de estadísticas"""
        # Mock de SQLite
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [1000]
        mock_conn.cursor.return_value = mock_cursor
        mock_sqlite_connect.return_value = mock_conn
        
        # Ejecutar test
        asyncio.run(self.manager._initialize_migration_stats())
        
        # Verificar resultados
        assert self.manager.stats.total_records == 1000
        assert self.manager.stats.total_batches == 10  # 1000 / 100
        assert self.manager.stats.start_time is not None
    
    def test_update_stats(self):
        """Test actualización de estadísticas"""
        self.manager.stats.start_time = datetime.now()
        self.manager.stats.total_records = 1000
        
        batch_result = {
            "total_records": 100,
            "successful_records": 95,
            "failed_records": 5
        }
        
        self.manager._update_stats(batch_result)
        
        assert self.manager.stats.processed_records == 100
        assert self.manager.stats.successful_records == 95
        assert self.manager.stats.failed_records == 5
        assert self.manager.stats.records_per_second > 0

# Tests de integración
class TestMigrationIntegration:
    """Tests de integración para migración"""
    
    @pytest.mark.asyncio
    async def test_phone_normalization_integration(self):
        """Test integración de normalización de teléfonos"""
        normalizer = PhoneNumberNormalizer()
        
        # Lista de números de prueba
        test_numbers = [
            "5512345678",      # Móvil CDMX
            "8112345678",      # Fijo Monterrey
            "+525512345678",   # Con código país
            "123",             # Inválido
            "",                # Vacío
            None               # None
        ]
        
        results = []
        for number in test_numbers:
            result = normalizer.normalize_mexican_phone(number)
            results.append(result)
        
        # Verificar resultados
        assert results[0]["success"] is True  # Válido
        assert results[1]["success"] is True  # Válido
        assert results[2]["success"] is True  # Válido
        assert results[3]["success"] is False # Inválido
        assert results[4]["success"] is False # Vacío
        assert results[5]["success"] is False # None
    
    def test_data_transformation_pipeline(self):
        """Test pipeline completo de transformación"""
        transformer = DataTransformer()
        
        # Registro de prueba completo
        test_record = {
            "id": 1,
            "numero": "5512345678",
            "campo1_original": "55-1234-5678",
            "nombre": "  MARIA GONZALEZ RODRIGUEZ  ",
            "direccion": "AV. INSURGENTES 1234",
            "colonia": "ROMA NORTE",
            "municipio_cof": "BENITO JUAREZ",
            "estado_cof": "CDMX",
            "lada": "55",
            "ciudad_por_lada": "Ciudad de México",
            "es_valido": 1,
            "fecha_migracion": "2025-01-27 12:00:00"
        }
        
        # Transformar
        result = transformer.transform_record(test_record)
        
        # Verificar transformación completa
        assert result["success"] is True
        data = result["data"]
        
        # Verificar campos críticos
        assert data["phone_e164"] == "+525512345678"
        assert data["phone_national"] == "5512345678"
        assert data["phone_original"] == "55-1234-5678"
        assert data["full_name"] == "MARIA GONZALEZ RODRIGUEZ"
        assert data["state_code"] == "CDMX"
        assert data["is_mobile"] is True
        assert data["status"] == "VERIFIED"
        assert data["source"] == "TELCEL2022"

def run_tests():
    """Ejecutar todos los tests"""
    print("🧪 Ejecutando tests de migración...")
    
    # Ejecutar tests con pytest
    pytest.main([
        __file__,
        "-v",
        "--tb=short"
    ])

if __name__ == "__main__":
    run_tests()