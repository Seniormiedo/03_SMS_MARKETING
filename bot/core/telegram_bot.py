"""
Telegram Bot integration for Contact Extractor Bot
Professional Telegram bot implementation with file upload capabilities
"""

import asyncio
import io
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from telegram.constants import ParseMode

from config import get_config
from utils.logger import get_logger
from core.validators import get_validator, parse_command, CommandType
from core.database import get_database_manager
from services.contact_service import ContactService
from services.export_service import ExportService


class TelegramContactBot:
    """
    Professional Telegram bot for contact extraction
    Handles all Telegram interactions and file uploads
    """
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger()
        self.validator = get_validator()
        self.db = get_database_manager()
        self.contact_service = ContactService()
        self.export_service = ExportService()
        
        # Bot application
        self.application: Optional[Application] = None
        self.is_running = False
        
        # User session tracking
        self.user_sessions: Dict[int, Dict[str, Any]] = {}
        
        # Rate limiting
        self.user_last_command: Dict[int, datetime] = {}
    
    async def initialize(self):
        """Initialize Telegram bot and services"""
        try:
            self.logger.info("Initializing Telegram Contact Extractor Bot...")
            
            # Initialize database connection
            if not self.db.test_connection():
                raise Exception("Database connection failed")
            
            # Load location data for validation
            await self._load_location_data()
            
            # Initialize services
            await self.contact_service.initialize()
            await self.export_service.initialize()
            
            # Create Telegram application
            self.application = Application.builder().token(self.config.telegram_bot_token).build()
            
            # Register handlers
            await self._register_handlers()
            
            # Set bot commands
            await self._set_bot_commands()
            
            self.is_running = True
            self.logger.info("✅ Telegram bot initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Telegram bot: {e}")
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
    
    async def _register_handlers(self):
        """Register all Telegram handlers"""
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("get", self.get_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("states", self.states_command))
        self.application.add_handler(CommandHandler("cities", self.cities_command))
        self.application.add_handler(CommandHandler("available", self.available_command))
        
        # Callback query handler for inline keyboards
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Message handler for text commands
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_message)
        )
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def _set_bot_commands(self):
        """Set bot commands in Telegram menu"""
        commands = [
            BotCommand("start", "🚀 Iniciar bot"),
            BotCommand("help", "❓ Ayuda y comandos"),
            BotCommand("get", "📤 Extraer contactos"),
            BotCommand("stats", "📊 Estadísticas del sistema"),
            BotCommand("states", "🗺️ Estados disponibles"),
            BotCommand("cities", "🏙️ Ciudades disponibles"),
            BotCommand("available", "📈 Disponibilidad de contactos"),
        ]
        
        await self.application.bot.set_my_commands(commands)
    
    def _check_rate_limit(self, user_id: int) -> bool:
        """Check if user is rate limited"""
        if not self.config.enable_rate_limiting:
            return True
        
        now = datetime.now()
        last_command = self.user_last_command.get(user_id)
        
        if last_command:
            time_diff = (now - last_command).total_seconds()
            if time_diff < 2:  # 2 seconds between commands
                return False
        
        self.user_last_command[user_id] = now
        return True
    
    def _get_user_session(self, user_id: int) -> Dict[str, Any]:
        """Get or create user session"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'extractions_today': 0,
                'last_extraction': None,
                'pending_confirmation': None
            }
        return self.user_sessions[user_id]
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        welcome_text = f"""
🤖 **¡Bienvenido al Contact Extractor Bot!**

¡Hola {user.first_name}! Soy tu bot especializado en extracción de contactos SMS para México.

🎯 **¿Qué puedo hacer?**
• Extraer contactos por mejores LADAs (premium)
• Filtrar por estado o ciudad específica
• Generar archivos Excel (.xlsx) o texto (.txt)
• Controlar uso y evitar duplicados

📋 **Comandos principales:**
• `/get 1000 premium xlsx` - Extraer contactos premium
• `/get 500 Sinaloa txt` - Extraer por estado
• `/help` - Ver todos los comandos
• `/stats` - Estadísticas del sistema

⚡ **Límites:**
• Rango: {self.config.min_extraction_amount:,} - {self.config.max_extraction_amount:,} contactos
• Máximo diario: {self.config.max_daily_extractions:,} contactos

🚀 **¡Comienza ahora con** `/help` **para ver todos los comandos!**
        """
        
        # Create inline keyboard for quick actions
        keyboard = [
            [InlineKeyboardButton("📤 Extraer Premium", callback_data="quick_premium")],
            [InlineKeyboardButton("🗺️ Ver Estados", callback_data="quick_states")],
            [InlineKeyboardButton("📊 Estadísticas", callback_data="quick_stats")],
            [InlineKeyboardButton("❓ Ayuda Completa", callback_data="quick_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
        # Log user interaction
        self.logger.audit("USER_START", {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "language_code": user.language_code
        })
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = self.validator.get_command_help()
        
        # Add Telegram-specific information
        help_text += f"""

🤖 **INFORMACIÓN DEL BOT:**
• Bot: @{self.config.telegram_bot_username}
• Versión: {self.config.bot_version}
• Archivos máximo: {self.config.telegram_max_file_size_mb} MB

💡 **Consejos de Uso:**
• Los archivos se envían directamente por Telegram
• Los contactos extraídos se marcan como usados
• Usa comandos rápidos con los botones de abajo

🔒 **Seguridad:**
• Todas las operaciones quedan registradas
• Control automático de límites diarios
• Validaciones completas de entrada
        """
        
        keyboard = [
            [InlineKeyboardButton("📤 Extraer Ahora", callback_data="quick_extract")],
            [InlineKeyboardButton("📊 Ver Stats", callback_data="quick_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def get_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /get command"""
        user_id = update.effective_user.id
        
        # Check rate limiting
        if not self._check_rate_limit(user_id):
            await update.message.reply_text(
                "⏳ **Espera un momento antes del siguiente comando**\n"
                "Rate limit: 1 comando cada 2 segundos"
            )
            return
        
        # Parse command arguments
        args = context.args
        if len(args) < 3:
            await update.message.reply_text(
                "❌ **Formato incorrecto**\n\n"
                "**Uso correcto:**\n"
                "`/get [cantidad] [premium|estado|ciudad] [xlsx|txt]`\n\n"
                "**Ejemplos:**\n"
                "• `/get 1000 premium xlsx`\n"
                "• `/get 500 Sinaloa txt`\n"
                "• `/get 2000 Guadalajara xlsx`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Reconstruct command
        command = f"/get {' '.join(args)}"
        
        # Process extraction
        await self._process_extraction_command(update, command)
    
    async def _process_extraction_command(self, update: Update, command: str):
        """Process extraction command"""
        user_id = update.effective_user.id
        
        try:
            # Parse and validate command
            parsed = self.validator.parse_command(command)
            
            if not parsed.is_valid:
                error_msg = "❌ **ERRORES DE VALIDACIÓN:**\n"
                for error in parsed.errors:
                    error_msg += f"• {error}\n"
                
                await update.message.reply_text(error_msg, parse_mode=ParseMode.MARKDOWN)
                return
            
            # Convert to extraction request
            request = parsed.to_extraction_request()
            if not request:
                await update.message.reply_text(
                    "❌ **Error interno:** No se pudo procesar la solicitud"
                )
                return
            
            # Check if confirmation is required
            if self.config.should_require_confirmation(request.amount):
                await self._request_confirmation(update, request)
                return
            
            # Process extraction immediately
            await self._execute_extraction(update, request)
            
        except Exception as e:
            self.logger.error(f"Error processing extraction command: {e}")
            await update.message.reply_text(
                f"❌ **Error interno:** {str(e)}"
            )
    
    async def _request_confirmation(self, update: Update, request):
        """Request confirmation for large extractions"""
        user_id = update.effective_user.id
        session = self._get_user_session(user_id)
        session['pending_confirmation'] = request
        
        confirmation_text = f"""
⚠️ **CONFIRMACIÓN REQUERIDA**

📋 **Detalles de la Extracción:**
• **Cantidad:** {request.amount:,} contactos
• **Tipo:** {str(request.extraction_type).title()}
• **Ubicación:** {request.location or 'Premium LADAs'}
• **Formato:** {str(request.export_format).upper()}

🔒 **Esta es una extracción grande que requiere confirmación.**

¿Deseas continuar?
        """
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirmar", callback_data="confirm_extraction")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel_extraction")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            confirmation_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def _execute_extraction(self, update: Update, request):
        """Execute the actual extraction"""
        user_id = update.effective_user.id
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            "⏳ **Procesando extracción...**\n"
            f"• Extrayendo {request.amount:,} contactos\n"
            f"• Tipo: {str(request.extraction_type).title()}\n"
            "• Por favor espera..."
        )
        
        try:
            # Execute extraction using services
            result = await self.contact_service.extract_contacts(request)
            
            if not result.is_successful():
                await processing_msg.edit_text(
                    f"❌ **Error en la extracción:**\n{result.error_message}"
                )
                return
            
            # Generate and upload file
            await self._upload_result_file(update, result, processing_msg)
            
            # Update user session
            session = self._get_user_session(user_id)
            session['extractions_today'] += result.total_extracted
            session['last_extraction'] = datetime.now()
            
            # Log successful extraction
            self.logger.audit("EXTRACTION_SUCCESS", {
                "user_id": user_id,
                "extraction_type": str(request.extraction_type),
                "amount_requested": request.amount,
                "amount_extracted": result.total_extracted,
                "format": str(request.export_format),
                "location": request.location
            })
            
        except Exception as e:
            self.logger.error(f"Extraction failed: {e}")
            await processing_msg.edit_text(
                f"❌ **Error durante la extracción:**\n{str(e)}"
            )
    
    async def _upload_result_file(self, update: Update, result, processing_msg):
        """Upload result file to Telegram"""
        try:
            if not result.file_path or not Path(result.file_path).exists():
                await processing_msg.edit_text("❌ **Error:** Archivo no generado correctamente")
                return
            
            file_path = Path(result.file_path)
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            
            # Check file size limit
            if file_size_mb > self.config.telegram_max_file_size_mb:
                await processing_msg.edit_text(
                    f"❌ **Archivo demasiado grande:** {file_size_mb:.1f} MB\n"
                    f"Límite máximo: {self.config.telegram_max_file_size_mb} MB\n"
                    "Intenta con una cantidad menor."
                )
                return
            
            # Prepare success message
            success_text = f"""
✅ **EXTRACCIÓN COMPLETADA**

📊 **Resultados:**
• **Extraídos:** {result.total_extracted:,} contactos
• **Formato:** {str(result.request.export_format).upper()}
• **Tamaño:** {file_size_mb:.1f} MB
• **Tiempo:** {result.get_performance_summary()['total_time']:.1f}s

📁 **Archivo adjunto:** {file_path.name}
            """
            
            # Upload file
            with open(file_path, 'rb') as file:
                await update.message.reply_document(
                    document=file,
                    filename=file_path.name,
                    caption=success_text,
                    parse_mode=None  # Disable markdown parsing to avoid entity errors
                )
            
            # Delete processing message
            await processing_msg.delete()
            
            # Clean up file
            try:
                file_path.unlink()
            except:
                pass
            
        except Exception as e:
            self.logger.error(f"File upload failed: {e}")
            await processing_msg.edit_text(
                f"❌ **Error subiendo archivo:**\n{str(e)}"
            )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user_id = update.effective_user.id
        session = self._get_user_session(user_id)
        
        # Get system stats (placeholder for now)
        stats_text = f"""
📊 **ESTADÍSTICAS DEL SISTEMA**

🤖 **Bot:**
• Nombre: {self.config.bot_name}
• Versión: {self.config.bot_version}
• Estado: ✅ Activo

👤 **Tu Actividad:**
• Extracciones hoy: {session['extractions_today']:,}
• Última extracción: {session['last_extraction'].strftime('%H:%M') if session['last_extraction'] else 'Nunca'}

⚙️ **Límites:**
• Rango: {self.config.min_extraction_amount:,} - {self.config.max_extraction_amount:,}
• Máximo diario: {self.config.max_daily_extractions:,}
• Restante hoy: {self.config.max_daily_extractions - session['extractions_today']:,}

🗄️ **Base de Datos:**
• Estados disponibles: {len(self.db.get_available_states())}
• Ciudades disponibles: {len(self.db.get_available_cities())}
• Estados premium: {len(self.db.get_premium_states())}
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 Actualizar", callback_data="refresh_stats")],
            [InlineKeyboardButton("📤 Extraer Ahora", callback_data="quick_extract")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def states_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /states command"""
        states = self.db.get_available_states()
        premium_states = self.db.get_premium_states()
        
        if not states:
            await update.message.reply_text("❌ No se pudieron cargar los estados")
            return
        
        # Split states into chunks for better display
        states_text = f"🗺️ **ESTADOS DISPONIBLES** ({len(states)} total)\n\n"
        
        states_text += "⭐ **Estados Premium (Top 10):**\n"
        for i, state in enumerate(premium_states[:10], 1):
            states_text += f"{i:2d}. {state}\n"
        
        states_text += f"\n💡 **Uso:** `/get [cantidad] [estado] [xlsx|txt]`"
        
        keyboard = [
            [InlineKeyboardButton("🏙️ Ver Ciudades", callback_data="show_cities")],
            [InlineKeyboardButton("📤 Extraer Premium", callback_data="extract_premium")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            states_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def cities_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cities command"""
        cities = self.db.get_available_cities()
        
        if not cities:
            await update.message.reply_text("❌ No se pudieron cargar las ciudades")
            return
        
        # Show top cities
        cities_text = f"🏙️ **CIUDADES PRINCIPALES** (Top 20)\n\n"
        
        for i, city in enumerate(cities[:20], 1):
            cities_text += f"{i:2d}. {city}\n"
        
        cities_text += f"\n📊 **Total disponibles:** {len(cities)}"
        cities_text += f"\n💡 **Uso:** `/get [cantidad] [ciudad] [xlsx|txt]`"
        
        keyboard = [
            [InlineKeyboardButton("🗺️ Ver Estados", callback_data="show_states")],
            [InlineKeyboardButton("📈 Disponibilidad", callback_data="show_availability")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            cities_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def available_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /available command"""
        availability_text = f"""
📈 **DISPONIBILIDAD DE CONTACTOS**

⭐ **Premium (Mejores LADAs):**
• Estados: {len(self.db.get_premium_states())}
• Estimación: ~2.5M contactos

📍 **Por Ubicación:**
• Estados totales: {len(self.db.get_available_states())}
• Ciudades totales: {len(self.db.get_available_cities())}

💡 **Comandos útiles:**
• `/get 1000 premium xlsx` - Contactos premium
• `/get 500 [estado] txt` - Por estado
• `/get 1000 [ciudad] xlsx` - Por ciudad
        """
        
        keyboard = [
            [InlineKeyboardButton("📤 Extraer Premium", callback_data="extract_premium")],
            [InlineKeyboardButton("🗺️ Ver Estados", callback_data="show_states")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            availability_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "quick_premium":
            await query.message.reply_text(
                "📤 **Extracción Premium**\n\n"
                "Usa el comando:\n"
                "`/get 1000 premium xlsx`\n\n"
                "Cambia la cantidad (100-10000) y formato (xlsx/txt) según necesites.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "quick_stats":
            await self.stats_command(update, context)
        
        elif data == "quick_help":
            await self.help_command(update, context)
        
        elif data == "confirm_extraction":
            user_id = query.from_user.id
            session = self._get_user_session(user_id)
            request = session.get('pending_confirmation')
            
            if request:
                session['pending_confirmation'] = None
                await query.message.edit_text("✅ **Confirmado. Procesando extracción...**")
                await self._execute_extraction(update, request)
            else:
                await query.message.edit_text("❌ **Error:** No hay extracción pendiente")
        
        elif data == "cancel_extraction":
            user_id = query.from_user.id
            session = self._get_user_session(user_id)
            session['pending_confirmation'] = None
            await query.message.edit_text("❌ **Extracción cancelada**")
    
    async def text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages that might be commands"""
        text = update.message.text.strip()
        
        # Check if it looks like a get command
        if text.lower().startswith('/get') or text.lower().startswith('get'):
            if not text.startswith('/'):
                text = '/' + text
            
            await self._process_extraction_command(update, text)
        else:
            await update.message.reply_text(
                "❓ **Comando no reconocido**\n\n"
                "Usa `/help` para ver todos los comandos disponibles.\n\n"
                "**Ejemplo de extracción:**\n"
                "`/get 1000 premium xlsx`",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        self.logger.error(f"Telegram bot error: {context.error}")
        
        if update and update.message:
            await update.message.reply_text(
                "❌ **Error interno del bot**\n"
                "El error ha sido registrado. Intenta nuevamente en unos momentos."
            )
    
    async def run(self):
        """Run the Telegram bot"""
        if not self.application:
            raise Exception("Bot not initialized")
        
        self.logger.info("🚀 Starting Telegram Contact Extractor Bot...")
        self.logger.info(f"Bot username: @{self.config.telegram_bot_username}")
        
        # Start the bot
        await self.application.run_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )
    
    async def shutdown(self):
        """Shutdown the bot gracefully"""
        try:
            self.logger.info("Shutting down Telegram bot...")
            
            if self.application:
                await self.application.shutdown()
            
            self.is_running = False
            self.logger.info("✅ Telegram bot shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


# Global bot instance
_telegram_bot: Optional[TelegramContactBot] = None


def get_telegram_bot() -> TelegramContactBot:
    """Get global Telegram bot instance"""
    global _telegram_bot
    if _telegram_bot is None:
        _telegram_bot = TelegramContactBot()
    return _telegram_bot


# Export main classes
__all__ = [
    "TelegramContactBot",
    "get_telegram_bot"
]