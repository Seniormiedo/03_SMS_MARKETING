"""
Main entry point for Contact Extractor Bot
Professional bot implementation with complete functionality
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add bot directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config
from utils.logger import setup_logging, get_logger
from core.database import get_database_manager, initialize_database, close_database
from core.validators import get_validator, parse_command, CommandType


class ContactExtractorBot:
    """
    Main bot class for contact extraction operations
    Handles command processing and coordinates all services
    """
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger()
        self.db = get_database_manager()
        self.validator = get_validator()
        self.is_running = False
    
    async def initialize(self):
        """Initialize bot components"""
        try:
            self.logger.info("Initializing Contact Extractor Bot...")
            
            # Test database connection
            if not self.db.test_connection():
                raise Exception("Database connection failed")
            
            # Load location data for validation
            await self._load_location_data()
            
            self.is_running = True
            self.logger.info("✅ Bot initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize bot: {e}")
            raise
    
    async def _load_location_data(self):
        """Load states, cities, and premium locations from database"""
        try:
            states = self.db.get_available_states()
            cities = self.db.get_available_cities()
            premium_states = self.db.get_premium_states()
            
            self.validator.set_known_locations(states, cities, premium_states)
            
            self.logger.info(
                f"Loaded location data: {len(states)} states, "
                f"{len(cities)} cities, {len(premium_states)} premium states"
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to load location data: {e}")
    
    async def process_command(self, command: str) -> str:
        """
        Process bot command and return response
        
        Args:
            command: Raw command string
            
        Returns:
            str: Bot response message
        """
        if not self.is_running:
            return "❌ Bot is not initialized. Please restart."
        
        try:
            # Parse and validate command
            parsed = self.validator.parse_command(command)
            
            # Handle validation errors
            if not parsed.is_valid:
                error_msg = "❌ **ERRORES DE VALIDACIÓN:**\n"
                for error in parsed.errors:
                    error_msg += f"• {error}\n"
                return error_msg
            
            # Add warnings if any
            response = ""
            if parsed.warnings:
                response += "⚠️ **ADVERTENCIAS:**\n"
                for warning in parsed.warnings:
                    response += f"• {warning}\n"
                response += "\n"
            
            # Route to appropriate handler
            if parsed.command_type == CommandType.GET:
                return await self._handle_get_command(parsed)
            elif parsed.command_type == CommandType.HELP:
                return self._handle_help_command()
            elif parsed.command_type == CommandType.STATS:
                return await self._handle_stats_command()
            elif parsed.command_type == CommandType.STATES:
                return self._handle_states_command()
            elif parsed.command_type == CommandType.CITIES:
                return self._handle_cities_command(parsed.location)
            elif parsed.command_type == CommandType.AVAILABLE:
                return await self._handle_available_command(parsed)
            else:
                return "❌ Comando no reconocido. Use /help para ver comandos disponibles."
                
        except Exception as e:
            self.logger.error(f"Error processing command '{command}': {e}")
            return f"❌ Error interno del bot: {str(e)}"
    
    async def _handle_get_command(self, parsed) -> str:
        """Handle GET command for contact extraction"""
        try:
            # Convert to extraction request
            request = parsed.to_extraction_request()
            if not request:
                return "❌ Error interno: no se pudo crear la solicitud de extracción."
            
            # Log the extraction request
            self.logger.log_extraction_request(
                request.extraction_type.value,
                request.amount,
                request.location,
                request.export_format.value
            )
            
            # For now, return a placeholder response
            # In Phase 2, this will be implemented with actual extraction logic
            response = f"🚧 **COMANDO PROCESADO (FASE 1 - INFRAESTRUCTURA)**\n\n"
            response += f"📋 **Detalles de la Solicitud:**\n"
            response += f"• Tipo: {request.extraction_type.value.upper()}\n"
            response += f"• Cantidad: {request.amount:,} contactos\n"
            response += f"• Ubicación: {request.location or 'Premium LADAs'}\n"
            response += f"• Formato: {request.export_format.value.upper()}\n\n"
            
            response += f"⏳ **Estado:** Infraestructura completada\n"
            response += f"📅 **Próxima Fase:** Implementación de extracción (Fase 2)\n\n"
            
            response += f"✅ **Validaciones Pasadas:**\n"
            response += f"• Formato de comando correcto\n"
            response += f"• Cantidad dentro de límites permitidos\n"
            response += f"• Tipo de extracción válido\n"
            response += f"• Formato de exportación válido\n\n"
            
            response += f"🔧 **Componentes Listos:**\n"
            response += f"• Sistema de configuración\n"
            response += f"• Conexión a base de datos\n"
            response += f"• Sistema de logging y auditoría\n"
            response += f"• Validaciones de entrada\n"
            response += f"• Modelos de datos\n"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in GET command handler: {e}")
            return f"❌ Error procesando comando GET: {str(e)}"
    
    def _handle_help_command(self) -> str:
        """Handle HELP command"""
        return self.validator.get_command_help()
    
    async def _handle_stats_command(self) -> str:
        """Handle STATS command"""
        try:
            # For now, return basic system stats
            # In Phase 2, this will include real extraction statistics
            stats = f"📊 **ESTADÍSTICAS DEL SISTEMA**\n\n"
            stats += f"🤖 **Bot:**\n"
            stats += f"• Nombre: {self.config.bot_name}\n"
            stats += f"• Versión: {self.config.bot_version}\n"
            stats += f"• Entorno: {self.config.bot_environment}\n"
            stats += f"• Estado: {'✅ Activo' if self.is_running else '❌ Inactivo'}\n\n"
            
            stats += f"🗄️ **Base de Datos:**\n"
            stats += f"• Host: {self.config.db_host}:{self.config.db_port}\n"
            stats += f"• Base: {self.config.db_name}\n"
            stats += f"• Conexión: {'✅ Activa' if self.db.test_connection() else '❌ Fallida'}\n\n"
            
            stats += f"⚙️ **Configuración:**\n"
            stats += f"• Rango extracción: {self.config.min_extraction_amount:,} - {self.config.max_extraction_amount:,}\n"
            stats += f"• Límite diario: {self.config.max_daily_extractions:,}\n"
            stats += f"• Límite por hora: {self.config.max_hourly_extractions}\n\n"
            
            stats += f"📁 **Archivos:**\n"
            stats += f"• Directorio exportación: {self.config.export_path}\n"
            stats += f"• Directorio logs: {self.config.log_path}\n"
            stats += f"• Retención: {self.config.file_retention_days} días\n\n"
            
            stats += f"🔧 **Fase Actual:** 1 - Infraestructura Base ✅\n"
            stats += f"📅 **Próxima Fase:** 2 - Funcionalidad Core"
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error in STATS command handler: {e}")
            return f"❌ Error obteniendo estadísticas: {str(e)}"
    
    def _handle_states_command(self) -> str:
        """Handle STATES command"""
        try:
            states = self.db.get_available_states()
            premium_states = self.db.get_premium_states()
            
            if not states:
                return "❌ No se pudieron cargar los estados disponibles."
            
            response = f"🗺️ **ESTADOS DISPONIBLES** ({len(states)} total)\n\n"
            
            if premium_states:
                response += f"⭐ **Estados Premium (Top 10):**\n"
                for i, state in enumerate(premium_states, 1):
                    response += f"{i:2d}. {state}\n"
                response += "\n"
            
            response += f"📍 **Todos los Estados:**\n"
            for i, state in enumerate(states, 1):
                marker = "⭐" if state in premium_states else "•"
                response += f"{marker} {state}\n"
                if i % 10 == 0 and i < len(states):
                    response += "\n"
            
            response += f"\n💡 **Uso:** `/get [cantidad] [estado] [xlsx|txt]`"
            return response
            
        except Exception as e:
            self.logger.error(f"Error in STATES command handler: {e}")
            return f"❌ Error obteniendo estados: {str(e)}"
    
    def _handle_cities_command(self, state: Optional[str] = None) -> str:
        """Handle CITIES command"""
        try:
            if state:
                cities = self.db.get_available_cities(state)
                title = f"🏙️ **CIUDADES DE {state.upper()}**"
            else:
                cities = self.db.get_available_cities()
                title = f"🏙️ **TODAS LAS CIUDADES DISPONIBLES**"
            
            if not cities:
                if state:
                    return f"❌ No se encontraron ciudades para el estado: {state}"
                else:
                    return "❌ No se pudieron cargar las ciudades disponibles."
            
            response = f"{title} ({len(cities)} total)\n\n"
            
            # Show cities in columns
            for i, city in enumerate(cities, 1):
                response += f"• {city}\n"
                if i % 15 == 0 and i < len(cities):
                    response += "\n"
            
            response += f"\n💡 **Uso:** `/get [cantidad] [ciudad] [xlsx|txt]`"
            return response
            
        except Exception as e:
            self.logger.error(f"Error in CITIES command handler: {e}")
            return f"❌ Error obteniendo ciudades: {str(e)}"
    
    async def _handle_available_command(self, parsed) -> str:
        """Handle AVAILABLE command"""
        try:
            response = f"📊 **DISPONIBILIDAD DE CONTACTOS**\n\n"
            
            if parsed.extraction_type and parsed.extraction_type.value == "premium":
                # Check premium availability
                response += f"⭐ **Contactos Premium:**\n"
                response += f"• Estado: Disponible\n"
                response += f"• Fuente: Top 10 LADAs por ICPTH\n\n"
                response += f"🔍 **Para cantidad específica, use:**\n"
                response += f"`/get [cantidad] premium [xlsx|txt]`"
                
            elif parsed.location:
                # Check specific location availability
                location = parsed.location
                response += f"📍 **Contactos en {location.title()}:**\n"
                response += f"• Estado: Verificando disponibilidad...\n"
                response += f"• Ubicación: {location}\n\n"
                response += f"🔍 **Para extraer, use:**\n"
                response += f"`/get [cantidad] {location} [xlsx|txt]`"
                
            else:
                # General availability
                response += f"📈 **Disponibilidad General:**\n"
                response += f"• Estados disponibles: {len(self.db.get_available_states())}\n"
                response += f"• Ciudades disponibles: {len(self.db.get_available_cities())}\n"
                response += f"• Estados premium: {len(self.db.get_premium_states())}\n\n"
                response += f"💡 **Comandos útiles:**\n"
                response += f"• `/available premium` - Disponibilidad premium\n"
                response += f"• `/available [ubicación]` - Disponibilidad específica\n"
                response += f"• `/states` - Ver todos los estados\n"
                response += f"• `/cities` - Ver todas las ciudades"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in AVAILABLE command handler: {e}")
            return f"❌ Error verificando disponibilidad: {str(e)}"
    
    async def shutdown(self):
        """Shutdown bot gracefully"""
        try:
            self.logger.info("Shutting down Contact Extractor Bot...")
            self.is_running = False
            await close_database()
            self.logger.info("✅ Bot shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


# Interactive mode for testing
async def interactive_mode():
    """Run bot in interactive mode for testing"""
    print("🤖 Contact Extractor Bot - Interactive Mode")
    print("=" * 50)
    
    # Initialize bot
    bot = ContactExtractorBot()
    
    try:
        await bot.initialize()
        print("✅ Bot initialized successfully!")
        print("💡 Type commands or 'quit' to exit")
        print("📝 Example: /get 1000 premium xlsx")
        print("-" * 50)
        
        while True:
            try:
                command = input("\n🤖 Bot> ").strip()
                
                if command.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not command:
                    continue
                
                # Process command
                response = await bot.process_command(command)
                print(f"\n{response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    finally:
        await bot.shutdown()


# Main execution
async def main():
    """Main entry point"""
    # Setup logging
    setup_logging()
    logger = get_logger()
    
    try:
        logger.info("Starting Contact Extractor Bot...")
        
        # Check if running interactively
        if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
            await interactive_mode()
        else:
            # Initialize bot for API/service mode
            bot = ContactExtractorBot()
            await bot.initialize()
            
            logger.info("✅ Bot ready for service mode")
            logger.info("🔧 Phase 1 (Infrastructure) completed successfully")
            logger.info("📅 Ready for Phase 2 (Core Functionality) implementation")
            
            # Keep running (in real implementation, this would be a web server or message handler)
            print("🤖 Bot is running... Press Ctrl+C to stop")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Shutting down...")
            finally:
                await bot.shutdown()
                
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())