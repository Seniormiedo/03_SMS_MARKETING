import asyncio
import os

from utils.logger import setup_logging
from core.database import get_database_manager
from core.validators import get_validator


async def test_contact_extractor_bot():
    # Lazy import to avoid side effects if something fails earlier
    from main import ContactExtractorBot

    bot = ContactExtractorBot()
    try:
        await bot.initialize()
        print("BOT INIT: OK")

        # Run a few commands
        help_text = bot._handle_help_command()
        print("HELP (head):\n" + help_text[:200].replace("\n", " ") + "...")

        stats_text = await bot._handle_stats_command()
        print("STATS (head):\n" + stats_text[:200].replace("\n", " ") + "...")

        states_text = bot._handle_states_command()
        print("STATES (head):\n" + states_text[:200].replace("\n", " ") + "...")

    finally:
        try:
            await bot.shutdown()
        except Exception:
            pass


async def main():
    setup_logging()

    # Print DB env
    print(
        "DB ENV:",
        os.environ.get("BOT_DB_HOST"),
        os.environ.get("BOT_DB_PORT"),
        os.environ.get("BOT_DB_NAME"),
        os.environ.get("BOT_DB_USER"),
    )

    # Basic DB connectivity test
    db = get_database_manager()
    ok = db.test_connection()
    print(f"DB connection: {'OK' if ok else 'FAIL'}")

    # Minimal validator checks
    v = get_validator()
    print("Validator /get example:")
    parsed = v.parse_command("/get 1000 premium xlsx")
    print(parsed.model_dump())

    # Bot smoke test (initialize + key handlers)
    await test_contact_extractor_bot()


if __name__ == "__main__":
    asyncio.run(main())


