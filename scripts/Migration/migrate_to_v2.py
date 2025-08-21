#!/usr/bin/env python3
"""
Migration Script for SMS Marketing Platform v2.0

This script helps migrate from the legacy structure to the new professional
architecture with CamelCase and Clean Architecture principles.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages the migration process from legacy to v2.0 structure."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.legacy_path = project_root / "Legacy" / "OLD_2025-01-13"
        self.backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def run_migration(self) -> bool:
        """
        Run the complete migration process.

        Returns:
            True if migration successful, False otherwise
        """
        try:
            logger.info("🚀 Starting SMS Marketing Platform v2.0 Migration")

            # Step 1: Validate prerequisites
            if not self._validate_prerequisites():
                return False

            # Step 2: Create additional backup
            if not self._create_migration_backup():
                return False

            # Step 3: Migrate configuration files
            if not self._migrate_configuration():
                return False

            # Step 4: Migrate database scripts
            if not self._migrate_database_scripts():
                return False

            # Step 5: Create service templates
            if not self._create_service_templates():
                return False

            # Step 6: Update Docker configuration
            if not self._update_docker_configuration():
                return False

            # Step 7: Create development scripts
            if not self._create_development_scripts():
                return False

            # Step 8: Validate new structure
            if not self._validate_new_structure():
                return False

            logger.info("✅ Migration completed successfully!")
            logger.info("📋 Next steps:")
            logger.info("   1. Review and update .env file")
            logger.info("   2. Run: docker-compose -f docker-compose.new.yml build")
            logger.info("   3. Run: docker-compose -f docker-compose.new.yml up -d")
            logger.info("   4. Test all services are working correctly")

            return True

        except Exception as e:
            logger.error(f"❌ Migration failed: {str(e)}")
            return False

    def _validate_prerequisites(self) -> bool:
        """Validate that prerequisites are met for migration."""
        logger.info("🔍 Validating prerequisites...")

        # Check if legacy backup exists
        if not self.legacy_path.exists():
            logger.error("Legacy backup not found. Please run backup first.")
            return False

        # Check if new structure directories exist
        required_dirs = [
            "Core/Domain/Entities",
            "Core/Application/Services",
            "Core/Infrastructure/Database",
            "Services/ApiGateway",
            "WebDashboard/src"
        ]

        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                logger.error(f"Required directory missing: {dir_path}")
                return False

        # Check if Docker is available
        try:
            subprocess.run(["docker", "--version"], check=True, capture_output=True)
            subprocess.run(["docker-compose", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Docker or Docker Compose not available")
            return False

        logger.info("✅ Prerequisites validated")
        return True

    def _create_migration_backup(self) -> bool:
        """Create an additional backup before migration."""
        logger.info("💾 Creating migration backup...")

        backup_dir = self.project_root / "backups" / f"pre_migration_{self.backup_timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup critical files
        critical_files = [
            ".env",
            "docker-compose.yml",
            "requirements.txt",
            "BaseEstructura.md"
        ]

        for file_name in critical_files:
            source_file = self.project_root / file_name
            if source_file.exists():
                shutil.copy2(source_file, backup_dir / file_name)

        # Backup current Core and Services if they exist
        for dir_name in ["Core", "Services"]:
            source_dir = self.project_root / dir_name
            if source_dir.exists():
                shutil.copytree(source_dir, backup_dir / dir_name, dirs_exist_ok=True)

        logger.info(f"✅ Migration backup created at: {backup_dir}")
        return True

    def _migrate_configuration(self) -> bool:
        """Migrate configuration files to new format."""
        logger.info("⚙️ Migrating configuration files...")

        # Copy .env.example to .env if .env doesn't exist
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"

        if not env_file.exists() and env_example.exists():
            shutil.copy2(env_example, env_file)
            logger.info("📄 Created .env from .env.example")

        # Migrate legacy bot configuration if exists
        legacy_bot_env = self.legacy_path / "bot" / ".env"
        if legacy_bot_env.exists():
            self._merge_env_files(legacy_bot_env, env_file)

        return True

    def _migrate_database_scripts(self) -> bool:
        """Migrate database scripts to Infrastructure/Database."""
        logger.info("🗄️ Migrating database scripts...")

        db_dir = self.project_root / "Infrastructure" / "Database"
        db_dir.mkdir(parents=True, exist_ok=True)

        # Copy database configuration files from legacy
        legacy_docker_dir = self.legacy_path / "docker"
        if legacy_docker_dir.exists():
            for config_file in ["postgres.conf", "redis.conf"]:
                source_file = legacy_docker_dir / config_file
                if source_file.exists():
                    shutil.copy2(source_file, db_dir / config_file)

        # Create init.sql from legacy if exists
        legacy_init = legacy_docker_dir / "init-db.sql"
        if legacy_init.exists():
            shutil.copy2(legacy_init, db_dir / "init.sql")

        # Copy migration scripts
        legacy_scripts = self.legacy_path / "scripts"
        if legacy_scripts.exists():
            scripts_db_dir = self.project_root / "Scripts" / "Database"
            scripts_db_dir.mkdir(parents=True, exist_ok=True)

            for script_file in legacy_scripts.glob("*.sql"):
                shutil.copy2(script_file, scripts_db_dir / script_file.name)

        return True

    def _create_service_templates(self) -> bool:
        """Create template files for microservices."""
        logger.info("🏗️ Creating service templates...")

        services = [
            "ApiGateway",
            "ContactManagement",
            "LeadScoring",
            "ValidationOrchestrator"
        ]

        validators = [
            "WhatsAppValidator",
            "InstagramValidator",
            "FacebookValidator",
            "GoogleValidator",
            "AppleValidator"
        ]

        # Create main services
        for service in services:
            self._create_service_template(f"Services/{service}")

        # Create validator services
        for validator in validators:
            self._create_service_template(f"Services/PlatformValidators/{validator}")

        return True

    def _create_service_template(self, service_path: str) -> None:
        """Create a template structure for a microservice."""
        service_dir = self.project_root / service_path
        service_dir.mkdir(parents=True, exist_ok=True)

        # Create standard directories
        subdirs = ["src", "tests", "config"]
        for subdir in subdirs:
            (service_dir / subdir).mkdir(exist_ok=True)

        # Create Dockerfile template
        dockerfile_content = '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \\
    && chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["python", "-m", "src.main"]
'''

        dockerfile_path = service_dir / "Dockerfile"
        if not dockerfile_path.exists():
            dockerfile_path.write_text(dockerfile_content)

        # Create requirements.txt template
        requirements_content = '''fastapi>=0.110.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
httpx>=0.25.0
structlog>=23.2.0
prometheus-client>=0.19.0
'''

        requirements_path = service_dir / "requirements.txt"
        if not requirements_path.exists():
            requirements_path.write_text(requirements_content)

    def _update_docker_configuration(self) -> bool:
        """Update Docker configuration files."""
        logger.info("🐳 Updating Docker configuration...")

        # Copy Infrastructure/Docker files from legacy if they exist
        docker_dir = self.project_root / "Infrastructure" / "Docker"
        docker_dir.mkdir(parents=True, exist_ok=True)

        legacy_docker = self.legacy_path / "docker"
        if legacy_docker.exists():
            for config_file in ["nginx.conf"]:
                source_file = legacy_docker / config_file
                if source_file.exists():
                    shutil.copy2(source_file, docker_dir / config_file)

        # Rename new docker-compose.yml
        new_compose = self.project_root / "docker-compose.new.yml"
        if new_compose.exists():
            # Backup existing docker-compose.yml
            existing_compose = self.project_root / "docker-compose.yml"
            if existing_compose.exists():
                backup_compose = self.project_root / f"docker-compose.legacy.{self.backup_timestamp}.yml"
                shutil.move(existing_compose, backup_compose)

            # Move new compose file
            shutil.move(new_compose, existing_compose)
            logger.info("✅ Updated docker-compose.yml")

        return True

    def _create_development_scripts(self) -> bool:
        """Create development and deployment scripts."""
        logger.info("📝 Creating development scripts...")

        scripts_dir = self.project_root / "Scripts" / "Development"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        # Create development setup script
        setup_script = '''#!/bin/bash
# Development Setup Script for SMS Marketing Platform v2.0

set -e

echo "🚀 Setting up SMS Marketing Platform v2.0 for development..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed. Aborting." >&2; exit 1; }

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📄 Created .env from .env.example"
    echo "⚠️  Please update .env with your configuration before proceeding"
    exit 0
fi

# Build and start services
echo "🏗️ Building services..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
docker-compose ps

echo "✅ Development environment is ready!"
echo "📋 Available services:"
echo "   - API Gateway: http://localhost:8080"
echo "   - Web Dashboard: http://localhost:3000"
echo "   - Grafana: http://localhost:3001"
echo "   - Flower: http://localhost:5555"
echo "   - Prometheus: http://localhost:9090"
'''

        setup_script_path = scripts_dir / "setup_dev.sh"
        setup_script_path.write_text(setup_script)
        setup_script_path.chmod(0o755)

        # Create testing script
        test_script = '''#!/bin/bash
# Testing Script for SMS Marketing Platform v2.0

set -e

echo "🧪 Running tests for SMS Marketing Platform v2.0..."

# Run unit tests
echo "🔬 Running unit tests..."
python -m pytest Tests/Unit/ -v --cov=Core --cov=Services

# Run integration tests
echo "🔗 Running integration tests..."
python -m pytest Tests/Integration/ -v

# Run linting
echo "🔍 Running code quality checks..."
black --check Core/ Services/
ruff check Core/ Services/
mypy Core/ Services/

echo "✅ All tests passed!"
'''

        test_script_path = scripts_dir / "run_tests.sh"
        test_script_path.write_text(test_script)
        test_script_path.chmod(0o755)

        return True

    def _validate_new_structure(self) -> bool:
        """Validate that the new structure is correct."""
        logger.info("✅ Validating new structure...")

        # Check required files exist
        required_files = [
            "pyproject.toml",
            "README.md",
            ".env.example",
            "docker-compose.yml",
            "Core/Domain/Entities/Contact.py",
            "Core/Shared/Configuration/SystemConfig.py"
        ]

        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                logger.error(f"Required file missing: {file_path}")
                return False

        # Check directory structure
        required_dirs = [
            "Core/Domain/Entities",
            "Core/Application/Services",
            "Core/Infrastructure/Database",
            "Services/ApiGateway",
            "Services/PlatformValidators/WhatsAppValidator",
            "WebDashboard/src",
            "Infrastructure/Docker",
            "Tests/Unit",
            "Documentation/Architecture"
        ]

        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                logger.error(f"Required directory missing: {dir_path}")
                return False

        logger.info("✅ New structure validation passed")
        return True

    def _merge_env_files(self, source_env: Path, target_env: Path) -> None:
        """Merge environment variables from source to target."""
        if not source_env.exists():
            return

        # Read existing target env
        target_vars = {}
        if target_env.exists():
            with open(target_env, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        target_vars[key] = value

        # Read source env and merge
        with open(source_env, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key not in target_vars:  # Don't overwrite existing values
                        target_vars[key] = value

        # Write merged env
        with open(target_env, 'w') as f:
            for key, value in sorted(target_vars.items()):
                f.write(f"{key}={value}\n")


def main():
    """Main migration function."""
    project_root = Path.cwd()

    print("🚀 SMS Marketing Platform v2.0 Migration Tool")
    print("=" * 50)

    # Confirm migration
    response = input("This will migrate your project to v2.0 structure. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        return

    # Run migration
    migration_manager = MigrationManager(project_root)
    success = migration_manager.run_migration()

    if success:
        print("\n🎉 Migration completed successfully!")
        print("Please review the migration.log file for details.")
    else:
        print("\n❌ Migration failed!")
        print("Please check the migration.log file for errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
