"""
Validation Number Service
Handles injection of validation numbers into contact extractions
"""

import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from models.contact import Contact
from core.database import get_database_manager
from utils.logger import get_logger


@dataclass
class ValidationContact:
    """Validation contact data structure"""
    phone_number: str
    state_name: str = "VALIDACION"
    municipality: str = "VALIDACION"
    lada: str = "526"
    is_validation: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        
        # Extract LADA from phone number if not provided
        if self.lada == "526" and len(self.phone_number) >= 3:
            self.lada = self.phone_number[:3]
    
    def to_contact(self) -> Contact:
        """Convert to Contact object"""
        # Generate a negative ID for validation contacts to avoid conflicts
        validation_id = -hash(self.phone_number) % 1000000
        
        # Extract national phone (remove country code if present)
        phone_national = self.phone_number
        if phone_national.startswith('52'):
            phone_national = phone_national[2:]
        
        # Create E164 format
        phone_e164 = f"+52{phone_national}"
        
        return Contact(
            id=validation_id,
            phone_e164=phone_e164,
            phone_national=phone_national,
            phone_original=self.phone_number,
            state_name=self.state_name,
            municipality=self.municipality,
            lada=self.lada,
            is_mobile=True,
            status="VERIFIED"  # Use string instead of enum for validation contacts
        )


@dataclass
class ValidationStats:
    """Validation injection statistics"""
    total_contacts: int
    validation_numbers_inserted: int
    insertion_frequency: int
    numbers_used: List[str]
    insertion_positions: List[int]
    execution_time: float = 0.0


class ValidationNumberService:
    """
    Service for managing validation number injection in contact extractions
    Handles random insertion of validation numbers (1 per 1000 contacts)
    """
    
    def __init__(self):
        self.db = get_database_manager()
        self.logger = get_logger()
        self.insertion_frequency = 1000  # 1 validation number per 1000 contacts
    
    def inject_validation_numbers(self, contacts: List[Contact], total_requested: int) -> tuple[List[Contact], ValidationStats]:
        """
        Inject validation numbers into contact list
        
        Args:
            contacts: List of extracted contacts
            total_requested: Total number of contacts requested by user
            
        Returns:
            Tuple of (updated_contacts_list, validation_stats)
        """
        start_time = datetime.now()
        
        # Calculate how many validation numbers to inject
        validation_count = total_requested // self.insertion_frequency
        
        if validation_count == 0:
            self.logger.debug(f"No validation numbers needed for {total_requested} contacts (< {self.insertion_frequency})")
            return contacts, ValidationStats(
                total_contacts=len(contacts),
                validation_numbers_inserted=0,
                insertion_frequency=self.insertion_frequency,
                numbers_used=[],
                insertion_positions=[]
            )
        
        self.logger.info(f"Injecting {validation_count} validation numbers into {len(contacts)} contacts")
        
        # Get validation numbers and inject them
        validation_contacts, insertion_positions, numbers_used = self._inject_numbers(
            contacts, validation_count, total_requested
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Create statistics
        stats = ValidationStats(
            total_contacts=len(validation_contacts),
            validation_numbers_inserted=validation_count,
            insertion_frequency=self.insertion_frequency,
            numbers_used=numbers_used,
            insertion_positions=insertion_positions,
            execution_time=execution_time
        )
        
        # Log injection summary
        self.logger.info(
            f"VALIDATION_INJECTION - Total: {stats.total_contacts}, "
            f"Validation inserted: {stats.validation_numbers_inserted}, "
            f"Numbers used: {numbers_used}, "
            f"Positions: {insertion_positions}, "
            f"Time: {execution_time:.3f}s"
        )
        
        return validation_contacts, stats
    
    def _inject_numbers(self, contacts: List[Contact], validation_count: int, total_requested: int) -> tuple[List[Contact], List[int], List[str]]:
        """
        Internal method to inject validation numbers
        
        Args:
            contacts: Original contact list
            validation_count: Number of validation numbers to inject
            total_requested: Total contacts requested
            
        Returns:
            Tuple of (updated_contacts, insertion_positions, numbers_used)
        """
        updated_contacts = contacts.copy()
        insertion_positions = []
        numbers_used = []
        
        for i in range(validation_count):
            # Calculate random position within each block of 1000
            block_start = i * self.insertion_frequency
            block_end = min(block_start + self.insertion_frequency, len(updated_contacts))
            
            if block_start >= len(updated_contacts):
                # If we don't have enough contacts, insert at the end
                insertion_pos = len(updated_contacts)
            else:
                # Random position within the current block
                insertion_pos = random.randint(block_start, min(block_end - 1, len(updated_contacts)))
            
            # Get random validation number
            validation_data = self.db.get_random_validation_number()
            
            if not validation_data:
                self.logger.warning(f"No validation numbers available for injection #{i+1}")
                continue
            
            # Create validation contact
            validation_contact = ValidationContact(
                phone_number=validation_data['phone_number'],
                state_name=validation_data['state_name'],
                municipality=validation_data['municipality'],
                lada=validation_data['lada']
            ).to_contact()
            
            # Insert validation contact at calculated position
            updated_contacts.insert(insertion_pos, validation_contact)
            
            # Update usage statistics
            self.db.update_validation_usage(validation_data['phone_number'])
            
            # Track insertion
            insertion_positions.append(insertion_pos)
            numbers_used.append(validation_data['phone_number'])
            
            self.logger.debug(
                f"Injected validation #{i+1}: {validation_data['phone_number']} at position {insertion_pos}"
            )
        
        return updated_contacts, insertion_positions, numbers_used
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get current validation numbers usage statistics"""
        return self.db.get_validation_stats()
    
    def validate_injection_randomness(self, insertion_positions: List[int], total_contacts: int, validation_count: int) -> Dict[str, Any]:
        """
        Validate that injection positions are truly random
        
        Args:
            insertion_positions: List of positions where validation numbers were inserted
            total_contacts: Total number of contacts in final list
            validation_count: Number of validation numbers inserted
            
        Returns:
            Dict with randomness analysis
        """
        if not insertion_positions:
            return {"error": "No insertion positions to analyze"}
        
        # Calculate expected distribution
        block_size = self.insertion_frequency
        expected_blocks = validation_count
        
        # Analyze distribution across blocks
        block_distribution = {}
        for pos in insertion_positions:
            block = pos // block_size
            block_distribution[block] = block_distribution.get(block, 0) + 1
        
        # Calculate statistics
        positions_range = max(insertion_positions) - min(insertion_positions) if len(insertion_positions) > 1 else 0
        avg_distance = positions_range / (len(insertion_positions) - 1) if len(insertion_positions) > 1 else 0
        expected_distance = total_contacts / validation_count if validation_count > 0 else 0
        
        return {
            "insertion_positions": insertion_positions,
            "total_contacts": total_contacts,
            "validation_count": validation_count,
            "block_distribution": block_distribution,
            "positions_range": positions_range,
            "average_distance": avg_distance,
            "expected_distance": expected_distance,
            "randomness_score": min(1.0, avg_distance / expected_distance) if expected_distance > 0 else 0,
            "is_well_distributed": len(set(insertion_positions)) == len(insertion_positions)  # No duplicates
        }


def get_validation_service() -> ValidationNumberService:
    """Get validation service instance"""
    return ValidationNumberService()
