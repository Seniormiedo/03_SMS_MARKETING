"""
Telegram Bot PRODUCCIÓN - Fase 2 Completa
Bot funcional conectado a base de datos real con 36M registros
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import time

# Add bot directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

from config import get_config
from utils.logger import setup_logging, get_logger
from core.validators import get_validator, parse_command, CommandType
from core.database import get_database_manager
from services.contact_service import ContactService
from services.export_service import ExportService


class TelegramProductionBot:
    """
    Bot de producción para Telegram con conexión real a base de datos
    Maneja extracciones reales de contactos desde PostgreSQL
    """
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger()
        self.validator = get_validator()
        self.db = get_database_manager()
        self.contact_service = ContactService()
        self.export_service = ExportService()
        
        # SECURITY: Authorized group ID only
        self.AUTHORIZED_GROUP_ID = -1002346121007
        
        # User sessions for production tracking
        self.user_sessions: Dict[int, Dict[str, Any]] = {}
        
        # Rate limiting
        self.user_last_command: Dict[int, datetime] = {}
        
        # Active extractions tracking
        self.active_extractions: Dict[int, bool] = {}
        
        # Application
        self.application = None
    
    def _is_authorized_group(self, update: Update) -> bool:
        """
        Check if the message comes from the authorized group
        SECURITY: Only respond to messages from the specific group ID
        """
        if not update.effective_chat:
            return False
        
        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        
        # Log all incoming messages for security monitoring
        self.logger.info(
            f"SECURITY CHECK - Chat ID: {chat_id}, Type: {chat_type}, "
            f"Authorized: {chat_id == self.AUTHORIZED_GROUP_ID}"
        )
        
        # Only allow messages from the specific authorized group
        if chat_id != self.AUTHORIZED_GROUP_ID:
            self.logger.warning(
                f"UNAUTHORIZED ACCESS ATTEMPT - Chat ID: {chat_id}, "
                f"User: {update.effective_user.id if update.effective_user else 'Unknown'}, "
                f"Username: {update.effective_user.username if update.effective_user else 'Unknown'}"
            )
            return False
        
        return True
    
    def _get_user_session(self, user_id: int) -> Dict[str, Any]:
        """Get or create user session with production tracking"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'extractions_today': 0,
                'contacts_extracted_today': 0,
                'last_extraction': None,
                'production_mode': True,
                'total_extractions': 0,
                'favorite_format': None
            }
        return self.user_sessions[user_id]
    
    def _check_rate_limit(self, user_id: int) -> bool:
        """Enhanced rate limiting for production"""
        if not self.config.enable_rate_limiting:
            return True
        
        now = datetime.now()
        last_command = self.user_last_command.get(user_id)
        
        if last_command:
            time_diff = (now - last_command).total_seconds()
            if time_diff < 3:  # 3 seconds between commands in production
                return False
        
        self.user_last_command[user_id] = now
        return True
    
    def _check_daily_limits(self, user_id: int, requested_amount: int) -> tuple[bool, str]:
        """Check daily extraction limits"""
        session = self._get_user_session(user_id)
        
        # Check daily contact limit
        if session['contacts_extracted_today'] + requested_amount > 50000:
            remaining = 50000 - session['contacts_extracted_today']
            return False, f"Límite diario alcanzado. Restantes hoy: {remaining:,} contactos"
        
        # Check daily extraction count
        if session['extractions_today'] >= 20:
            return False, "Límite de 20 extracciones diarias alcanzado"
        
        return True, ""
    
    async def initialize(self):
        """Initialize production bot with real database"""
        try:
            self.logger.info("Initializing Telegram PRODUCTION Bot...")
            
            # Test database connection
            if not self.db.test_connection():
                raise Exception("Database connection failed - cannot start production bot")
            
            # Initialize services
            await self.contact_service.initialize()
            await self.export_service.initialize()
            
            # Load real location data
            await self._load_real_location_data()
            
            # Create Telegram application
            self.application = Application.builder().token(self.config.telegram_bot_token).build()
            
            # Register handlers
            self._register_handlers()
            await self._set_bot_commands()
            
            self.logger.info("✅ Telegram PRODUCTION bot initialized successfully")
            self.logger.info("🔗 Connected to real database with 36M+ records")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize production bot: {e}")
            raise
    
    async def _load_real_location_data(self):
        """Load real location data from database"""
        try:
            self.logger.info("Loading real location data from database...")
            
            states = self.db.get_available_states()
            cities = self.db.get_available_cities()
            premium_states = self.db.get_premium_states()
            
            self.validator.set_known_locations(states, cities, premium_states)
            
            self.logger.info(
                f"✅ Loaded REAL location data: {len(states)} states, "
                f"{len(cities)} cities, {len(premium_states)} premium states"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to load real location data: {e}")
            # Continue with empty data - will be handled by validators
    
    def _register_handlers(self):
        """Register all production handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("get", self.get_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("states", self.states_command))
        self.application.add_handler(CommandHandler("cities", self.cities_command))
        self.application.add_handler(CommandHandler("available", self.available_command))
        
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_message))
        self.application.add_error_handler(self.error_handler)
    
    async def _set_bot_commands(self):
        """Set production bot commands menu"""
        commands = [
            BotCommand("start", "🚀 Iniciar bot de producción"),
            BotCommand("help", "❓ Ayuda y comandos"),
            BotCommand("get", "📤 Extraer contactos REALES"),
            BotCommand("stats", "📊 Estadísticas en tiempo real"),
            BotCommand("states", "🗺️ Estados con datos reales"),
            BotCommand("cities", "🏙️ Ciudades con contactos"),
            BotCommand("available", "📈 Disponibilidad real"),
        ]
        await self.application.bot.set_my_commands(commands)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Production start command"""
        # SECURITY: Check if message comes from authorized group
        if not self._is_authorized_group(update):
            return  # Silently ignore unauthorized messages
            
        user = update.effective_user
        session = self._get_user_session(user.id)
        
        welcome_text = f"""🚀 *¡Bienvenido al Contact Extractor Bot \\- PRODUCCIÓN\\!*

¡Hola {user.first_name}\\! Bot conectado a base de datos real con *36M\\+ registros*\\.

📊 *Tu Actividad Hoy:*
• Extracciones: {session['extractions_today']}/20
• Contactos extraídos: {session['contacts_extracted_today']:,}/50,000

🎯 *Extracciones REALES:*
• `/get 1000 premium xlsx` \\- Mejores LADAs \\(datos reales\\)
• `/get 500 Sinaloa txt` \\- Por estado \\(datos reales\\)
• `/get 2000 Guadalajara xlsx` \\- Por ciudad \\(datos reales\\)

⚡ *Características de Producción:*
• ✅ Base de datos PostgreSQL real
• ✅ 36M\\+ contactos verificados
• ✅ Marcado automático como OPTED\\_OUT
• ✅ Auditoría completa de extracciones

🔒 *Límites de Producción:*
• Máximo: 10,000 contactos por extracción
• Límite diario: 50,000 contactos
• Extracciones diarias: 20 máximo

🎊 *¡Datos 100% reales listos para campañas SMS\\!*

📋 *Comandos principales:*
• `/get` \\- Extraer contactos reales
• `/states` \\- Ver estados disponibles  
• `/stats` \\- Estadísticas en tiempo real
• `/help` \\- Ayuda completa"""
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        # Log production user start
        self.logger.audit("PRODUCTION_USER_START", {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "extractions_today": session['extractions_today'],
            "contacts_today": session['contacts_extracted_today']
        })
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Production help command"""
        # SECURITY: Check if message comes from authorized group
        if not self._is_authorized_group(update):
            return  # Silently ignore unauthorized messages
        help_text = """🤖 *CONTACT EXTRACTOR BOT \\- PRODUCCIÓN*

📋 *COMANDOS PRINCIPALES:*

🚀 `/start` \\- Iniciar el bot y ver bienvenida

📤 `/get \\[cantidad\\] \\[ubicación\\] \\[formato\\]`
   • Extrae contactos REALES de la base de datos
   • *Ejemplos:*
     \\- `/get 1000 premium xlsx` \\- 1000 contactos premium en Excel
     \\- `/get 500 Sinaloa txt` \\- 500 contactos de Sinaloa en texto
     \\- `/get 2000 Guadalajara xlsx` \\- 2000 contactos de Guadalajara

📊 `/stats` \\- Estadísticas del sistema y tu actividad

🗺️ `/states` \\- Ver todos los estados disponibles

🏙️ `/cities` \\- Ver ciudades disponibles \\(opcional: `/cities \\[estado\\]`\\)

📈 `/available` \\- Verificar disponibilidad de contactos

❓ `/help` \\- Mostrar esta ayuda

⚡ *CARACTERÍSTICAS DESTACADAS:*
• ✅ Base de datos real con 36M\\+ contactos
• ✅ Solo números móviles verificados
• ✅ Marcado automático como OPTED\\_OUT
• ✅ Auditoría completa de extracciones
• ✅ Formatos XLSX y TXT
• ✅ Límites de seguridad integrados

🔒 *LÍMITES DE PRODUCCIÓN:*
• Cantidad por extracción: 100 \\- 10,000 contactos
• Límite diario personal: 50,000 contactos
• Extracciones diarias: 20 máximo
• Rate limit: 3 segundos entre comandos

💡 *CONSEJOS:*
• Usa `premium` para los mejores contactos por ICPTH
• Los contactos extraídos no se pueden reutilizar
• Revisa `/stats` para ver tu progreso diario
• Contacta soporte si necesitas límites mayores

🎯 *¡Listo para campañas SMS profesionales\\!*"""
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    async def states_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Production states command"""
        # SECURITY: Check if message comes from authorized group
        if not self._is_authorized_group(update):
            return  # Silently ignore unauthorized messages
            
        try:
            states = self.db.get_available_states()
            premium_states = self.db.get_premium_states()
            
            if not states:
                await update.message.reply_text(
                    "❌ **No se pudieron cargar los estados**\n\n"
                    "La base de datos puede estar inicializándose.\n"
                    "Intenta nuevamente en unos momentos."
                )
                return
            
            response = f"🗺️ **ESTADOS CON CONTACTOS REALES** ({len(states)} total)\n\n"
            
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
            
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            self.logger.error(f"Error in states command: {e}")
            await update.message.reply_text(
                "❌ **Error obteniendo estados**\n\n"
                "Error técnico registrado para revisión."
            )
    
    async def cities_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Production cities command"""
        # SECURITY: Check if message comes from authorized group
        if not self._is_authorized_group(update):
            return  # Silently ignore unauthorized messages
            
        try:
            args = context.args
            state = args[0] if args else None
            
            if state:
                cities = self.db.get_available_cities(state)
                title = f"🏙️ **CIUDADES DE {state.upper()} CON CONTACTOS REALES**"
            else:
                cities = self.db.get_available_cities()
                title = f"🏙️ **TODAS LAS CIUDADES CON CONTACTOS REALES**"
            
            if not cities:
                if state:
                    await update.message.reply_text(f"❌ No se encontraron ciudades para: **{state}**")
                else:
                    await update.message.reply_text("❌ No se pudieron cargar las ciudades disponibles.")
                return
            
            response = f"{title} ({len(cities)} total)\n\n"
            
            # Show cities in columns
            for i, city in enumerate(cities, 1):
                response += f"• {city}\n"
                if i % 15 == 0 and i < len(cities):
                    response += "\n"
            
            response += f"\n💡 **Uso:** `/get [cantidad] [ciudad] [xlsx|txt]`"
            
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            self.logger.error(f"Error in cities command: {e}")
            await update.message.reply_text(
                "❌ **Error obteniendo ciudades**\n\n"
                "Error técnico registrado para revisión."
            )
    
    async def available_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Production available command"""
        # SECURITY: Check if message comes from authorized group
        if not self._is_authorized_group(update):
            return  # Silently ignore unauthorized messages
            
        try:
            args = context.args
            location = args[0] if args else None
            
            response = f"📊 **DISPONIBILIDAD DE CONTACTOS REALES**\n\n"
            
            if location and location.lower() == "premium":
                response += f"⭐ **Contactos Premium:**\n"
                response += f"• Estado: ✅ Disponible\n"
                response += f"• Fuente: Top 10 LADAs por ICPTH\n"
                response += f"• Calidad: Números móviles verificados\n\n"
                response += f"🔍 **Para extraer:**\n"
                response += f"`/get [cantidad] premium [xlsx|txt]`"
                
            elif location:
                response += f"📍 **Contactos en {location.title()}:**\n"
                response += f"• Estado: Verificando disponibilidad...\n"
                response += f"• Ubicación: {location}\n"
                response += f"• Tipo: Números móviles reales\n\n"
                response += f"🔍 **Para extraer:**\n"
                response += f"`/get [cantidad] {location} [xlsx|txt]`"
                
            else:
                # General availability
                try:
                    states_count = len(self.db.get_available_states())
                    cities_count = len(self.db.get_available_cities())
                    premium_count = len(self.db.get_premium_states())
                except:
                    states_count = cities_count = premium_count = 0
                
                response += f"📈 **Disponibilidad General:**\n"
                response += f"• Estados con contactos: {states_count}\n"
                response += f"• Ciudades disponibles: {cities_count}\n"
                response += f"• Estados premium: {premium_count}\n"
                response += f"• Base total: 36M+ contactos verificados\n\n"
                response += f"💡 **Comandos útiles:**\n"
                response += f"• `/available premium` - Info contactos premium\n"
                response += f"• `/available [ubicación]` - Info ubicación específica\n"
                response += f"• `/states` - Ver todos los estados\n"
                response += f"• `/cities` - Ver todas las ciudades"
            
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            self.logger.error(f"Error in available command: {e}")
            await update.message.reply_text(
                "❌ **Error verificando disponibilidad**\n\n"
                "Error técnico registrado para revisión."
            )
    
    async def get_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Production GET command with real extraction"""
        # SECURITY: Check if message comes from authorized group
        if not self._is_authorized_group(update):
            return  # Silently ignore unauthorized messages
            
        user_id = update.effective_user.id
        
        # Check if user has active extraction
        if self.active_extractions.get(user_id, False):
            await update.message.reply_text(
                "⏳ **Tienes una extracción en progreso**\n"
                "Espera a que termine antes de iniciar otra."
            )
            return
        
        # Rate limiting
        if not self._check_rate_limit(user_id):
            await update.message.reply_text(
                "⏳ **Espera un momento**\n"
                "Rate limit: 1 comando cada 3 segundos en producción"
            )
            return
        
        # Parse command
        args = context.args
        if len(args) < 3:
            await update.message.reply_text(
                "❌ *Formato incorrecto para extracción REAL*\n\n"
                "*Uso:* `/get \\[cantidad\\] \\[premium\\|estado\\|ciudad\\] \\[xlsx\\|txt\\]`\n\n"
                "*Ejemplos con datos reales:*\n"
                "• `/get 1000 premium xlsx` \\- 1000 contactos de mejores LADAs\n"
                "• `/get 500 Sinaloa txt` \\- 500 contactos reales de Sinaloa\n"
                "• `/get 2000 Guadalajara xlsx` \\- 2000 contactos de Guadalajara\n\n"
                "⚠️ *Los contactos extraídos serán marcados como OPTED\\_OUT*",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
        
        # Process real extraction
        command = f"/get {' '.join(args)}"
        await self._process_production_extraction(update, command)
    
    async def _process_production_extraction(self, update: Update, command: str):
        """Process real production extraction"""
        user_id = update.effective_user.id
        
        try:
            # Mark user as having active extraction
            self.active_extractions[user_id] = True
            
            # Parse and validate command
            parsed = self.validator.parse_command(command)
            
            if not parsed.is_valid:
                error_msg = "❌ **ERRORES DE VALIDACIÓN:**\n"
                for error in parsed.errors:
                    error_msg += f"• {error}\n"
                await update.message.reply_text(error_msg, parse_mode=ParseMode.MARKDOWN)
                return
            
            # Check daily limits
            can_extract, limit_msg = self._check_daily_limits(user_id, parsed.amount)
            if not can_extract:
                await update.message.reply_text(f"🚫 **{limit_msg}**")
                return
            
            # Convert to extraction request
            request = parsed.to_extraction_request()
            if not request:
                await update.message.reply_text("❌ **Error interno:** No se pudo procesar la solicitud")
                return
            
            # Show processing message for real extraction
            processing_msg = await update.message.reply_text(
                f"⏳ **PROCESANDO EXTRACCIÓN REAL**\n\n"
                f"📊 **Parámetros:**\n"
                f"• Cantidad: {request.amount:,} contactos\n"
                f"• Tipo: {str(request.extraction_type).title()}\n"
                f"• Ubicación: {request.location or 'Premium LADAs'}\n"
                f"• Formato: {str(request.export_format).upper()}\n\n"
                f"🔍 **Consultando base de datos real...**\n"
                f"⏱️ **Esto puede tomar 10-30 segundos**\n\n"
                f"⚠️ **Los contactos serán marcados como OPTED_OUT**"
            )
            
            # Execute REAL extraction
            start_time = time.time()
            result = await self.contact_service.extract_contacts(request)
            
            if not result.is_successful():
                await processing_msg.edit_text(
                    f"❌ **ERROR EN EXTRACCIÓN REAL:**\n\n"
                    f"🔍 **Detalles:**\n{result.error_message}\n\n"
                    f"💡 **Sugerencias:**\n"
                    f"• Intenta con una cantidad menor\n"
                    f"• Verifica que la ubicación exista\n"
                    f"• Usa `/available` para ver disponibilidad"
                )
                return
            
            # Generate real file
            await processing_msg.edit_text(
                f"📊 **EXTRACCIÓN COMPLETADA - GENERANDO ARCHIVO**\n\n"
                f"✅ **Extraídos:** {result.total_extracted:,} contactos reales\n"
                f"⏱️ **Tiempo de consulta:** {result.query_time_seconds:.1f}s\n"
                f"🔄 **Marcados como OPTED_OUT:** {result.total_updated:,}\n\n"
                f"📁 **Generando archivo {str(request.export_format).upper()}...**"
            )
            
            # Export to file
            file_path = await self.export_service.export_contacts(result)
            
            # Upload real file to Telegram
            await self._upload_production_file(update, result, file_path, processing_msg)
            
            # Update user session
            session = self._get_user_session(user_id)
            session['extractions_today'] += 1
            session['contacts_extracted_today'] += result.total_extracted
            session['last_extraction'] = datetime.now()
            session['total_extractions'] += 1
            session['favorite_format'] = str(request.export_format)
            
            # Log production extraction
            self.logger.audit("PRODUCTION_EXTRACTION_SUCCESS", {
                "user_id": user_id,
                "extraction_type": str(request.extraction_type),
                "location": request.location,
                "amount_requested": request.amount,
                "amount_extracted": result.total_extracted,
                "query_time": result.query_time_seconds,
                "export_time": result.export_time_seconds,
                "file_size": result.file_size
            })
            
        except Exception as e:
            self.logger.error(f"Production extraction failed: {e}")
            await update.message.reply_text(
                f"❌ **ERROR CRÍTICO EN PRODUCCIÓN:**\n\n"
                f"🔍 **Error:** {str(e)}\n\n"
                f"🔧 **El error ha sido registrado para revisión técnica**"
            )
            
        finally:
            # Clear active extraction flag
            self.active_extractions[user_id] = False
    
    async def _upload_production_file(self, update: Update, result, file_path: str, processing_msg):
        """Upload production file to Telegram"""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                await processing_msg.edit_text("❌ **Error:** Archivo no generado correctamente")
                return
            
            file_size_mb = file_path_obj.stat().st_size / (1024 * 1024)
            
            # Check file size limit
            if file_size_mb > self.config.telegram_max_file_size_mb:
                await processing_msg.edit_text(
                    f"❌ **Archivo demasiado grande:** {file_size_mb:.1f} MB\n"
                    f"Límite Telegram: {self.config.telegram_max_file_size_mb} MB\n\n"
                    f"💡 **Solución:** Intenta con una cantidad menor de contactos"
                )
                return
            
            # Success message for production
            success_text = f"""
🎉 **EXTRACCIÓN REAL COMPLETADA**

📊 **Resultados de Producción:**
• **Extraídos:** {result.total_extracted:,} contactos REALES
• **Marcados OPTED_OUT:** {result.total_updated:,}
• **Formato:** {str(result.request.export_format).upper()}
• **Tamaño:** {file_size_mb:.1f} MB

⏱️ **Performance:**
• Consulta DB: {result.query_time_seconds:.1f}s
• Generación: {result.export_time_seconds:.1f}s
• Total: {result.total_time_seconds:.1f}s

🔒 **Garantía de Calidad:**
• ✅ Números verificados de 36M+ base
• ✅ Solo números móviles activos
• ✅ Contactos marcados para no reutilizar
• ✅ Auditoría completa registrada

📁 **Archivo listo para campañas SMS**
            """
            
            # Upload file
            with open(file_path_obj, 'rb') as file:
                await update.message.reply_document(
                    document=file,
                    filename=file_path_obj.name,
                    caption=success_text,
                    parse_mode=None  # Disable markdown parsing to avoid entity errors
                )
            
            # Delete processing message
            await processing_msg.delete()
            
            # Clean up file
            try:
                file_path_obj.unlink()
                self.logger.info(f"Cleaned up production file: {file_path_obj}")
            except Exception as cleanup_error:
                self.logger.warning(f"Failed to cleanup file: {cleanup_error}")
            
        except Exception as e:
            self.logger.error(f"Production file upload failed: {e}")
            await processing_msg.edit_text(
                f"❌ **Error subiendo archivo de producción:**\n{str(e)}"
            )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Production stats command"""
        # SECURITY: Check if message comes from authorized group
        if not self._is_authorized_group(update):
            return  # Silently ignore unauthorized messages
            
        user_id = update.effective_user.id
        session = self._get_user_session(user_id)
        
        # Get real database stats
        try:
            states_count = len(self.db.get_available_states())
            cities_count = len(self.db.get_available_cities())
            premium_count = len(self.db.get_premium_states())
        except:
            states_count = cities_count = premium_count = 0
        
        stats_text = f"""
📊 **ESTADÍSTICAS DE PRODUCCIÓN**

🤖 **Bot de Producción:**
• Nombre: {self.config.bot_name}
• Versión: {self.config.bot_version}
• Estado: ✅ Conectado a BD real
• Base de datos: PostgreSQL con 36M+ registros

👤 **Tu Actividad Hoy:**
• Extracciones: {session['extractions_today']}/20
• Contactos extraídos: {session['contacts_extracted_today']:,}/50,000
• Última extracción: {session['last_extraction'].strftime('%H:%M') if session['last_extraction'] else 'Nunca'}
• Formato favorito: {session['favorite_format'] or 'N/A'}
• Total histórico: {session['total_extractions']} extracciones

🗄️ **Base de Datos Real:**
• Estados con contactos: {states_count}
• Ciudades disponibles: {cities_count}
• Estados premium: {premium_count}
• Contactos totales: 36M+ verificados

⚡ **Límites de Producción:**
• Por extracción: 100 - 10,000 contactos
• Diario personal: 50,000 contactos
• Extracciones diarias: 20 máximo
• Rate limit: 3 segundos entre comandos

🔒 **Garantías:**
• ✅ Solo contactos VERIFIED
• ✅ Marcado automático OPTED_OUT
• ✅ Auditoría completa
• ✅ Sin duplicados

💡 **Tip**: Usa `/get [cantidad] [ubicación] [formato]` para extraer contactos
        """
        
        await update.message.reply_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages in production"""
        # SECURITY: Check if message comes from authorized group
        if not self._is_authorized_group(update):
            return  # Silently ignore unauthorized messages
            
        text = update.message.text.strip()
        
        if text.lower().startswith(('get ', '/get')):
            if not text.startswith('/'):
                text = '/' + text
            await self._process_production_extraction(update, text)
        else:
            await update.message.reply_text(
                "❓ **Comando no reconocido en producción**\n\n"
                "**Comandos disponibles:**\n"
                "• `/get [cantidad] [ubicación] [formato]` - Extracción real\n"
                "• `/help` - Ayuda completa\n"
                "• `/stats` - Estadísticas de producción\n\n"
                "**Ejemplo:** `/get 1000 premium xlsx`",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Production error handler"""
        # SECURITY: Check if message comes from authorized group (even for errors)
        if update and not self._is_authorized_group(update):
            return  # Silently ignore unauthorized messages
            
        self.logger.error(f"Production Telegram error: {context.error}")
        
        if update and update.message:
            await update.message.reply_text(
                "❌ **Error interno de producción**\n\n"
                "El error ha sido registrado para revisión técnica.\n"
                "Intenta nuevamente en unos momentos."
            )
    
    async def run(self):
        """Run the production bot"""
        self.logger.info("🚀 Starting Telegram PRODUCTION Bot...")
        self.logger.info(f"Bot: @{self.config.telegram_bot_username}")
        self.logger.info("🔗 Connected to real PostgreSQL database")
        self.logger.info("📊 Ready for real contact extractions")
        
        # Initialize the application properly
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(drop_pending_updates=True)
        
        # Keep running until stopped
        try:
            import asyncio
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            pass
        finally:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()


async def main():
    """Main entry point for production bot"""
    setup_logging()
    logger = get_logger()
    
    try:
        logger.info("🚀 Starting Telegram Contact Extractor Bot - PRODUCTION")
        
        bot = TelegramProductionBot()
        await bot.initialize()
        
        logger.info("✅ Production bot ready!")
        logger.info("🔗 Available at: https://t.me/RNumbeRs_bot")
        logger.info("🎯 Fase 2 - Producción con base de datos real")
        
        await bot.run()
        
    except KeyboardInterrupt:
        logger.info("👋 Production bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Production bot failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())