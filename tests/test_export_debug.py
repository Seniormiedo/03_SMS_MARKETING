#!/usr/bin/env python3
"""
Test script to debug export service
"""

import asyncio
from services.export_service import ExportService
from models.extraction import ExtractionResult, ExtractionRequest, ExtractionType, ExportFormat
from core.database import get_database_manager

async def test_export_with_real_data():
    print("🔍 Testing export service with real data...")
    
    # Get real contacts from database
    db = get_database_manager()
    contacts = db.get_contacts_by_city('Tijuana', 2)
    print(f'Got {len(contacts)} real contacts from DB')
    
    if not contacts:
        print('No contacts found!')
        return
    
    # Create request and result
    request = ExtractionRequest(
        extraction_type=ExtractionType.CITY,
        amount=100,
        export_format=ExportFormat.TXT,
        location='Tijuana'
    )
    
    result = ExtractionResult(request=request)
    result.contacts = contacts
    result.total_extracted = len(contacts)
    
    print(f'Sample contact: {contacts[0].phone_e164 if contacts else "None"}')
    
    # Test export
    export_service = ExportService()
    await export_service.initialize()
    
    try:
        file_path = await export_service.export_contacts(result)
        print(f'✅ Export successful: {file_path}')
        
        from pathlib import Path
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f'📄 File exists: {size} bytes')
            # Read first few lines
            with open(file_path, 'r') as f:
                content = f.read(200)
                print(f'📄 Content preview: {content}')
        
    except Exception as e:
        print(f'❌ Export failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_export_with_real_data())
