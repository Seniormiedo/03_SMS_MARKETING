"""
Formatters and utilities for Contact Extractor Bot
Phone number formatting, file naming, and data processing utilities
"""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from phonenumbers import parse, format_number, PhoneNumberFormat, is_valid_number


class PhoneFormatter:
    """Professional phone number formatting utilities"""
    
    @staticmethod
    def format_to_digits(phone: str, digits: int = 12) -> str:
        """
        Format phone number to specified digit count
        
        Args:
            phone: Phone number in any format
            digits: Target digit count (10, 12, or 13)
            
        Returns:
            str: Formatted phone number
        """
        if not phone:
            return ""
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Handle different input formats
        if digits_only.startswith('521'):
            # E.164 format with country code and mobile prefix
            digits_only = '52' + digits_only[3:]
        elif digits_only.startswith('1') and len(digits_only) == 11:
            # US format, convert to Mexican
            digits_only = '52' + digits_only[1:]
        elif len(digits_only) == 10:
            # National format, add country code
            digits_only = '52' + digits_only
        
        # Format to requested digits
        if digits == 10 and len(digits_only) >= 12:
            return digits_only[-10:]  # Last 10 digits
        elif digits == 12 and len(digits_only) >= 12:
            return digits_only[-12:]  # Last 12 digits (52xxxxxxxxxx)
        elif digits == 13 and len(digits_only) >= 12:
            return '+' + digits_only[-12:]  # E.164 format
        
        return digits_only
    
    @staticmethod
    def validate_mexican_phone(phone: str) -> bool:
        """
        Validate Mexican phone number
        
        Args:
            phone: Phone number to validate
            
        Returns:
            bool: True if valid Mexican phone
        """
        try:
            # Try to parse as Mexican number
            parsed = parse(phone, "MX")
            return is_valid_number(parsed)
        except:
            return False
    
    @staticmethod
    def format_for_display(phone: str) -> str:
        """
        Format phone for human-readable display
        
        Args:
            phone: Phone number
            
        Returns:
            str: Formatted display number
        """
        try:
            parsed = parse(phone, "MX")
            return format_number(parsed, PhoneNumberFormat.NATIONAL)
        except:
            return phone


class FileNameGenerator:
    """Professional file name generation utilities"""
    
    @staticmethod
    def generate_extraction_filename(
        extraction_type: str,
        amount: int,
        location: Optional[str] = None,
        format_ext: str = "xlsx"
    ) -> str:
        """
        Generate unique filename for extraction
        
        Args:
            extraction_type: Type of extraction (premium, state, city)
            amount: Number of contacts
            location: Location name (if applicable)
            format_ext: File extension
            
        Returns:
            str: Generated filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Clean location name for filename
        if location:
            clean_location = re.sub(r'[^\w\s-]', '', location)
            clean_location = re.sub(r'[-\s]+', '_', clean_location)
            location_part = f"_{clean_location}"
        else:
            location_part = ""
        
        return f"{extraction_type}_{amount}{location_part}_{timestamp}.{format_ext}"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for filesystem compatibility
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        # Remove invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove multiple underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        # Ensure reasonable length
        if len(sanitized) > 200:
            name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
            sanitized = name[:190] + ('.' + ext if ext else '')
        
        return sanitized


class DataFormatter:
    """Data formatting utilities for exports"""
    
    @staticmethod
    def format_contact_for_xlsx(contact: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format contact data for XLSX export
        
        Args:
            contact: Contact data dictionary
            
        Returns:
            dict: Formatted contact data
        """
        phone_12 = PhoneFormatter.format_to_digits(
            contact.get('phone_national', ''), 12
        )
        
        city = contact.get('city', '').upper() if contact.get('city') else 'UNKNOWN'
        
        return {
            'Number': phone_12,
            'Content': city
        }
    
    @staticmethod
    def format_contact_for_txt(contact: Dict[str, Any]) -> str:
        """
        Format contact data for TXT export
        
        Args:
            contact: Contact data dictionary
            
        Returns:
            str: Formatted phone number
        """
        return PhoneFormatter.format_to_digits(
            contact.get('phone_national', ''), 12
        )
    
    @staticmethod
    def format_location_name(location: str) -> str:
        """
        Format location name consistently
        
        Args:
            location: Raw location name
            
        Returns:
            str: Formatted location name
        """
        if not location:
            return "UNKNOWN"
        
        # Common Mexican location mappings
        mappings = {
            'cdmx': 'Ciudad de México',
            'df': 'Ciudad de México',
            'ciudad de mexico': 'Ciudad de México',
            'nuevo leon': 'Nuevo León',
            'san luis potosi': 'San Luis Potosí',
            'queretaro': 'Querétaro',
            'yucatan': 'Yucatán',
            'michoacan': 'Michoacán'
        }
        
        location_lower = location.lower().strip()
        
        # Check for exact mappings
        if location_lower in mappings:
            return mappings[location_lower]
        
        # Title case for proper names
        return location.title().strip()


class ProgressFormatter:
    """Progress and status formatting utilities"""
    
    @staticmethod
    def format_progress_bar(current: int, total: int, width: int = 30) -> str:
        """
        Create ASCII progress bar
        
        Args:
            current: Current progress
            total: Total items
            width: Bar width in characters
            
        Returns:
            str: Formatted progress bar
        """
        if total == 0:
            return "[" + "=" * width + "] 100%"
        
        progress = current / total
        filled = int(width * progress)
        bar = "=" * filled + "-" * (width - filled)
        percentage = int(progress * 100)
        
        return f"[{bar}] {percentage}%"
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            str: Formatted size (e.g., "1.5 MB")
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Format duration in human-readable format
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            str: Formatted duration
        """
        if seconds < 1:
            return f"{seconds * 1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.0f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"


# Export main classes
__all__ = [
    "PhoneFormatter",
    "FileNameGenerator", 
    "DataFormatter",
    "ProgressFormatter"
]