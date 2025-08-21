#!/usr/bin/env python3
"""
Test script to debug contact service complete flow
"""

import asyncio
from services.contact_service import ContactService
from models.extraction import ExtractionRequest, ExtractionType, ExportFormat

async def test_contact_service_flow():
    print("🔍 Testing complete ContactService flow...")
    
    service = ContactService()
    await service.initialize()
    
    # Test Tijuana with complete flow
    request = ExtractionRequest(
        extraction_type=ExtractionType.CITY,
        amount=100,
        export_format=ExportFormat.TXT,
        location='Tijuana'
    )
    
    print('🚀 Starting complete extraction flow...')
    
    try:
        result = await service.extract_contacts(request)
        print(f'✅ Extraction result:')
        print(f'   - Success: {result.is_successful()}')
        print(f'   - Status: {result.status}')
        print(f'   - File path: {result.file_path}')
        print(f'   - Total extracted: {result.total_extracted}')
        print(f'   - Warnings: {len(result.warnings)}')
        print(f'   - Error: {result.error_message}')
        
        # Check file
        if result.file_path:
            from pathlib import Path
            if Path(result.file_path).exists():
                size = Path(result.file_path).stat().st_size
                print(f'📄 File exists: {size} bytes')
                with open(result.file_path, 'r') as f:
                    content = f.read(100)
                    print(f'📄 Content preview: {repr(content)}')
            else:
                print('❌ File does not exist')
        else:
            print('❌ No file path in result')
            
    except Exception as e:
        print(f'❌ Exception in flow: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_contact_service_flow())
