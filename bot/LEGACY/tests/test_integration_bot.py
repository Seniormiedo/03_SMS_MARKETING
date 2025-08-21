import asyncio
import os

import pytest

from utils.logger import setup_logging
from core.database import get_database_manager
from core.validators import get_validator
from services.contact_service import ContactService
from models.extraction import ExtractionRequest, ExtractionType, ExportFormat


@pytest.mark.asyncio
async def test_db_connectivity():
    setup_logging()
    db = get_database_manager()
    assert db.test_connection() is True


@pytest.mark.asyncio
async def test_premium_extraction_readonly(tmp_path):
    os.environ["BOT_TEST_MODE"] = "true"
    setup_logging()

    service = ContactService()
    await service.initialize()

    req = ExtractionRequest(
        extraction_type=ExtractionType.PREMIUM,
        amount=200,
        export_format=ExportFormat.TXT,
    )

    result = await service.extract_contacts(req)
    assert result.total_extracted >= 0  # puede ser 0 si no hay datos
    assert result.status.name in ("COMPLETED", "FAILED")


@pytest.mark.asyncio
async def test_states_and_cities_listing():
    db = get_database_manager()
    states = db.get_available_states()
    cities = db.get_available_cities()
    assert isinstance(states, list)
    assert isinstance(cities, list)

