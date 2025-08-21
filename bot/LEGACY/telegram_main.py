"""
Main entry point for Telegram Contact Extractor Bot
Production-ready Telegram bot implementation
"""

import asyncio
import sys
from pathlib import Path

# Add bot directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config
from utils.logger import setup_logging, get_logger
from core.telegram_bot import get_telegram_bot


async def main():
    """Main entry point for Telegram bot"""
    
    # Setup logging
    setup_logging()
    logger = get_logger()
    
    try:
        logger.info("🚀 Starting Telegram Contact Extractor Bot...")
        
        # Get configuration
        config = get_config()
        logger.info(f"Bot: @{config.telegram_bot_username}")
        logger.info(f"Version: {config.bot_version}")
        logger.info(f"Environment: {config.bot_environment}")
        
        # Initialize and run bot
        bot = get_telegram_bot()
        await bot.initialize()
        
        logger.info("✅ Bot initialized successfully")
        logger.info("🔗 Bot available at: https://t.me/RNumbeRs_bot")
        
        # Run the bot
        await bot.run()
        
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        try:
            bot = get_telegram_bot()
            await bot.shutdown()
        except:
            pass


if __name__ == "__main__":
    # Run the Telegram bot
    asyncio.run(main())