"""
Validation system for Contact Extractor Bot
Handles input validation, command parsing, and business rules
"""

import re
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, validator

from config import get_config
from models.extraction import ExtractionType, ExportFormat, ExtractionRequest
from utils.logger import get_logger


class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, field: str = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(message)


class CommandType(str, Enum):
    """Bot command types"""
    GET = "get"
    HELP = "help"
    STATS = "stats"
    STATES = "states"
    CITIES = "cities"
    AVAILABLE = "available"
    UNKNOWN = "unknown"


class ParsedCommand(BaseModel):
    """
    Parsed command structure
    Represents a validated bot command
    """
    
    command_type: CommandType = Field(..., description="Type of command")
    raw_command: str = Field(..., description="Original raw command")
    
    # GET command specific fields
    amount: Optional[int] = Field(None, description="Number of contacts requested")
    extraction_type: Optional[ExtractionType] = Field(None, description="Type of extraction")
    location: Optional[str] = Field(None, description="Location filter")
    export_format: Optional[ExportFormat] = Field(None, description="Export format")
    
    # Validation results
    is_valid: bool = Field(default=True, description="Command is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    
    def add_error(self, error: str):
        """Add validation error"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add validation warning"""
        self.warnings.append(warning)
    
    def to_extraction_request(self) -> Optional[ExtractionRequest]:
        """Convert to ExtractionRequest if valid GET command"""
        if not self.is_valid or self.command_type != CommandType.GET:
            return None
        
        return ExtractionRequest(
            extraction_type=self.extraction_type,
            amount=self.amount,
            export_format=self.export_format,
            location=self.location
        )


class BotValidator:
    """
    Main validation system for bot commands
    Handles parsing, validation, and business rule checks
    """
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger()
        
        # Known states and cities (can be loaded from database)
        self._known_states = set()
        self._known_cities = set()
        self._premium_states = set()
        
        # Command patterns
        self.get_pattern = re.compile(
            r'^/get\s+(\d+)\s+(premium|[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ\s]+)\s+(xlsx|txt)$',
            re.IGNORECASE
        )
    
    def set_known_locations(self, states: List[str], cities: List[str], premium_states: List[str]):
        """
        Set known locations for validation
        
        Args:
            states: List of valid state names
            cities: List of valid city names  
            premium_states: List of premium state names
        """
        self._known_states = {state.lower().strip() for state in states}
        self._known_cities = {city.lower().strip() for city in cities}
        self._premium_states = {state.lower().strip() for state in premium_states}
        
        self.logger.info(
            f"Updated known locations: {len(states)} states, "
            f"{len(cities)} cities, {len(premium_states)} premium states"
        )
    
    def parse_command(self, command: str) -> ParsedCommand:
        """
        Parse and validate bot command
        
        Args:
            command: Raw command string
            
        Returns:
            ParsedCommand: Parsed and validated command
        """
        command = command.strip()
        
        # Determine command type
        if command.startswith('/get'):
            return self._parse_get_command(command)
        elif command.startswith('/help'):
            return ParsedCommand(command_type=CommandType.HELP, raw_command=command)
        elif command.startswith('/stats'):
            return ParsedCommand(command_type=CommandType.STATS, raw_command=command)
        elif command.startswith('/states'):
            return ParsedCommand(command_type=CommandType.STATES, raw_command=command)
        elif command.startswith('/cities'):
            return self._parse_cities_command(command)
        elif command.startswith('/available'):
            return self._parse_available_command(command)
        else:
            parsed = ParsedCommand(command_type=CommandType.UNKNOWN, raw_command=command)
            parsed.add_error("Unknown command. Use /help for available commands.")
            return parsed
    
    def _parse_get_command(self, command: str) -> ParsedCommand:
        """
        Parse GET command with comprehensive validation
        
        Args:
            command: GET command string
            
        Returns:
            ParsedCommand: Parsed GET command
        """
        parsed = ParsedCommand(command_type=CommandType.GET, raw_command=command)
        
        # Try to match the pattern
        match = self.get_pattern.match(command)
        if not match:
            parsed.add_error(
                "Invalid GET command format. "
                "Use: /get [amount] [premium|state|city] [xlsx|txt]"
            )
            return parsed
        
        amount_str, location_str, format_str = match.groups()
        
        # Validate amount
        try:
            amount = int(amount_str)
            if not self.config.is_valid_extraction_amount(amount):
                parsed.add_error(
                    f"Amount must be between {self.config.min_extraction_amount} "
                    f"and {self.config.max_extraction_amount}"
                )
            else:
                parsed.amount = amount
                
                # Check if confirmation is required
                if self.config.should_require_confirmation(amount):
                    parsed.add_warning(
                        f"Large extraction ({amount:,} contacts) may require confirmation"
                    )
        except ValueError:
            parsed.add_error(f"Invalid amount: {amount_str}")
        
        # Validate export format
        try:
            parsed.export_format = ExportFormat(format_str.lower())
        except ValueError:
            parsed.add_error(f"Invalid format: {format_str}. Use 'xlsx' or 'txt'")
        
        # Validate location and determine extraction type
        location_lower = location_str.lower().strip()
        
        # Debug logging
        from utils.logger import get_logger
        logger = get_logger()
        logger.info(f"🔍 PARSING LOCATION: '{location_str}' -> '{location_lower}'")
        logger.info(f"🔍 Known cities count: {len(self._known_cities)}")
        logger.info(f"🔍 Known states count: {len(self._known_states)}")
        
        if location_lower == "premium":
            parsed.extraction_type = ExtractionType.PREMIUM
            parsed.location = None
            logger.info(f"✅ Detected as PREMIUM extraction")
        else:
            # Check if it's a known STATE FIRST (states are more authoritative than cities)
            if location_lower in self._known_states:
                parsed.extraction_type = ExtractionType.STATE
                parsed.location = location_str.strip()
                logger.info(f"✅ Detected as STATE extraction: {parsed.location}")
            # Then check if it's a known city
            elif location_lower in self._known_cities:
                parsed.extraction_type = ExtractionType.CITY
                parsed.location = location_str.strip()
                logger.info(f"✅ Detected as CITY extraction: {parsed.location}")
            else:
                # If we don't have location data loaded, try to guess intelligently
                if not self._known_states and not self._known_cities:
                    # For common Mexican cities, assume city type
                    common_cities = ['tijuana', 'guadalajara', 'monterrey', 'puebla', 'cancun', 'merida', 'toluca', 'leon']
                    if location_lower in common_cities:
                        parsed.extraction_type = ExtractionType.CITY
                    else:
                        parsed.extraction_type = ExtractionType.STATE  # Default assumption
                    
                    parsed.location = location_str.strip()
                    parsed.add_warning(
                        f"Location '{location_str}' will be validated against database"
                    )
                else:
                    # Try fuzzy matching for cities (allow partial matches)
                    fuzzy_city_match = any(location_lower in city.lower() or city.lower() in location_lower 
                                         for city in self._known_cities)
                    fuzzy_state_match = any(location_lower in state.lower() or state.lower() in location_lower 
                                          for state in self._known_states)
                    
                    if fuzzy_city_match:
                        parsed.extraction_type = ExtractionType.CITY
                        parsed.location = location_str.strip()
                        parsed.add_warning(f"Using fuzzy match for city: {location_str}")
                    elif fuzzy_state_match:
                        parsed.extraction_type = ExtractionType.STATE
                        parsed.location = location_str.strip()
                        parsed.add_warning(f"Using fuzzy match for state: {location_str}")
                    else:
                        parsed.add_error(
                            f"Unknown location: {location_str}. "
                            f"Use /states or /cities to see available options"
                        )
        
        return parsed
    
    def _parse_cities_command(self, command: str) -> ParsedCommand:
        """Parse CITIES command"""
        parsed = ParsedCommand(command_type=CommandType.CITIES, raw_command=command)
        
        # Check if state is specified
        parts = command.split()
        if len(parts) > 1:
            state = " ".join(parts[1:])
            parsed.location = state
        
        return parsed
    
    def _parse_available_command(self, command: str) -> ParsedCommand:
        """Parse AVAILABLE command"""
        parsed = ParsedCommand(command_type=CommandType.AVAILABLE, raw_command=command)
        
        # Check if location is specified
        parts = command.split()
        if len(parts) > 1:
            location = " ".join(parts[1:])
            if location.lower() == "premium":
                parsed.extraction_type = ExtractionType.PREMIUM
            else:
                parsed.location = location
        
        return parsed
    
    def validate_extraction_request(self, request: ExtractionRequest) -> Tuple[bool, List[str]]:
        """
        Validate extraction request against business rules
        
        Args:
            request: Extraction request to validate
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        # Validate amount
        if not self.config.is_valid_extraction_amount(request.amount):
            errors.append(
                f"Invalid amount: {request.amount}. "
                f"Must be between {self.config.min_extraction_amount} "
                f"and {self.config.max_extraction_amount}"
            )
        
        # Validate location requirement
        if request.extraction_type != ExtractionType.PREMIUM and not request.location:
            errors.append(
                f"Location is required for {request.extraction_type.value} extraction"
            )
        
        # Validate location format
        if request.location:
            location = request.location.strip()
            if len(location) < 2:
                errors.append("Location name too short")
            elif len(location) > 100:
                errors.append("Location name too long")
            elif not re.match(r'^[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ\s\-\.]+$', location):
                errors.append("Location contains invalid characters")
        
        is_valid = len(errors) == 0
        
        if not is_valid:
            self.logger.log_validation_error(
                "extraction_request",
                "; ".join(errors),
                request.dict()
            )
        
        return is_valid, errors
    
    def validate_phone_number(self, phone: str) -> Tuple[bool, str]:
        """
        Validate phone number format
        
        Args:
            phone: Phone number to validate
            
        Returns:
            Tuple[bool, str]: (is_valid, formatted_phone_or_error)
        """
        if not phone:
            return False, "Phone number is required"
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Check length
        if len(digits_only) == 10:
            # National format
            return True, f"52{digits_only}"
        elif len(digits_only) == 12 and digits_only.startswith('52'):
            # Already in 12-digit format
            return True, digits_only
        elif len(digits_only) == 13 and digits_only.startswith('521'):
            # E.164 format without +
            return True, digits_only[1:]  # Remove leading 1
        else:
            return False, f"Invalid phone format: {phone}"
    
    def validate_file_name(self, file_name: str) -> Tuple[bool, str]:
        """
        Validate export file name
        
        Args:
            file_name: File name to validate
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not file_name:
            return False, "File name is required"
        
        # Check for invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        if re.search(invalid_chars, file_name):
            return False, "File name contains invalid characters"
        
        # Check length
        if len(file_name) > 255:
            return False, "File name too long"
        
        # Check extension
        valid_extensions = ['.xlsx', '.txt']
        if not any(file_name.lower().endswith(ext) for ext in valid_extensions):
            return False, f"Invalid file extension. Use: {', '.join(valid_extensions)}"
        
        return True, ""
    
    def normalize_location_name(self, location: str) -> str:
        """
        Normalize location name for consistent matching
        
        Args:
            location: Raw location name
            
        Returns:
            str: Normalized location name
        """
        if not location:
            return ""
        
        # Basic normalization
        normalized = location.strip()
        
        # Common replacements for Mexican locations
        replacements = {
            'cdmx': 'Ciudad de México',
            'df': 'Ciudad de México',
            'ciudad de mexico': 'Ciudad de México',
            'nuevo leon': 'Nuevo León',
            'san luis potosi': 'San Luis Potosí',
            'queretaro': 'Querétaro',
            'yucatan': 'Yucatán',
            'michoacan': 'Michoacán'
        }
        
        normalized_lower = normalized.lower()
        for key, value in replacements.items():
            if key == normalized_lower:
                return value
        
        # Title case for proper names
        return normalized.title()
    
    def get_command_help(self) -> str:
        """
        Get help text for all commands
        
        Returns:
            str: Formatted help text
        """
        help_text = """
🤖 **CONTACT EXTRACTOR BOT - COMANDOS DISPONIBLES**

**📤 Extracción de Contactos:**
• `/get [100-10000] premium [xlsx|txt]` - Mejores LADAs
• `/get [100-10000] [estado] [xlsx|txt]` - Por estado específico
• `/get [100-10000] [ciudad] [xlsx|txt]` - Por ciudad específica

**📊 Información del Sistema:**
• `/stats` - Estadísticas del sistema
• `/states` - Lista de estados disponibles
• `/cities [estado]` - Ciudades disponibles (opcionalmente por estado)
• `/available [premium|ubicación]` - Contactos disponibles

**❓ Ayuda:**
• `/help` - Esta ayuda

**💡 Ejemplos:**
• `/get 1000 premium xlsx` - 1000 contactos premium en Excel
• `/get 500 Sinaloa txt` - 500 contactos de Sinaloa en texto
• `/get 2000 Guadalajara xlsx` - 2000 contactos de Guadalajara

**⚠️ Límites:**
• Mínimo: 100 contactos por extracción
• Máximo: 10,000 contactos por extracción
• Máximo diario: 50,000 contactos
• Formatos: xlsx (Excel) o txt (texto plano)
        """
        return help_text.strip()


# Global validator instance
_validator_instance: Optional[BotValidator] = None


def get_validator() -> BotValidator:
    """
    Get global validator instance (singleton)
    
    Returns:
        BotValidator: Validator instance
    """
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = BotValidator()
    return _validator_instance


def parse_command(command: str) -> ParsedCommand:
    """
    Parse command (convenience function)
    
    Args:
        command: Raw command string
        
    Returns:
        ParsedCommand: Parsed command
    """
    return get_validator().parse_command(command)


def validate_extraction_request(request: ExtractionRequest) -> Tuple[bool, List[str]]:
    """
    Validate extraction request (convenience function)
    
    Args:
        request: Extraction request
        
    Returns:
        Tuple[bool, List[str]]: (is_valid, errors)
    """
    return get_validator().validate_extraction_request(request)


# Export main classes and functions
__all__ = [
    "BotValidator",
    "ParsedCommand", 
    "CommandType",
    "ValidationError",
    "get_validator",
    "parse_command",
    "validate_extraction_request"
]