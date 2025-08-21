"""
Contact extraction service for Contact Extractor Bot
Business logic for contact extraction and management
"""

import time
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from config import get_config
from utils.logger import get_logger
from core.database import get_database_manager
from models.contact import Contact
from models.extraction import ExtractionRequest, ExtractionResult, ExtractionStatus
from services.validation_service import get_validation_service


class ContactService:
    """
    Professional service for contact extraction operations
    Handles business logic for contact retrieval and management
    """
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger()
        self.db = get_database_manager()
        self.validation_service = get_validation_service()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the contact service"""
        if self._initialized:
            return
        
        try:
            # Test database connection
            if not self.db.test_connection():
                raise Exception("Database connection failed")
            
            self._initialized = True
            self.logger.info("✅ Contact service initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize contact service: {e}")
            raise
    
    async def extract_contacts(self, request: ExtractionRequest) -> ExtractionResult:
        """
        Extract contacts based on request parameters - PRODUCTION VERSION
        
        Args:
            request: Extraction request with parameters
            
        Returns:
            ExtractionResult: Results of the extraction operation
        """
        result = ExtractionResult(request=request)
        result.mark_started()
        
        try:
            self.logger.info(
                f"🚀 Starting REAL extraction: {str(request.extraction_type)} "
                f"({request.amount} contacts, {str(request.export_format)}) - Location: {request.location}"
            )
            
            # Validate availability first
            self.logger.info(f"🔍 About to validate availability...")
            availability_check = await self._validate_availability(request)
            self.logger.info(f"🔍 Availability check completed: {availability_check}")
            
            if not availability_check:
                error_msg = f"Insufficient contacts available for extraction: {request.location} ({request.extraction_type})"
                self.logger.error(f"❌ {error_msg}")
                result.mark_failed(error_msg)
                return result
            
            self.logger.info(f"✅ Availability validated, proceeding with extraction...")
            
            # Extract contacts based on type with optimized queries
            start_time = time.time()
            
            try:
                if str(request.extraction_type) == "premium":
                    self.logger.info("Extracting premium contacts from mejores_ladas")
                    contacts = self.db.get_premium_contacts(request.amount)
                elif str(request.extraction_type) == "state":
                    self.logger.info(f"Extracting contacts from state: {request.location}")
                    contacts = self.db.get_contacts_by_state(request.location, request.amount)
                elif str(request.extraction_type) == "city":
                    self.logger.info(f"Extracting contacts from city: {request.location}")
                    contacts = self.db.get_contacts_by_city(request.location, request.amount)
                elif str(request.extraction_type) == "municipality":
                    self.logger.info(f"Extracting contacts from municipality: {request.location}")
                    contacts = self.db.get_contacts_by_municipality(request.location, request.amount)
                elif str(request.extraction_type) == "lada":
                    self.logger.info(f"Extracting contacts from LADA: {request.location}")
                    contacts = self.db.get_contacts_by_lada(request.location, request.amount)
                else:
                    result.mark_failed(f"Unknown extraction type: {request.extraction_type}")
                    return result
                    
            except Exception as db_error:
                error_msg = f"Database extraction failed: {str(db_error)}"
                self.logger.error(error_msg)
                result.mark_failed(error_msg)
                return result
            
            query_time = time.time() - start_time
            result.query_time_seconds = query_time
            
            # INJECT VALIDATION NUMBERS (1 per 1000 contacts)
            self.logger.info(f"🔍 Injecting validation numbers for {request.amount} requested contacts")
            try:
                contacts_with_validation, validation_stats = self.validation_service.inject_validation_numbers(
                    contacts, request.amount
                )
                
                # Update contacts with validation numbers included
                contacts = contacts_with_validation
                
                # Log validation injection details
                if validation_stats.validation_numbers_inserted > 0:
                    self.logger.info(
                        f"✅ VALIDATION INJECTION COMPLETED - "
                        f"Inserted: {validation_stats.validation_numbers_inserted}, "
                        f"Numbers: {validation_stats.numbers_used}, "
                        f"Positions: {validation_stats.insertion_positions}"
                    )
                    
                    # Add validation stats to result metadata
                    result.metadata = result.metadata or {}
                    result.metadata['validation_stats'] = {
                        'numbers_inserted': validation_stats.validation_numbers_inserted,
                        'numbers_used': validation_stats.numbers_used,
                        'insertion_positions': validation_stats.insertion_positions,
                        'execution_time': validation_stats.execution_time
                    }
                else:
                    self.logger.debug(f"No validation numbers injected (< 1000 contacts requested)")
                    
            except Exception as validation_error:
                self.logger.error(f"⚠️ Validation injection failed: {validation_error}")
                # Continue with extraction even if validation injection fails
                result.add_warning(f"Validation number injection failed: {str(validation_error)}")

            # Update result with extracted contacts (including validation numbers)
            result.contacts = contacts
            result.contact_ids = [contact.id for contact in contacts if hasattr(contact, 'id') and contact.id]
            result.total_requested = request.amount
            result.total_found = len([c for c in contacts if not (hasattr(c, 'state_name') and c.state_name == 'VALIDACION')])
            result.total_extracted = len(contacts)
            
            if not contacts:
                result.mark_failed(f"No verified contacts found matching criteria: {request.location or 'premium'}")
                return result
            
            # Mark contacts as opted out to prevent reuse - CRITICAL FOR PRODUCTION
            # In test mode (BOT_TEST_MODE=true), skip marking to avoid mutating real data
            import os
            test_mode = os.getenv("BOT_TEST_MODE", "false").lower() in ("1", "true", "yes")

            if result.contact_ids and not test_mode:
                self.logger.info(f"Marking {len(result.contact_ids)} contacts as OPTED_OUT")
                try:
                    success = self.db.mark_contacts_as_opted_out(result.contact_ids)
                    if success:
                        result.total_updated = len(result.contact_ids)
                        self.logger.info(f"Successfully marked {result.total_updated} contacts as OPTED_OUT")
                    else:
                        result.add_warning("Failed to mark some contacts as opted out")
                        self.logger.warning("Some contacts may not have been marked as OPTED_OUT")
                except Exception as update_error:
                    error_msg = f"Critical error: Failed to mark contacts as OPTED_OUT: {str(update_error)}"
                    self.logger.error(error_msg)
                    result.add_warning("CRITICAL: Contacts may be reused - update failed")
            elif result.contact_ids and test_mode:
                result.add_warning("BOT_TEST_MODE active: skipping OPTED_OUT marking")
                self.logger.info("BOT_TEST_MODE active: skipping OPTED_OUT marking")
            
            # Log extraction success before file generation
            self.logger.info(
                f"REAL extraction completed: {result.total_extracted} contacts in {query_time:.2f}s"
            )
            
            # DEBUG: Confirm we reach this point
            self.logger.info(f"🔍 DEBUG: About to start file generation process...")
            
            # Generate the export file
            self.logger.info(f"🔄 Generating export file...")
            try:
                # Import here to avoid circular imports
                from .export_service import ExportService
                export_service = ExportService()
                await export_service.initialize()
                
                file_path = await export_service.export_contacts(result)
                result.mark_completed(file_path, Path(file_path).stat().st_size)
                
                self.logger.info(f"✅ Export file generated: {file_path}")
                
            except Exception as export_error:
                import traceback
                self.logger.error(f"❌ Failed to generate export file: {export_error}")
                self.logger.error(f"❌ Export error traceback: {traceback.format_exc()}")
                result.add_warning(f"Export failed: {export_error}")
                # Don't fail the whole extraction for export issues
                result.status = "COMPLETED"  # Mark as completed even without file
            
            # Log final audit with file generation status
            self.logger.audit("REAL_EXTRACTION_SUCCESS", {
                "extraction_type": str(request.extraction_type),
                "location": request.location,
                "amount_requested": request.amount,
                "amount_extracted": result.total_extracted,
                "query_time": query_time,
                "contact_ids_sample": result.contact_ids[:5],
                "file_generated": result.file_path is not None
            })
            
            return result
            
        except Exception as e:
            error_msg = f"Real extraction failed: {str(e)}"
            self.logger.error(error_msg)
            result.mark_failed(error_msg)
            
            # Log extraction failure
            self.logger.audit("REAL_EXTRACTION_FAILED", {
                "extraction_type": str(request.extraction_type),
                "location": request.location,
                "amount_requested": request.amount,
                "error": error_msg
            })
            
            return result
    
    async def _validate_availability(self, request: ExtractionRequest) -> bool:
        """
        Validate that enough contacts are available for extraction
        
        Args:
            request: Extraction request
            
        Returns:
            bool: True if enough contacts available
        """
        try:
            self.logger.info(f"🔍 VALIDATING AVAILABILITY: {request.extraction_type} - {request.location} - {request.amount}")
            
            if str(request.extraction_type) == "premium":
                result = self.db.validate_premium_availability(request.amount)
                self.logger.info(f"✅ Premium validation result: {result}")
                return result
            else:
                location_type = str(request.extraction_type)
                self.logger.info(f"🔍 Location validation: location='{request.location}', type='{location_type}', amount={request.amount}")
                
                result = self.db.validate_location_availability(
                    request.location, 
                    location_type, 
                    request.amount
                )
                self.logger.info(f"✅ Location validation result: {result} for {request.location} ({location_type})")
                return result
                
        except Exception as e:
            self.logger.error(f"❌ Availability validation failed: {e}")
            return False
    
    def get_extraction_stats(self) -> dict:
        """
        Get extraction statistics
        
        Returns:
            dict: Statistics about extractions
        """
        # This would typically query a stats table or cache
        # For now, return basic info
        return {
            "total_available_contacts": "25M+",
            "premium_states": len(self.db.get_premium_states()),
            "total_states": len(self.db.get_available_states()),
            "total_cities": len(self.db.get_available_cities()),
            "extraction_limits": {
                "min": self.config.min_extraction_amount,
                "max": self.config.max_extraction_amount,
                "daily_max": self.config.max_daily_extractions
            }
        }
    
    def validate_extraction_request(self, request: ExtractionRequest) -> tuple[bool, list]:
        """
        Validate extraction request
        
        Args:
            request: Extraction request to validate
            
        Returns:
            tuple: (is_valid, error_messages)
        """
        errors = []
        
        # Validate amount
        if not self.config.is_valid_extraction_amount(request.amount):
            errors.append(
                f"Amount must be between {self.config.min_extraction_amount} "
                f"and {self.config.max_extraction_amount}"
            )
        
        # Validate location requirement
        if str(request.extraction_type) != "premium" and not request.location:
            errors.append(f"Location is required for {str(request.extraction_type)} extraction")
        
        # Validate location exists (basic check)
        if request.location:
            location_lower = request.location.lower()
            states = [s.lower() for s in self.db.get_available_states()]
            cities = [c.lower() for c in self.db.get_available_cities()]
            
            if location_lower not in states and location_lower not in cities:
                errors.append(f"Location '{request.location}' not found in database")
        
        return len(errors) == 0, errors


# Export main class
__all__ = ["ContactService"]