"""
Test configuration loading
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
print(f"Looking for .env at: {env_path}")
print(f".env exists: {env_path.exists()}")

if env_path.exists():
    load_dotenv(env_path)
    print("Loaded .env file")
else:
    print("No .env file found")

# Check environment variables
print(f"BOT_DB_PASSWORD: {os.getenv('BOT_DB_PASSWORD', 'NOT SET')}")
print(f"BOT_DB_HOST: {os.getenv('BOT_DB_HOST', 'NOT SET')}")
print(f"BOT_DB_NAME: {os.getenv('BOT_DB_NAME', 'NOT SET')}")

# Test Pydantic config
from pydantic_settings import BaseSettings

class TestConfig(BaseSettings):
    db_password: str
    db_host: str = "localhost"
    db_name: str = "sms_marketing"
    
    class Config:
        env_file = ".env"
        env_prefix = "BOT_"

try:
    config = TestConfig()
    print("✅ Configuration loaded successfully")
    print(f"DB Password: {config.db_password}")
except Exception as e:
    print(f"❌ Configuration failed: {e}")